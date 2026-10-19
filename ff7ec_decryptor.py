"""
FF7EC Decryptor & Media Transcoder
Main Entry Point & Facade

This module serves as the primary entry point and backward-compatible facade for
the modular FF7EC decryptor package. It initializes Windows process environment
and delegates execution to the structured domain and application packages:
- ff7ec.constants: Application constants, scopes, and binary signatures.
- ff7ec.models: Domain Data Transfer Objects (DTOs) and models.
- ff7ec.common: Logging and Aspect-Oriented Programming (AOP) decorators.
- ff7ec.config: Configuration persistence and path resolution.
- ff7ec.crypto: XOR cipher, Applibot decryption, and binary format detectors.
- ff7ec.tools: External dependency discovery, downloads, and execution.
- ff7ec.media: Video demuxing, audio decoding, and post-processing.
- ff7ec.mapping: Protobuf manifest decoding and asset database management.
- ff7ec.scanner: IL2CPP metadata and cryptographic key auditing.
- ff7ec.engine: Concurrent multithreaded extraction pipeline.
- ff7ec.ui: Dynamic multi-theme Tkinter graphical user interface.
- ff7ec.cli: Command-line interface parser and dispatcher.
"""

import os
import sys

# Configure Windows Taskbar AppUserModelID and standard streams for PyInstaller windowed builds
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Shalzuth.FF7EC.AssetDecryptor.2.1")
        if ctypes.windll.kernel32.AttachConsole(-1):
            sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace")
            sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace")
    except Exception:
        pass

if sys.stdout is None:
    try:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    except Exception:
        pass
if sys.stderr is None:
    try:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")
    except Exception:
        pass

# Re-export all public domain models, constants, and services for 100% backward compatibility
from ff7ec.constants import (
    APP_NAME,
    APP_VERSION,
    APP_AUTHOR,
    APP_DESCRIPTION,
    BASE_DIR,
    TOOLS_DIR,
    CONFIG_FILE,
    LOG_FILE,
    DEFAULT_INITIAL_MASK,
    DEFAULT_FIRST_BYTE,
    CRI_USM_KEY_UPPER,
    CRI_USM_KEY_LOWER,
    DEFAULT_STEAM_INPUT_DIR,
    FALLBACK_STEAM_INPUT_DIR,
    DEFAULT_OUTPUT_DIR,
    FALLBACK_OUTPUT_DIR,
    DEFAULT_WORKER_THREADS,
    MIN_WORKER_THREADS,
    MAX_WORKER_THREADS,
    DEFAULT_SCOPE,
    SUPPORTED_SCOPES,
    DEFAULT_VIDEO_FORMAT,
    DEFAULT_AUDIO_FORMAT,
    SUPPORTED_VIDEO_FORMATS,
    SUPPORTED_AUDIO_FORMATS,
    VIDEO_FORMAT_MP4,
    VIDEO_FORMAT_WEBM,
    AUDIO_FORMAT_MP3,
    AUDIO_FORMAT_FLAC,
    AUDIO_FORMAT_WAV,
    SCOPE_ALL,
    SCOPE_BUNDLES_ONLY,
    SCOPE_VIDEO_ONLY,
    SCOPE_AUDIO_ONLY,
    SCOPE_LABELS,
    SCOPE_VAL_TO_DISPLAY,
    SCOPE_DISPLAY_TO_VAL,
    SUBDIR_BUNDLES,
    SUBDIR_AUDIO_CRIWARE,
    SUBDIR_VIDEOS_RAW,
    SUBDIR_OTHER_RAW,
    SUBDIR_CONVERTED_VIDEOS,
    SUBDIR_CONVERTED_AUDIO,
    MAGIC_UNITYFS,
    MAGIC_CRI_ACB,
    MAGIC_CRI_AWB,
    MAGIC_CRI_USM,
    MAGIC_OGG,
    MAGIC_RIFF,
    MAGIC_FTYP,
    VGMSTREAM_RELEASE_URL,
    FFMPEG_RELEASE_URL,
)
from ff7ec.models import (
    FileInfo,
    ScanReport,
    ExtractionJob,
    ProgressUpdate,
)
from ff7ec.common.aop import (
    timed_action,
    safe_run,
    thread_synchronized,
)
from ff7ec.common.logger import (
    UILogHandler,
    setup_logger,
)
from ff7ec.config.manager import (
    load_config,
    save_config,
    get_initial_mapping_path,
    resolve_game_asset_dir,
    get_app_icon_path,
)
from ff7ec.crypto.cipher import (
    ApplibotCipher,
    string_to_mask_bytes,
    decrypt_asset_bundle,
)
from ff7ec.crypto.detector import (
    FileDetector,
    detect_file_info,
    extract_crid_original_name,
    extract_crid_original_name_from_file,
)
from ff7ec.tools.locator import (
    ToolManager,
    ensure_tools,
)
from ff7ec.media.video import (
    UsmVideoTranscoder,
    convert_usm_video,
)
from ff7ec.media.audio import (
    CriwareAudioTranscoder,
    convert_criware_audio,
)
from ff7ec.media.postprocess import (
    PostProcessor,
    check_pause_and_stop,
    convert_existing_videos_only,
    convert_existing_audio_only,
    extract_audio_from_usm,
    extract_audio_from_videos_only,
)
from ff7ec.mapping.protobuf import (
    ProtobufDecoder,
    _decode_octo_data_message,
    _decode_octo_database,
)
from ff7ec.mapping.server import (
    NeverCrisisServerManager,
    is_nevercrisis_server_running,
    find_nevercrisis_server,
    start_nevercrisis_server,
)
from ff7ec.mapping.database import (
    MappingDatabaseService,
    dump_octo_database_native,
    build_mapping_database,
    locate_or_fetch_mapping_database,
    load_mapping_file,
    OCTO_REVISIONS,
    OCTO_RESOURCES_URL,
    OCTO_HEADERS,
)
from ff7ec.scanner.engine_scanner import (
    GameScannerService,
    scan_game_engine_and_keys,
    format_scan_report,
)
from ff7ec.engine.batch import (
    BatchExtractionEngine,
    run_batch_process,
)
from ff7ec.ui.themes import THEMES, ThemeManager
from ff7ec.ui.gui import launch_gui
from ff7ec.cli.commands import CliApp, main

__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "APP_AUTHOR",
    "APP_DESCRIPTION",
    "BASE_DIR",
    "TOOLS_DIR",
    "CONFIG_FILE",
    "LOG_FILE",
    "DEFAULT_INITIAL_MASK",
    "DEFAULT_FIRST_BYTE",
    "CRI_USM_KEY_UPPER",
    "CRI_USM_KEY_LOWER",
    "DEFAULT_STEAM_INPUT_DIR",
    "FALLBACK_STEAM_INPUT_DIR",
    "DEFAULT_OUTPUT_DIR",
    "FALLBACK_OUTPUT_DIR",
    "DEFAULT_WORKER_THREADS",
    "MIN_WORKER_THREADS",
    "MAX_WORKER_THREADS",
    "DEFAULT_SCOPE",
    "SUPPORTED_SCOPES",
    "DEFAULT_VIDEO_FORMAT",
    "DEFAULT_AUDIO_FORMAT",
    "SUPPORTED_VIDEO_FORMATS",
    "SUPPORTED_AUDIO_FORMATS",
    "VIDEO_FORMAT_MP4",
    "VIDEO_FORMAT_WEBM",
    "AUDIO_FORMAT_MP3",
    "AUDIO_FORMAT_FLAC",
    "AUDIO_FORMAT_WAV",
    "SCOPE_ALL",
    "SCOPE_BUNDLES_ONLY",
    "SCOPE_VIDEO_ONLY",
    "SCOPE_AUDIO_ONLY",
    "SCOPE_LABELS",
    "SCOPE_VAL_TO_DISPLAY",
    "SCOPE_DISPLAY_TO_VAL",
    "SUBDIR_BUNDLES",
    "SUBDIR_AUDIO_CRIWARE",
    "SUBDIR_VIDEOS_RAW",
    "SUBDIR_OTHER_RAW",
    "SUBDIR_CONVERTED_VIDEOS",
    "SUBDIR_CONVERTED_AUDIO",
    "MAGIC_UNITYFS",
    "MAGIC_CRI_ACB",
    "MAGIC_CRI_AWB",
    "MAGIC_CRI_USM",
    "MAGIC_OGG",
    "MAGIC_RIFF",
    "MAGIC_FTYP",
    "VGMSTREAM_RELEASE_URL",
    "FFMPEG_RELEASE_URL",
    "FileInfo",
    "ScanReport",
    "ExtractionJob",
    "ProgressUpdate",
    "timed_action",
    "safe_run",
    "thread_synchronized",
    "UILogHandler",
    "setup_logger",
    "load_config",
    "save_config",
    "get_initial_mapping_path",
    "resolve_game_asset_dir",
    "get_app_icon_path",
    "ApplibotCipher",
    "string_to_mask_bytes",
    "decrypt_asset_bundle",
    "FileDetector",
    "detect_file_info",
    "extract_crid_original_name",
    "extract_crid_original_name_from_file",
    "ToolManager",
    "ensure_tools",
    "UsmVideoTranscoder",
    "convert_usm_video",
    "CriwareAudioTranscoder",
    "convert_criware_audio",
    "PostProcessor",
    "check_pause_and_stop",
    "convert_existing_videos_only",
    "convert_existing_audio_only",
    "extract_audio_from_usm",
    "extract_audio_from_videos_only",
    "ProtobufDecoder",
    "_decode_octo_data_message",
    "_decode_octo_database",
    "NeverCrisisServerManager",
    "is_nevercrisis_server_running",
    "find_nevercrisis_server",
    "start_nevercrisis_server",
    "MappingDatabaseService",
    "dump_octo_database_native",
    "build_mapping_database",
    "locate_or_fetch_mapping_database",
    "load_mapping_file",
    "OCTO_REVISIONS",
    "OCTO_RESOURCES_URL",
    "OCTO_HEADERS",
    "GameScannerService",
    "scan_game_engine_and_keys",
    "format_scan_report",
    "BatchExtractionEngine",
    "run_batch_process",
    "THEMES",
    "ThemeManager",
    "launch_gui",
    "CliApp",
    "main",
]

if __name__ == "__main__":
    main()
