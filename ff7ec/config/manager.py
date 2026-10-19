"""
Configuration & Path Management
Handles JSON persistence, default directory discovery, and asset path normalization.
"""

import os
import sys
import json
from typing import Dict, Any, Optional

from ff7ec.constants import (
    BASE_DIR,
    CONFIG_FILE,
    TOOLS_DIR,
    DEFAULT_STEAM_INPUT_DIR,
    FALLBACK_STEAM_INPUT_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_VIDEO_FORMAT,
    DEFAULT_AUDIO_FORMAT,
    DEFAULT_SCOPE,
    DEFAULT_WORKER_THREADS,
)


def get_initial_input_dir() -> str:
    """Returns the default Steam game installation path."""
    return DEFAULT_STEAM_INPUT_DIR


def get_initial_output_dir() -> str:
    """Returns the default destination root path."""
    return DEFAULT_OUTPUT_DIR


def get_initial_mapping_path() -> str:
    """Scans common locations to auto-locate octocacheevai.json."""
    candidates = [
        os.path.join(BASE_DIR, "data", "octo", "octocacheevai.json"),
        os.path.join(BASE_DIR, "octocacheevai.json"),
        os.path.join(BASE_DIR, "data", "octocacheevai.json"),
        os.path.join(DEFAULT_STEAM_INPUT_DIR, "pdb", "3001", "323173179", "octocacheevai.json"),
        os.path.join(DEFAULT_STEAM_INPUT_DIR, "octo", "pdb", "3001", "323173179", "octocacheevai.json"),
        os.path.join(FALLBACK_STEAM_INPUT_DIR, "pdb", "3001", "323173179", "octocacheevai.json"),
        os.path.join(FALLBACK_STEAM_INPUT_DIR, "octo", "pdb", "3001", "323173179", "octocacheevai.json"),
        r"C:\FF7EC_Decrypted_Assets\octocacheevai.json",
        r"D:\FF7EC_Decrypted_Assets\octocacheevai.json",
    ]
    for c in candidates:
        if os.path.exists(c) and os.path.getsize(c) > 0:
            return os.path.normpath(c)
    return ""


def resolve_game_asset_dir(path: str) -> str:
    """
    Resolves the actual asset directory containing game assets.
    If the user selects the root FF7EC game folder (e.g. .../FF7EC),
    automatically detects and resolves to .../FF7EC/octo/v1.
    If they already selected octo/v1 or another subfolder, preserves it.
    """
    if not path:
        return ""
    p = os.path.normpath(path)
    candidate_octo_v1 = os.path.join(p, "octo", "v1")
    if os.path.isdir(candidate_octo_v1):
        return candidate_octo_v1
    candidate_v1 = os.path.join(p, "v1")
    if os.path.isdir(candidate_v1) and os.path.basename(p).lower() == "octo":
        return candidate_v1
    return p


def get_app_icon_path() -> str:
    """
    Locates the application icon (app.ico), checking PyInstaller MEIPASS,
    BASE_DIR, executable directory, and fallback paths.
    """
    candidates = []
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        candidates.append(os.path.join(sys._MEIPASS, "app.ico"))
    candidates.append(os.path.join(BASE_DIR, "app.ico"))
    if "__file__" in globals():
        candidates.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.ico"))
    candidates.append(os.path.join(os.getcwd(), "app.ico"))
    for c in candidates:
        if c and os.path.isfile(c) and os.path.getsize(c) > 0:
            return os.path.abspath(c)
    return ""


DEFAULT_CONFIG: Dict[str, Any] = {
    "source_dir": get_initial_input_dir(),
    "output_dir": get_initial_output_dir(),
    "mapping_path": get_initial_mapping_path(),
    "crid_mod_path": os.path.join(TOOLS_DIR, "crid_mod.exe"),
    "vgmstream_path": os.path.join(TOOLS_DIR, "vgmstream-cli.exe"),
    "convert_video": True,
    "convert_audio": True,
    "video_format": DEFAULT_VIDEO_FORMAT,
    "audio_format": DEFAULT_AUDIO_FORMAT,
    "extract_scope": DEFAULT_SCOPE,
    "worker_threads": DEFAULT_WORKER_THREADS,
    "resume_mode": True,
    "ui_theme": "Material Dark",
    "window_geometry": "1040x800+100+60",
}


class ConfigManager:
    """Manages application configuration loading, validation, and JSON persistence."""

    def __init__(self, config_path: str = CONFIG_FILE):
        self.config_path = config_path

    def load_config(self) -> Dict[str, Any]:
        """Loads saved configuration with fallback defaults."""
        config = dict(DEFAULT_CONFIG)
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    config.update(saved)
            except Exception:
                pass
        # Auto-populate mapping path if missing or pointing to nonexistent file
        if not config.get("mapping_path") or not os.path.exists(config.get("mapping_path", "")):
            default_map = get_initial_mapping_path()
            if default_map:
                config["mapping_path"] = default_map
        return config

    def save_config(self, config: Dict[str, Any]) -> bool:
        """Persists configuration to disk in JSON format."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception:
            return False


# Global singleton instance for convenient access
_default_manager = ConfigManager()


def load_config() -> Dict[str, Any]:
    return _default_manager.load_config()


def save_config(config: Dict[str, Any]) -> bool:
    return _default_manager.save_config(config)
