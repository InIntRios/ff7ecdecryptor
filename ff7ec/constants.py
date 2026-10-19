"""
Final Fantasy VII: Ever Crisis (FF7EC)
Central Constants and System Definitions
"""

import os
import sys

# Application Metadata
APP_NAME = "FF7EC Asset Decryptor & Media Converter"
APP_VERSION = "2.1.0"
APP_AUTHOR = "InIntRios"
APP_DESCRIPTION = "High-performance asset decryptor and media converter for FF7: Ever Crisis"

# Application Filesystem Locations (Supports frozen PyInstaller executable)
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    # Anchor to root project directory where entry point resides
    _current_file_dir = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(_current_file_dir)

CONFIG_FILE = os.path.join(BASE_DIR, "ff7ec_config.json")
LOG_FILE = os.path.join(BASE_DIR, "ff7ec_extract.log")
TOOLS_DIR = os.path.join(BASE_DIR, "tools")

# Game Asset Cryptography Constants (Applibot XOR Cipher)
DEFAULT_INITIAL_MASK = 0xAB
DEFAULT_FIRST_BYTE = 0x55  # 'U' for standard UnityFS bundle

# CRI Middleware USM Decryption Keys (64-bit split key)
CRI_USM_KEY_UPPER = "000011DA"
CRI_USM_KEY_LOWER = "4DE45ADE"

# Default Steam Game Directories
DEFAULT_STEAM_INPUT_DIR = r"C:\Program Files (x86)\Steam\steamapps\common\FF7EC"
FALLBACK_STEAM_INPUT_DIR = r"D:\SteamLibrary\steamapps\common\FF7EC"

DEFAULT_OUTPUT_DIR = r"C:\FF7EC_Decrypted_Assets"
FALLBACK_OUTPUT_DIR = r"D:\FF7EC_Decrypted_Assets"

# Subdirectory Names for Organized Asset Extraction
SUBDIR_BUNDLES = "bundles"
SUBDIR_AUDIO_CRIWARE = "audio_criware"
SUBDIR_VIDEOS_RAW = "videos"
SUBDIR_OTHER_RAW = "other_raw"
SUBDIR_CONVERTED_VIDEOS = "converted_videos"
SUBDIR_CONVERTED_AUDIO = "converted_audio"

# Media Formats
VIDEO_FORMAT_MP4 = "mp4"
VIDEO_FORMAT_WEBM = "webm"
SUPPORTED_VIDEO_FORMATS = [VIDEO_FORMAT_MP4, VIDEO_FORMAT_WEBM]
DEFAULT_VIDEO_FORMAT = VIDEO_FORMAT_MP4

AUDIO_FORMAT_MP3 = "mp3"
AUDIO_FORMAT_FLAC = "flac"
AUDIO_FORMAT_WAV = "wav"
SUPPORTED_AUDIO_FORMATS = [AUDIO_FORMAT_MP3, AUDIO_FORMAT_FLAC, AUDIO_FORMAT_WAV]
DEFAULT_AUDIO_FORMAT = AUDIO_FORMAT_MP3

# Extraction Scope Modes
SCOPE_ALL = "all"
SCOPE_VIDEO_ONLY = "video_only"
SCOPE_AUDIO_ONLY = "audio_only"
SCOPE_BUNDLES_ONLY = "bundles_only"
SUPPORTED_SCOPES = [SCOPE_ALL, SCOPE_VIDEO_ONLY, SCOPE_AUDIO_ONLY, SCOPE_BUNDLES_ONLY]
DEFAULT_SCOPE = SCOPE_ALL

SCOPE_LABELS = {
    SCOPE_ALL: "All Assets (Bundles + Audio + Video)",
    SCOPE_VIDEO_ONLY: "Video Only (USM Cutscenes & Animations)",
    SCOPE_AUDIO_ONLY: "Audio Only (CRI ACB/AWB Soundtracks & SFX)",
    SCOPE_BUNDLES_ONLY: "Bundles Only (3D Models, Textures, Meshes)",
}

SCOPE_DISPLAY_TO_VAL = {
    "All Assets (Bundles + Audio + Video)": SCOPE_ALL,
    "Video Only (USM Cutscenes & Animations)": SCOPE_VIDEO_ONLY,
    "Audio Only (CRI ACB/AWB Soundtracks & SFX)": SCOPE_AUDIO_ONLY,
    "Bundles Only (3D Models, Textures, Meshes)": SCOPE_BUNDLES_ONLY,
}
SCOPE_VAL_TO_DISPLAY = {v: k for k, v in SCOPE_DISPLAY_TO_VAL.items()}

# Performance & Concurrency
CPU_COUNT = os.cpu_count() or 4
DEFAULT_WORKER_THREADS = min(32, max(4, CPU_COUNT * 2))
MIN_WORKER_THREADS = 1
MAX_WORKER_THREADS = 64

# Binary Magic Signatures
MAGIC_UNITYFS = b"UnityFS"
MAGIC_CRI_ACB = b"@UTF"
MAGIC_CRI_AWB = b"AFS2"
MAGIC_CRI_USM = b"CRID"
MAGIC_OGG = b"OggS"
MAGIC_RIFF = b"RIFF"
MAGIC_FTYP = b"ftyp"

# External Dependency Download URLs
VGMSTREAM_RELEASE_URL = "https://github.com/vgmstream/vgmstream-releases/releases/latest/download/vgmstream-win64.zip"
FFMPEG_RELEASE_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
