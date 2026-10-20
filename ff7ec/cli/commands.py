"""
Command Line Interface (CLI) Dispatcher & Subcommands
Follows SOLID, Clean Code, and OOP patterns for command parsing and execution.
"""

import os
import sys
import threading
import argparse
import logging
from typing import Optional, List

from ff7ec.constants import (
    APP_NAME,
    DEFAULT_STEAM_INPUT_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_WORKER_THREADS,
    SUPPORTED_SCOPES,
    DEFAULT_SCOPE,
    SUPPORTED_VIDEO_FORMATS,
    DEFAULT_VIDEO_FORMAT,
    SUPPORTED_AUDIO_FORMATS,
    DEFAULT_AUDIO_FORMAT,
    SCOPE_VIDEO_ONLY,
    SCOPE_AUDIO_ONLY,
    SCOPE_BUNDLES_ONLY,
    TOOLS_DIR,
)
from ff7ec.config.manager import load_config, get_initial_mapping_path
from ff7ec.common.logger import setup_logger
from ff7ec.crypto.cipher import decrypt_asset_bundle
from ff7ec.tools.locator import ensure_tools
from ff7ec.mapping.database import (
    build_mapping_database,
    locate_or_fetch_mapping_database,
)
from ff7ec.scanner.engine_scanner import (
    scan_game_engine_and_keys,
    format_scan_report,
)
from ff7ec.engine.batch import run_batch_process
from ff7ec.media.postprocess import (
    convert_existing_videos_only,
    convert_existing_audio_only,
    extract_audio_from_videos_only,
)
from ff7ec.ui.gui import launch_gui


class CliApp:
    """Manages CLI argument parsing and dispatches commands to domain services."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or setup_logger()
        self.config = load_config()

    def build_parser(self) -> argparse.ArgumentParser:
        """Constructs and returns the argparse parser with all modes."""
        cfg = self.config
        parser = argparse.ArgumentParser(description=f"{APP_NAME} (Command-line Interface)")
        parser.add_argument("--gui", action="store_true", help="Launch interactive graphical user interface (GUI)")

        subparsers = parser.add_subparsers(dest="mode", help="Execution mode")

        # Mode: single
        p_single = subparsers.add_parser("single", help="Decrypt a single file using its logical asset mask")
        p_single.add_argument("input", help="Source encrypted file path")
        p_single.add_argument("output", help="Destination decrypted file path")
        p_single.add_argument("mask", help="Asset mask string (e.g., 'character/cloud/model.d')")

        # Mode: batch
        p_batch = subparsers.add_parser("batch", help="Batch decrypt and extract all assets in source directory")
        p_batch.add_argument("--source", "-s", default=cfg.get("source_dir", DEFAULT_STEAM_INPUT_DIR),
                             help=f"Source octo\\v1 folder (Default: {DEFAULT_STEAM_INPUT_DIR})")
        p_batch.add_argument("--output", "-o", default=cfg.get("output_dir", DEFAULT_OUTPUT_DIR),
                             help="Destination extraction directory")
        p_batch.add_argument("--mapping", "-m", default=cfg.get("mapping_path", ""),
                             help="Path to JSON mapping file (MD5 -> Asset name)")
        p_batch.add_argument("--crid", default=cfg.get("crid_mod_path", os.path.join(TOOLS_DIR, "crid_mod.exe")),
                             help="Path to crid_mod.exe")
        p_batch.add_argument("--vgmstream", default=cfg.get("vgmstream_path", os.path.join(TOOLS_DIR, "vgmstream-cli.exe")),
                             help="Path to vgmstream-cli.exe")
        p_batch.add_argument("--threads", "-t", type=int, default=cfg.get("worker_threads", DEFAULT_WORKER_THREADS),
                             help="Number of concurrent worker threads")
        p_batch.add_argument("--scope", choices=SUPPORTED_SCOPES, default=cfg.get("extract_scope", DEFAULT_SCOPE),
                             help=f"Asset extraction scope: {', '.join(SUPPORTED_SCOPES)} (Default: %(default)s)")
        p_batch.add_argument("--video-only", action="store_true", help="Extract only video cutscenes (shorthand for --scope video_only)")
        p_batch.add_argument("--audio-only", action="store_true", help="Extract only audio banks (shorthand for --scope audio_only)")
        p_batch.add_argument("--bundles-only", action="store_true", help="Extract only Unity asset bundles (shorthand for --scope bundles_only)")
        p_batch.add_argument("--video-format", choices=SUPPORTED_VIDEO_FORMATS, default=cfg.get("video_format", DEFAULT_VIDEO_FORMAT),
                             help="Target video format for USM containers (mp4 or webm)")
        p_batch.add_argument("--audio-format", choices=SUPPORTED_AUDIO_FORMATS, default=cfg.get("audio_format", DEFAULT_AUDIO_FORMAT),
                             help="Target audio format for audio banks (mp3, flac, or wav)")
        p_batch.add_argument("--no-video", action="store_true", help="Disable automatic video conversion")
        p_batch.add_argument("--no-audio", action="store_true", help="Disable automatic audio conversion")
        p_batch.add_argument("--no-resume", action="store_true", help="Disable skip-existing resume mode")

        # Mode: extract-videos
        p_ext_v = subparsers.add_parser("extract-videos", help="Extract and convert USM cutscene videos only from game source (skips bundles & audio)")
        p_ext_v.add_argument("--source", "-s", default=cfg.get("source_dir", DEFAULT_STEAM_INPUT_DIR),
                             help=f"Source octo\\v1 folder (Default: {DEFAULT_STEAM_INPUT_DIR})")
        p_ext_v.add_argument("--output", "-o", default=cfg.get("output_dir", DEFAULT_OUTPUT_DIR),
                             help="Destination extraction directory")
        p_ext_v.add_argument("--mapping", "-m", default=cfg.get("mapping_path", ""),
                             help="Path to JSON mapping file (MD5 -> Asset name)")
        p_ext_v.add_argument("--crid", default=cfg.get("crid_mod_path", os.path.join(TOOLS_DIR, "crid_mod.exe")),
                             help="Path to crid_mod.exe")
        p_ext_v.add_argument("--vgmstream", default=cfg.get("vgmstream_path", os.path.join(TOOLS_DIR, "vgmstream-cli.exe")),
                             help="Path to vgmstream-cli.exe")
        p_ext_v.add_argument("--format", choices=SUPPORTED_VIDEO_FORMATS, default=cfg.get("video_format", DEFAULT_VIDEO_FORMAT),
                             help="Target video format (mp4 or webm)")
        p_ext_v.add_argument("--threads", "-t", type=int, default=cfg.get("worker_threads", DEFAULT_WORKER_THREADS),
                             help="Number of concurrent worker threads")
        p_ext_v.add_argument("--no-convert", action="store_true", help="Do not transcode to MP4/WebM, keep decrypted raw .usm only")
        p_ext_v.add_argument("--no-resume", action="store_true", help="Disable skip-existing resume mode")

        # Mode: extract-audio
        p_ext_a = subparsers.add_parser("extract-audio", help="Extract and convert CRI ACB/AWB audio only from game source (skips bundles & videos)")
        p_ext_a.add_argument("--source", "-s", default=cfg.get("source_dir", DEFAULT_STEAM_INPUT_DIR),
                             help=f"Source octo\\v1 folder (Default: {DEFAULT_STEAM_INPUT_DIR})")
        p_ext_a.add_argument("--output", "-o", default=cfg.get("output_dir", DEFAULT_OUTPUT_DIR),
                             help="Destination extraction directory")
        p_ext_a.add_argument("--mapping", "-m", default=cfg.get("mapping_path", ""),
                             help="Path to JSON mapping file (MD5 -> Asset name)")
        p_ext_a.add_argument("--vgmstream", default=cfg.get("vgmstream_path", os.path.join(TOOLS_DIR, "vgmstream-cli.exe")),
                             help="Path to vgmstream-cli.exe")
        p_ext_a.add_argument("--format", choices=SUPPORTED_AUDIO_FORMATS, default=cfg.get("audio_format", DEFAULT_AUDIO_FORMAT),
                             help="Target audio format (mp3, flac, or wav)")
        p_ext_a.add_argument("--threads", "-t", type=int, default=cfg.get("worker_threads", DEFAULT_WORKER_THREADS),
                             help="Number of concurrent worker threads")
        p_ext_a.add_argument("--no-convert", action="store_true", help="Do not transcode tracks, keep raw .acb/.awb sound banks only")
        p_ext_a.add_argument("--no-resume", action="store_true", help="Disable skip-existing resume mode")

        # Mode: extract-usm-audio
        p_ext_ua = subparsers.add_parser("extract-usm-audio", help="Scan output folder and extract audio tracks directly from .usm cutscenes into converted_audio/")
        p_ext_ua.add_argument("--output", "-o", default=cfg.get("output_dir", DEFAULT_OUTPUT_DIR),
                              help="Root destination directory containing .usm cutscenes")
        p_ext_ua.add_argument("--format", choices=SUPPORTED_AUDIO_FORMATS, default=cfg.get("audio_format", DEFAULT_AUDIO_FORMAT),
                              help="Target audio format (mp3, flac, or wav)")
        p_ext_ua.add_argument("--crid", default=cfg.get("crid_mod_path", os.path.join(TOOLS_DIR, "crid_mod.exe")),
                              help="Path to crid_mod.exe")
        p_ext_ua.add_argument("--vgmstream", default=cfg.get("vgmstream_path", os.path.join(TOOLS_DIR, "vgmstream-cli.exe")),
                              help="Path to vgmstream-cli.exe")
        p_ext_ua.add_argument("--threads", "-t", type=int, default=cfg.get("worker_threads", DEFAULT_WORKER_THREADS),
                              help="Number of concurrent worker threads")

        # Mode: convert-videos
        p_post_v = subparsers.add_parser("convert-videos", help="Scan output folder and convert all .usm videos into converted_videos/")
        p_post_v.add_argument("--output", "-o", default=cfg.get("output_dir", DEFAULT_OUTPUT_DIR),
                              help="Root destination directory containing extracted .usm files")
        p_post_v.add_argument("--format", choices=SUPPORTED_VIDEO_FORMATS, default=cfg.get("video_format", DEFAULT_VIDEO_FORMAT),
                              help="Target video format (mp4 or webm)")
        p_post_v.add_argument("--crid", default=cfg.get("crid_mod_path", os.path.join(TOOLS_DIR, "crid_mod.exe")),
                              help="Path to crid_mod.exe")
        p_post_v.add_argument("--vgmstream", default=cfg.get("vgmstream_path", os.path.join(TOOLS_DIR, "vgmstream-cli.exe")),
                              help="Path to vgmstream-cli.exe")
        p_post_v.add_argument("--threads", "-t", type=int, default=cfg.get("worker_threads", DEFAULT_WORKER_THREADS),
                              help="Number of concurrent worker threads")

        # Mode: convert-audio
        p_post_a = subparsers.add_parser("convert-audio", help="Scan output folder and convert all .acb/.awb/.wav audio into converted_audio/")
        p_post_a.add_argument("--output", "-o", default=cfg.get("output_dir", DEFAULT_OUTPUT_DIR),
                              help="Root destination directory containing extracted audio files")
        p_post_a.add_argument("--format", choices=SUPPORTED_AUDIO_FORMATS, default=cfg.get("audio_format", DEFAULT_AUDIO_FORMAT),
                              help="Target audio format (mp3, flac, or wav)")
        p_post_a.add_argument("--vgmstream", default=cfg.get("vgmstream_path", os.path.join(TOOLS_DIR, "vgmstream-cli.exe")),
                              help="Path to vgmstream-cli.exe")
        p_post_a.add_argument("--threads", "-t", type=int, default=cfg.get("worker_threads", DEFAULT_WORKER_THREADS),
                              help="Number of concurrent worker threads")

        # Mode: build-mapping
        p_bmap = subparsers.add_parser("build-mapping", help="Fetch and generate octocacheevai.json asset database directly via game API")
        p_bmap.add_argument("--export", "-e", help="Optional destination directory or file path to copy octocacheevai.json")

        # Mode: get-mapping
        p_map = subparsers.add_parser("get-mapping", help="Locate, verify, or export octocacheevai.json asset database")
        p_map.add_argument("--export", "-e", help="Destination directory or file path to copy octocacheevai.json")
        p_map.add_argument("--build", "-b", action="store_true", help="Fetch and generate database via API if missing or to update")

        # Mode: scan-keys
        p_scan = subparsers.add_parser("scan-keys", help="Scan game installation, inspect GameAssembly.dll/IL2CPP engine, and display media decryption keys")
        p_scan.add_argument("--source", "-s", default=cfg.get("source_dir", DEFAULT_STEAM_INPUT_DIR),
                            help="Path to FF7EC game installation directory")

        # Mode: check-tools
        subparsers.add_parser("check-tools", help="Verify and automatically install required external dependencies")

        return parser

    def run(self, args: Optional[List[str]] = None) -> int:
        """Parses CLI arguments and dispatches command."""
        parser = self.build_parser()
        parsed = parser.parse_args(args)

        if parsed.gui or parsed.mode is None:
            launch_gui()
            return 0

        mode = parsed.mode
        logger = self.logger

        if mode == "single":
            with open(parsed.input, "rb") as f:
                enc = f.read()
            dec = decrypt_asset_bundle(enc, parsed.mask)
            os.makedirs(os.path.dirname(os.path.abspath(parsed.output)), exist_ok=True)
            with open(parsed.output, "wb") as f:
                f.write(dec)
            logger.info(f"Single file decryption complete: {parsed.output}")

        elif mode == "batch":
            scope = parsed.scope
            if parsed.video_only:
                scope = SCOPE_VIDEO_ONLY
            elif parsed.audio_only:
                scope = SCOPE_AUDIO_ONLY
            elif parsed.bundles_only:
                scope = SCOPE_BUNDLES_ONLY

            conv_v = (not parsed.no_video) if scope != SCOPE_AUDIO_ONLY else False
            conv_a = (not parsed.no_audio) if scope != SCOPE_VIDEO_ONLY else False

            if scope == SCOPE_BUNDLES_ONLY:
                map_check = parsed.mapping or get_initial_mapping_path()
                if not map_check or not os.path.isfile(map_check) or os.path.getsize(map_check) == 0:
                    logger.error("================================================================================")
                    logger.error("[ERROR] Cannot decrypt Asset Bundles without 'octocacheevai.json' database!")
                    logger.error("[ERROR] Please run 'python ff7ec_decryptor.py build-mapping' first to generate it.")
                    logger.error("================================================================================")
                    return 1

            stop_evt = threading.Event()
            pause_evt = threading.Event()
            pause_evt.set()
            run_batch_process(
                source_dir=parsed.source,
                output_dir=parsed.output,
                mapping_path=parsed.mapping,
                crid_mod_path=parsed.crid,
                vgmstream_path=parsed.vgmstream,
                convert_video=conv_v,
                convert_audio=conv_a,
                video_format=parsed.video_format,
                audio_format=parsed.audio_format,
                max_workers=parsed.threads,
                resume=not parsed.no_resume,
                extract_scope=scope,
                logger=logger,
                stop_event=stop_evt,
                pause_event=pause_evt,
            )

        elif mode == "extract-videos":
            stop_evt = threading.Event()
            pause_evt = threading.Event()
            pause_evt.set()
            run_batch_process(
                source_dir=parsed.source,
                output_dir=parsed.output,
                mapping_path=parsed.mapping,
                crid_mod_path=parsed.crid,
                vgmstream_path=parsed.vgmstream,
                convert_video=not parsed.no_convert,
                convert_audio=False,
                video_format=parsed.format,
                audio_format=self.config.get("audio_format", DEFAULT_AUDIO_FORMAT),
                max_workers=parsed.threads,
                resume=not parsed.no_resume,
                extract_scope=SCOPE_VIDEO_ONLY,
                logger=logger,
                stop_event=stop_evt,
                pause_event=pause_evt,
            )

        elif mode == "extract-audio":
            stop_evt = threading.Event()
            pause_evt = threading.Event()
            pause_evt.set()
            run_batch_process(
                source_dir=parsed.source,
                output_dir=parsed.output,
                mapping_path=parsed.mapping,
                crid_mod_path=self.config.get("crid_mod_path", os.path.join(TOOLS_DIR, "crid_mod.exe")),
                vgmstream_path=parsed.vgmstream,
                convert_video=False,
                convert_audio=not parsed.no_convert,
                video_format=self.config.get("video_format", DEFAULT_VIDEO_FORMAT),
                audio_format=parsed.format,
                max_workers=parsed.threads,
                resume=not parsed.no_resume,
                extract_scope=SCOPE_AUDIO_ONLY,
                logger=logger,
                stop_event=stop_evt,
                pause_event=pause_evt,
            )

        elif mode == "extract-usm-audio":
            stop_evt = threading.Event()
            pause_evt = threading.Event()
            pause_evt.set()
            extract_audio_from_videos_only(
                output_dir=parsed.output,
                target_format=parsed.format,
                crid_mod_path=parsed.crid,
                vgmstream_path=parsed.vgmstream,
                max_workers=parsed.threads,
                logger=logger,
                stop_event=stop_evt,
                pause_event=pause_evt,
            )

        elif mode == "convert-videos":
            stop_evt = threading.Event()
            pause_evt = threading.Event()
            pause_evt.set()
            convert_existing_videos_only(
                output_dir=parsed.output,
                target_format=parsed.format,
                crid_mod_path=parsed.crid,
                vgmstream_path=parsed.vgmstream,
                max_workers=parsed.threads,
                logger=logger,
                stop_event=stop_evt,
                pause_event=pause_evt,
            )

        elif mode == "convert-audio":
            stop_evt = threading.Event()
            pause_evt = threading.Event()
            pause_evt.set()
            convert_existing_audio_only(
                output_dir=parsed.output,
                target_format=parsed.format,
                vgmstream_path=parsed.vgmstream,
                max_workers=parsed.threads,
                logger=logger,
                stop_event=stop_evt,
                pause_event=pause_evt,
            )

        elif mode == "build-mapping":
            target_dir = parsed.export if parsed.export else None
            found, b_cnt, r_cnt = build_mapping_database(target_copy_dir=target_dir, logger=logger)
            if found:
                logger.info("=" * 80)
                logger.info(f"DATABASE BUILD COMPLETE: {found}")
                logger.info(f"- Asset Bundles: {b_cnt:,}")
                logger.info(f"- Game Resources: {r_cnt:,}")
                logger.info("=" * 80)
            else:
                logger.error("Failed to build octocacheevai.json database via API.")
                return 1

        elif mode == "scan-keys":
            rep = scan_game_engine_and_keys(parsed.source, logger=logger)
            print(format_scan_report(rep))

        elif mode == "get-mapping":
            target_dir = parsed.export if parsed.export else None
            if getattr(parsed, "build", False):
                found, b_cnt, r_cnt = build_mapping_database(target_copy_dir=target_dir, logger=logger)
            else:
                found, b_cnt, r_cnt = locate_or_fetch_mapping_database(
                    target_copy_dir=target_dir, auto_build_if_missing=False, logger=logger
                )
            if found:
                logger.info("=" * 80)
                logger.info(f"MAPPING DATABASE READY: {found}")
                logger.info(f"- Asset Bundles: {b_cnt:,}")
                logger.info(f"- Game Resources: {r_cnt:,}")
                logger.info("=" * 80)
            else:
                logger.error("octocacheevai.json was not found. Use 'build-mapping' to generate it via API.")
                return 1

        elif mode == "check-tools":
            ensure_tools(logger, auto_download=True)

        else:
            parser.print_help()

        return 0


def main():
    """Main CLI entrypoint."""
    if len(sys.argv) == 1:
        launch_gui()
        return
    app = CliApp()
    sys.exit(app.run())
