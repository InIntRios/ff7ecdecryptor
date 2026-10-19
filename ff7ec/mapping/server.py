"""
NeverCrisis Offline Server Integration
Discovers, detects, and controls FF7ECServer.exe when operating in offline/emulator mode.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional

from ff7ec.constants import (
    BASE_DIR,
    TOOLS_DIR,
    DEFAULT_STEAM_INPUT_DIR,
    FALLBACK_STEAM_INPUT_DIR,
)


class NeverCrisisServerManager:
    """Manages detection and invocation of the NeverCrisis offline game server."""

    @staticmethod
    def is_running() -> bool:
        """Checks if NeverCrisis offline server (FF7ECServer.exe) is currently running."""
        if sys.platform != "win32":
            return False
        try:
            cmd = 'tasklist /FI "IMAGENAME eq FF7ECServer.exe" /NH'
            out = subprocess.check_output(cmd, shell=True, text=True, errors="replace")
            return "FF7ECServer.exe" in out
        except Exception:
            return False

    @staticmethod
    def find_server(game_hint_dir: Optional[str] = None) -> Optional[str]:
        """
        Locates FF7ECServer.exe in the game folder, Steam directories, or project tools.
        Returns absolute normalized path if found, or None.
        """
        if game_hint_dir and os.path.isdir(game_hint_dir):
            p = Path(os.path.abspath(game_hint_dir))
            for _ in range(5):
                candidate = p / "FF7ECServer.exe"
                if candidate.is_file():
                    return os.path.normpath(str(candidate))
                if p.parent == p:
                    break
                p = p.parent

        candidates = [
            os.path.join(DEFAULT_STEAM_INPUT_DIR, "FF7ECServer.exe"),
            os.path.join(FALLBACK_STEAM_INPUT_DIR, "FF7ECServer.exe"),
            os.path.join(BASE_DIR, "FF7ECServer.exe"),
            os.path.join(TOOLS_DIR, "FF7ECServer.exe"),
        ]

        for c in candidates:
            if os.path.isfile(c):
                return os.path.normpath(c)
        return None

    @classmethod
    def start_server(cls, server_path: Optional[str] = None) -> bool:
        """
        Launches FF7ECServer.exe detached in its own console window.
        Returns True if started successfully, False otherwise.
        """
        if not server_path:
            server_path = cls.find_server()
        if not server_path or not os.path.isfile(server_path):
            return False
        try:
            server_dir = os.path.dirname(server_path)
            if sys.platform == "win32":
                subprocess.Popen([server_path], cwd=server_dir, creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen([server_path], cwd=server_dir)
            return True
        except Exception:
            return False


# Functional aliases for backward compatibility
is_nevercrisis_server_running = NeverCrisisServerManager.is_running
find_nevercrisis_server = NeverCrisisServerManager.find_server
start_nevercrisis_server = NeverCrisisServerManager.start_server
