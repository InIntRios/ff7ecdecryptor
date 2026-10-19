"""
FF7EC Decryptor & Media Transcoder Package
Modular, clean, maintainable architecture following SOLID, KISS, DDD, and OOP principles.
"""

from ff7ec.constants import (
    APP_NAME,
    APP_VERSION,
    APP_AUTHOR,
    APP_DESCRIPTION,
)
from ff7ec.models import (
    FileInfo,
    ScanReport,
    ExtractionJob,
    ProgressUpdate,
)
from ff7ec.crypto.cipher import (
    ApplibotCipher,
    decrypt_asset_bundle,
    string_to_mask_bytes,
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
    convert_existing_videos_only,
    convert_existing_audio_only,
    extract_audio_from_videos_only,
)
from ff7ec.mapping.database import (
    MappingDatabaseService,
    dump_octo_database_native,
    build_mapping_database,
    locate_or_fetch_mapping_database,
    load_mapping_file,
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
from ff7ec.ui.gui import launch_gui
from ff7ec.cli.commands import CliApp, main

__version__ = APP_VERSION
__author__ = APP_AUTHOR

__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "APP_AUTHOR",
    "APP_DESCRIPTION",
    "FileInfo",
    "ScanReport",
    "ExtractionJob",
    "ProgressUpdate",
    "ApplibotCipher",
    "decrypt_asset_bundle",
    "string_to_mask_bytes",
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
    "convert_existing_videos_only",
    "convert_existing_audio_only",
    "extract_audio_from_videos_only",
    "MappingDatabaseService",
    "dump_octo_database_native",
    "build_mapping_database",
    "locate_or_fetch_mapping_database",
    "load_mapping_file",
    "GameScannerService",
    "scan_game_engine_and_keys",
    "format_scan_report",
    "BatchExtractionEngine",
    "run_batch_process",
    "launch_gui",
    "CliApp",
    "main",
]
