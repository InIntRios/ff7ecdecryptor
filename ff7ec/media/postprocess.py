"""
Post-Processing Services for Decrypted & Extracted Media
Enables scanning previously extracted asset batches and converting videos or audio without rescanning source assets.
"""

import os
import sys
import time
import shutil
import threading
import subprocess
import logging
from typing import Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from ff7ec.constants import (
    SUBDIR_CONVERTED_VIDEOS,
    SUBDIR_CONVERTED_AUDIO,
    CRI_USM_KEY_UPPER,
    CRI_USM_KEY_LOWER,
    AUDIO_FORMAT_WAV,
    AUDIO_FORMAT_FLAC,
)
from ff7ec.crypto.detector import extract_crid_original_name_from_file
from ff7ec.tools.locator import ToolManager
from ff7ec.media.video import convert_usm_video
from ff7ec.media.audio import convert_criware_audio


def check_pause_and_stop(pause_event: threading.Event, stop_event: threading.Event) -> bool:
    """
    Helper to pause thread execution when pause_event is cleared.
    Returns True to continue, False if stop_event is signaled.
    """
    while not pause_event.is_set():
        if stop_event.is_set():
            return False
        time.sleep(0.1)
    return not stop_event.is_set()


class PostProcessor:
    """Provides operations to transcode and extract media from already dumped files."""

    @classmethod
    def convert_existing_videos_only(
        cls,
        output_dir: str,
        target_format: str,
        crid_mod_path: str,
        vgmstream_path: Optional[str],
        max_workers: int,
        logger: logging.Logger,
        stop_event: threading.Event,
        pause_event: threading.Event,
        progress_callback: Optional[Callable] = None,
    ) -> None:
        """
        Scans the destination folder directly for previously extracted .usm files.
        Extracts their embedded original filenames and outputs converted videos into <output_dir>/converted_videos/.
        """
        target_video_dir = os.path.join(output_dir, SUBDIR_CONVERTED_VIDEOS)
        os.makedirs(target_video_dir, exist_ok=True)

        logger.info("================================================================================")
        logger.info(f"STARTING POST-PROCESS VIDEO CONVERSION (Target Format: {target_format.upper()})")
        logger.info(f"Scanning Directory:       {output_dir}")
        logger.info(f"Separate Output Folder:   {target_video_dir}")
        logger.info(f"Parallel Worker Threads:  {max_workers}")
        logger.info("================================================================================")

        if not os.path.exists(output_dir):
            logger.error(f"Directory not found: {output_dir}")
            return

        usm_files = []
        for root, _, files in os.walk(output_dir):
            if os.path.basename(root) == SUBDIR_CONVERTED_VIDEOS:
                continue
            for f in files:
                if f.lower().endswith(".usm"):
                    usm_files.append(os.path.join(root, f))

        total = len(usm_files)
        logger.info(f"Found {total} USM video file(s) to convert.")
        if total == 0:
            return

        success = 0
        skipped = 0
        processed = 0
        ext = "." + target_format.lower().strip()

        def _process_one(usm_path: str):
            detected_name = extract_crid_original_name_from_file(usm_path)
            target_video = os.path.join(target_video_dir, f"{detected_name}{ext}")

            if os.path.exists(target_video) and os.path.getsize(target_video) > 0:
                return ("skip", detected_name, target_video, usm_path)

            if convert_usm_video(usm_path, target_video, target_format, crid_mod_path, vgmstream_path, logger):
                return ("success", detected_name, target_video, usm_path)
            return ("fail", detected_name, target_video, usm_path)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_process_one, u): u for u in usm_files}
            for future in as_completed(futures):
                if not check_pause_and_stop(pause_event, stop_event):
                    logger.warning("Operation paused or stopped by user.")
                    break

                processed += 1
                status, det_name, target_path, orig_path = future.result()
                if status == "success":
                    success += 1
                    logger.info(f"[{processed}/{total}] Converted Video: {os.path.basename(target_path)} (from {os.path.basename(orig_path)})")
                elif status == "skip":
                    skipped += 1
                else:
                    logger.warning(f"[{processed}/{total}] Failed: {os.path.basename(orig_path)}")

                if progress_callback:
                    progress_callback(processed, total, success, skipped)

        logger.info("================================================================================")
        logger.info(f"Video conversion complete: {success} converted, {skipped} skipped.")
        logger.info(f"All converted videos are saved in: {target_video_dir}")
        logger.info("================================================================================")

    @classmethod
    def convert_existing_audio_only(
        cls,
        output_dir: str,
        target_format: str,
        vgmstream_path: str,
        max_workers: int,
        logger: logging.Logger,
        stop_event: threading.Event,
        pause_event: threading.Event,
        progress_callback: Optional[Callable] = None,
    ) -> None:
        """
        Scans the destination folder for ACB, AWB, and WAV audio banks.
        Decodes and transcodes all audio tracks into <output_dir>/converted_audio/.
        """
        target_audio_dir = os.path.join(output_dir, SUBDIR_CONVERTED_AUDIO)
        os.makedirs(target_audio_dir, exist_ok=True)

        logger.info("================================================================================")
        logger.info(f"STARTING POST-PROCESS AUDIO CONVERSION (Target Format: {target_format.upper()})")
        logger.info(f"Scanning Directory:       {output_dir}")
        logger.info(f"Separate Output Folder:   {target_audio_dir}")
        logger.info(f"Parallel Worker Threads:  {max_workers}")
        logger.info("================================================================================")

        if not os.path.exists(output_dir):
            logger.error(f"Directory not found: {output_dir}")
            return

        audio_files = []
        for root, _, files in os.walk(output_dir):
            if os.path.basename(root) == SUBDIR_CONVERTED_AUDIO:
                continue
            for f in files:
                f_lower = f.lower()
                if f_lower.endswith((".acb", ".awb", ".wav", ".adx")):
                    audio_files.append(os.path.join(root, f))

        total = len(audio_files)
        logger.info(f"Found {total} audio container/bank file(s) to process (.acb, .awb, .wav).")
        if total == 0:
            return

        success_banks = 0
        total_tracks = 0
        processed = 0

        def _process_audio_bank(bank_path: str):
            count = convert_criware_audio(bank_path, target_audio_dir, target_format, vgmstream_path, logger)
            return count, bank_path

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_process_audio_bank, a): a for a in audio_files}
            for future in as_completed(futures):
                if not check_pause_and_stop(pause_event, stop_event):
                    logger.warning("Audio conversion paused or stopped by user.")
                    break

                processed += 1
                count, b_path = future.result()
                if count > 0:
                    success_banks += 1
                    total_tracks += count
                    logger.info(f"[{processed}/{total}] Extracted {count} track(s) from: {os.path.basename(b_path)}")
                else:
                    logger.info(f"[{processed}/{total}] Processed: {os.path.basename(b_path)}")

                if progress_callback:
                    progress_callback(processed, total, success_banks, 0)

        logger.info("================================================================================")
        logger.info(f"Audio conversion complete: {total_tracks} track(s) extracted across {success_banks} sound banks.")
        logger.info(f"All converted audio files are saved in: {target_audio_dir}")
        logger.info("================================================================================")

    @classmethod
    def extract_audio_from_usm(
        cls,
        usm_path: str,
        target_audio_dir: str,
        target_format: str,
        crid_mod_path: str,
        vgmstream_path: str,
        logger: logging.Logger,
    ) -> bool:
        """
        Extracts the audio track directly from a USM video, decodes via vgmstream-cli,
        and encodes to MP3, FLAC, or WAV into target_audio_dir.
        """
        if not crid_mod_path or not os.path.exists(crid_mod_path):
            return False

        os.makedirs(target_audio_dir, exist_ok=True)
        detected_name = extract_crid_original_name_from_file(usm_path)
        fmt = target_format.lower().strip()
        dest_path = os.path.join(target_audio_dir, f"{detected_name}.{fmt}")

        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
            return True

        temp_dir = os.path.join(
            target_audio_dir,
            f"_usmaudio_{threading.get_ident()}_{int(time.time() * 1000) % 100000}_{os.getpid()}",
        )
        os.makedirs(temp_dir, exist_ok=True)
        temp_usm = os.path.join(temp_dir, "input.usm")

        try:
            shutil.copy2(usm_path, temp_usm)
            cmd_crid = [
                crid_mod_path,
                "-b", CRI_USM_KEY_UPPER,
                "-a", CRI_USM_KEY_LOWER,
                "-x", "-i",
                temp_usm,
            ]
            startupinfo = ToolManager.get_hidden_process_startupinfo()
            subprocess.run(cmd_crid, capture_output=True, text=True, timeout=120, startupinfo=startupinfo, cwd=temp_dir)

            raw_audio_file = None
            for fname in os.listdir(temp_dir):
                fp = os.path.join(temp_dir, fname)
                if fname == "input.usm" or not os.path.isfile(fp) or os.path.getsize(fp) == 0:
                    continue
                fext = os.path.splitext(fname)[1].lower()
                if fext in (".adx", ".hca", ".wav", ".ogg"):
                    raw_audio_file = fp
                    break

            if not raw_audio_file:
                return False

            try:
                with open(raw_audio_file, "rb") as af:
                    hdr = af.read(16)
            except Exception:
                hdr = b""

            if hdr.startswith(b"\xc8\xc3\xc1") or hdr.startswith(b"HCA"):
                hca_target = os.path.join(temp_dir, "stream.hca")
                if raw_audio_file != hca_target:
                    try:
                        shutil.move(raw_audio_file, hca_target)
                        raw_audio_file = hca_target
                    except Exception:
                        pass

            out_wav = os.path.join(temp_dir, "stream.wav")
            if vgmstream_path and os.path.exists(vgmstream_path):
                cmd_vgm = [vgmstream_path, "-o", out_wav, raw_audio_file]
                subprocess.run(cmd_vgm, capture_output=True, text=True, timeout=120, startupinfo=startupinfo)
            elif raw_audio_file.lower().endswith(".wav"):
                out_wav = raw_audio_file

            if not os.path.exists(out_wav) or os.path.getsize(out_wav) == 0:
                return False

            if fmt == AUDIO_FORMAT_WAV:
                shutil.copy2(out_wav, dest_path)
            elif fmt == AUDIO_FORMAT_FLAC:
                cmd_ff = ["ffmpeg", "-y", "-i", out_wav, "-c:a", "flac", dest_path]
                subprocess.run(cmd_ff, capture_output=True, text=True, timeout=90, startupinfo=startupinfo)
            else:
                # Default MP3
                cmd_ff = ["ffmpeg", "-y", "-i", out_wav, "-c:a", "libmp3lame", "-q:a", "2", dest_path]
                subprocess.run(cmd_ff, capture_output=True, text=True, timeout=90, startupinfo=startupinfo)

            return os.path.exists(dest_path) and os.path.getsize(dest_path) > 0

        except Exception as e:
            logger.error(f"Error extracting audio from USM {usm_path}: {e}")
            return False
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @classmethod
    def extract_audio_from_videos_only(
        cls,
        output_dir: str,
        target_format: str,
        crid_mod_path: str,
        vgmstream_path: str,
        max_workers: int,
        logger: logging.Logger,
        stop_event: threading.Event,
        pause_event: threading.Event,
        progress_callback: Optional[Callable] = None,
    ) -> None:
        """Scans output directory for .usm video files and extracts their audio tracks into <output_dir>/converted_audio/."""
        target_audio_dir = os.path.join(output_dir, SUBDIR_CONVERTED_AUDIO)
        os.makedirs(target_audio_dir, exist_ok=True)

        logger.info("================================================================================")
        logger.info(f"STARTING USM AUDIO STREAM EXTRACTION (Target Format: {target_format.upper()})")
        logger.info(f"Scanning Directory:       {output_dir}")
        logger.info(f"Separate Output Folder:   {target_audio_dir}")
        logger.info(f"Parallel Worker Threads:  {max_workers}")
        logger.info("================================================================================")

        if not os.path.exists(output_dir):
            logger.error(f"Directory not found: {output_dir}")
            return

        usm_files = []
        for root, _, files in os.walk(output_dir):
            if os.path.basename(root) in (SUBDIR_CONVERTED_AUDIO, SUBDIR_CONVERTED_VIDEOS):
                continue
            for f in files:
                if f.lower().endswith(".usm"):
                    usm_files.append(os.path.join(root, f))

        total = len(usm_files)
        logger.info(f"Found {total} USM video file(s) to extract audio from.")
        if total == 0:
            return

        success = 0
        processed = 0

        def _worker(u_path: str):
            ok = cls.extract_audio_from_usm(u_path, target_audio_dir, target_format, crid_mod_path, vgmstream_path, logger)
            return ok, u_path

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_worker, u): u for u in usm_files}
            for future in as_completed(futures):
                if not check_pause_and_stop(pause_event, stop_event):
                    logger.warning("Operation paused or stopped by user.")
                    break

                processed += 1
                ok, u_path = future.result()
                if ok:
                    success += 1
                    logger.info(f"[{processed}/{total}] Extracted audio: {os.path.basename(u_path)}")
                else:
                    logger.warning(f"[{processed}/{total}] Failed: {os.path.basename(u_path)}")

                if progress_callback:
                    progress_callback(processed, total, success, 0)

        logger.info("================================================================================")
        logger.info(f"USM audio extraction complete: {success}/{total} tracks extracted.")
        logger.info(f"Saved into: {target_audio_dir}")
        logger.info("================================================================================")


# Functional aliases for backward compatibility
convert_existing_videos_only = PostProcessor.convert_existing_videos_only
convert_existing_audio_only = PostProcessor.convert_existing_audio_only
extract_audio_from_usm = PostProcessor.extract_audio_from_usm
extract_audio_from_videos_only = PostProcessor.extract_audio_from_videos_only
