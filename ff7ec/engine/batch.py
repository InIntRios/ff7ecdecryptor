"""
Parallel Batch Extraction Engine
Executes multi-threaded decryption, asset classification, and media transcoding pipelines.
"""

import os
import time
import threading
import logging
from typing import Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from ff7ec.constants import (
    DEFAULT_SCOPE,
    SCOPE_VIDEO_ONLY,
    SCOPE_AUDIO_ONLY,
    SCOPE_BUNDLES_ONLY,
    SCOPE_LABELS,
    SUBDIR_BUNDLES,
    SUBDIR_AUDIO_CRIWARE,
    SUBDIR_VIDEOS_RAW,
    SUBDIR_OTHER_RAW,
    SUBDIR_CONVERTED_VIDEOS,
    SUBDIR_CONVERTED_AUDIO,
    MAGIC_CRI_USM,
    MAGIC_CRI_ACB,
    MAGIC_CRI_AWB,
    MAGIC_RIFF,
    MAGIC_OGG,
)
from ff7ec.common.logger import setup_logger
from ff7ec.config.manager import resolve_game_asset_dir
from ff7ec.crypto.cipher import decrypt_asset_bundle
from ff7ec.crypto.detector import detect_file_info, extract_crid_original_name
from ff7ec.media.video import convert_usm_video
from ff7ec.media.audio import convert_criware_audio
from ff7ec.media.postprocess import check_pause_and_stop
from ff7ec.mapping.database import load_mapping_file


class BatchExtractionEngine:
    """Orchestrates parallel multithreaded extraction, decryption, and media conversions."""

    @classmethod
    def run(
        cls,
        source_dir: str,
        output_dir: str,
        mapping_path: str,
        crid_mod_path: str,
        vgmstream_path: str,
        convert_video: bool,
        convert_audio: bool,
        video_format: str,
        audio_format: str,
        max_workers: int,
        resume: bool,
        extract_scope: str = DEFAULT_SCOPE,
        logger: Optional[logging.Logger] = None,
        stop_event: Optional[threading.Event] = None,
        pause_event: Optional[threading.Event] = None,
        progress_callback: Optional[Callable] = None,
    ) -> None:
        """
        High-performance parallel extraction workflow (100% read-only on source).
        Converts media directly into dedicated converted_videos/ and converted_audio/ folders.
        Supports extract_scope: 'all', 'video_only', 'audio_only', 'bundles_only'.
        """
        if logger is None:
            logger = setup_logger()
        if stop_event is None:
            stop_event = threading.Event()
        if pause_event is None:
            pause_event = threading.Event()
            pause_event.set()

        target_vid_dir = os.path.join(output_dir, SUBDIR_CONVERTED_VIDEOS)
        target_aud_dir = os.path.join(output_dir, SUBDIR_CONVERTED_AUDIO)

        if convert_video:
            os.makedirs(target_vid_dir, exist_ok=True)
        if convert_audio:
            os.makedirs(target_aud_dir, exist_ok=True)

        scope_name = SCOPE_LABELS.get(extract_scope, extract_scope)

        logger.info("================================================================================")
        logger.info("STARTING BATCH EXTRACTION PROCESS")
        logger.info(f"Extraction Scope:              {scope_name.upper()}")
        logger.info(f"Source Directory (Read-Only):  {source_dir}")
        logger.info(f"Raw Output Directory:          {output_dir}")
        logger.info(f"Converted Videos Folder:       {target_vid_dir}")
        logger.info(f"Converted Audio Folder:        {target_aud_dir}")
        logger.info(f"Parallel Worker Threads:       {max_workers}")
        logger.info(f"Convert Video:                 {'ENABLED (' + video_format.upper() + ')' if convert_video else 'DISABLED'}")
        logger.info(f"Convert Audio:                 {'ENABLED (' + audio_format.upper() + ')' if convert_audio else 'DISABLED'}")
        logger.info(f"Skip Existing (Resume):        {'ENABLED' if resume else 'DISABLED'}")

        actual_source = resolve_game_asset_dir(source_dir)
        if os.path.abspath(actual_source).lower() != os.path.abspath(source_dir).lower():
            logger.info(f"Resolved Game Asset Directory: {actual_source}")
        source_dir = actual_source

        if not os.path.exists(source_dir):
            logger.error(f"Source directory does not exist: {source_dir}")
            return

        mapping = load_mapping_file(mapping_path, logger) if mapping_path else {}

        logger.info(f"Step 1: Scanning source directory for asset files [Scope: {scope_name}]...")
        file_list = []
        total_size = 0

        for root, _, files in os.walk(source_dir):
            if stop_event.is_set():
                logger.warning("Scan canceled by user.")
                return

            for fname in files:
                if fname.endswith(".meta"):
                    continue
                fpath = os.path.join(root, fname)

                # Fast scope filtering
                if extract_scope == SCOPE_VIDEO_ONLY:
                    mask = mapping.get(fname.lower())
                    if mask:
                        if not mask.lower().endswith(".usm"):
                            continue
                    else:
                        try:
                            with open(fpath, "rb") as f_chk:
                                if f_chk.read(4) != MAGIC_CRI_USM:
                                    continue
                        except Exception:
                            continue
                elif extract_scope == SCOPE_AUDIO_ONLY:
                    mask = mapping.get(fname.lower())
                    if mask:
                        if not mask.lower().endswith((".acb", ".awb", ".acf", ".wav", ".ogg")):
                            continue
                    else:
                        try:
                            with open(fpath, "rb") as f_chk:
                                if f_chk.read(4) not in (MAGIC_CRI_ACB, MAGIC_CRI_AWB, MAGIC_RIFF, MAGIC_OGG):
                                    continue
                        except Exception:
                            continue
                elif extract_scope == SCOPE_BUNDLES_ONLY:
                    mask = mapping.get(fname.lower())
                    if mask:
                        if mask.lower().endswith((".usm", ".acb", ".awb", ".acf")):
                            continue
                    else:
                        try:
                            with open(fpath, "rb") as f_chk:
                                hdr = f_chk.read(4)
                                if hdr in (MAGIC_CRI_USM, MAGIC_CRI_ACB, MAGIC_CRI_AWB):
                                    continue
                        except Exception:
                            continue

                try:
                    sz = os.path.getsize(fpath)
                    if sz > 0:
                        file_list.append((fpath, fname, sz))
                        total_size += sz
                except Exception:
                    pass

        total_files = len(file_list)
        logger.info(f"Found {total_files:,} asset files ({total_size / (1024 ** 3):.2f} GB total)")

        if total_files == 0:
            logger.warning("No files found to process.")
            return

        logger.info("Step 2: Starting multithreaded decryption and extraction...")
        success_count = 0
        skipped_count = 0
        video_count = 0
        audio_count = 0
        error_count = 0
        processed_count = 0

        lock = threading.Lock()
        start_time = time.time()

        def _worker_task(item):
            nonlocal success_count, skipped_count, video_count, audio_count, error_count, processed_count
            fpath, fname, sz = item

            if not check_pause_and_stop(pause_event, stop_event):
                return

            md5_key = fname.lower()
            mask = mapping.get(md5_key)

            try:
                with open(fpath, "rb") as f:
                    data = f.read()

                out_data = data
                is_crid_video = False
                is_cri_audio = False
                detected_video_name = fname

                if mask:
                    mask_clean = mask.replace("/", os.sep).replace("\\", os.sep)
                    if mask.lower().endswith(".usm"):
                        out_data = data
                        is_crid_video = True
                        detected_video_name = os.path.splitext(os.path.basename(mask))[0]
                        rel_out = os.path.join(SUBDIR_VIDEOS_RAW, mask_clean)
                    elif mask.lower().endswith((".acb", ".awb", ".acf")):
                        out_data = data
                        is_cri_audio = mask.lower().endswith((".acb", ".awb"))
                        rel_out = os.path.join(SUBDIR_AUDIO_CRIWARE, mask_clean)
                    else:
                        out_data = decrypt_asset_bundle(data, mask)
                        if not mask_clean.endswith((".a", ".d", ".bundle", ".unity3d")):
                            mask_clean += ".bundle"
                        rel_out = os.path.join(SUBDIR_BUNDLES, mask_clean)
                else:
                    cat_folder, ext = detect_file_info(data)
                    save_name = fname
                    if ext == ".usm":
                        is_crid_video = True
                        detected_video_name = extract_crid_original_name(data, fname)
                        save_name = detected_video_name
                    elif ext in (".acb", ".awb"):
                        is_cri_audio = True

                    rel_out = os.path.join(cat_folder, save_name + ext)

                out_path = os.path.join(output_dir, rel_out)

                # Check resume / skip for raw output
                if resume and os.path.exists(out_path) and os.path.getsize(out_path) == len(out_data):
                    with lock:
                        skipped_count += 1
                        processed_count += 1
                    return

                os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
                with open(out_path, "wb") as f:
                    f.write(out_data)

                # Video conversion into separate converted_videos folder
                if is_crid_video and convert_video:
                    vid_ext = "." + video_format.lower().strip()
                    target_vid = os.path.join(target_vid_dir, f"{detected_video_name}{vid_ext}")
                    if not (resume and os.path.exists(target_vid) and os.path.getsize(target_vid) > 0):
                        if convert_usm_video(out_path, target_vid, video_format, crid_mod_path, vgmstream_path, logger):
                            with lock:
                                video_count += 1

                # Audio conversion into separate converted_audio folder
                if is_cri_audio and convert_audio:
                    num_tracks = convert_criware_audio(out_path, target_aud_dir, audio_format, vgmstream_path, logger)
                    if num_tracks > 0:
                        with lock:
                            audio_count += num_tracks

                with lock:
                    success_count += 1
                    processed_count += 1

            except Exception as ex:
                with lock:
                    error_count += 1
                    processed_count += 1
                logger.error(f"Error processing {fpath}: {ex}")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_worker_task, item) for item in file_list]

            last_report_time = time.time()
            for idx, future in enumerate(as_completed(futures), 1):
                if not check_pause_and_stop(pause_event, stop_event):
                    logger.warning("Batch processing paused or stopped.")
                    for f in futures:
                        f.cancel()
                    break

                current_time = time.time()
                if (current_time - last_report_time >= 0.5) or (idx == total_files):
                    last_report_time = current_time
                    with lock:
                        p = processed_count
                        s = success_count
                        sk = skipped_count
                    if progress_callback:
                        progress_callback(p, total_files, s, sk)
                    elapsed = max(1.0, current_time - start_time)
                    speed = p / elapsed
                    remaining = max(0, total_files - p)
                    eta_sec = remaining / max(0.1, speed)
                    eta_str = time.strftime("%Hh %Mm %Ss", time.gmtime(eta_sec))
                    logger.info(
                        f"Progress: [{p:,}/{total_files:,}] ({p / total_files * 100:.1f}%) | "
                        f"Success: {s:,} | Skipped: {sk:,} | Speed: {speed:.1f} files/s | ETA: {eta_str}"
                    )

        total_time = time.time() - start_time
        logger.info("================================================================================")
        logger.info(f"BATCH EXTRACTION COMPLETE in {total_time / 60:.2f} minutes!")
        logger.info(f"- Successfully processed: {success_count:,} file(s)")
        logger.info(f"- Skipped (Resume):        {skipped_count:,} file(s)")
        if convert_video:
            logger.info(f"- Videos Converted:        {video_count:,} video(s) -> {target_vid_dir}")
        if convert_audio:
            logger.info(f"- Audio Tracks Converted:  {audio_count:,} audio file(s) -> {target_aud_dir}")
        logger.info(f"- Source directory untouched (100% read-only).")
        logger.info("================================================================================")


# Functional alias for backward compatibility
run_batch_process = BatchExtractionEngine.run
