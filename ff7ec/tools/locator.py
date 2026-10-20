"""
External Dependency Management & Tool Locator
Locates, verifies, downloads, and configures external binaries:
1. crid_mod.exe (CRI USM video demuxer)
2. vgmstream-cli.exe (CRI ACB/AWB audio decoder)
3. ffmpeg.exe (Video/audio transcode & container muxer)
"""

import os
import sys
import shutil
import zipfile
import subprocess
import urllib.request
import logging
from typing import Tuple, Optional

from ff7ec.constants import (
    BASE_DIR,
    TOOLS_DIR,
    VGMSTREAM_RELEASE_URL,
    FFMPEG_RELEASE_URL,
)


class ToolManager:
    """Manages discovery, verification, and automatic installation of external CLI tools."""

    @staticmethod
    def get_hidden_process_startupinfo() -> Optional[subprocess.STARTUPINFO]:
        """Returns Windows startupinfo configured to suppress console popups."""
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            return startupinfo
        return None

    @classmethod
    def locate_crid_mod(cls, logger: Optional[logging.Logger] = None) -> Optional[str]:
        """Searches for crid_mod.exe across standard paths and synchronizes to tools directory."""
        candidates = [
            os.path.join(TOOLS_DIR, "crid_mod.exe"),
            r"C:\FF7\Tools\crid_mod.exe",
            r"C:\FF7\Tools\FF7ECProcessor\crid_mod.exe",
            r"C:\FF7\Tools\FF7ECProcessor\tools\crid_mod.exe",
            r"C:\FF7\Tools\FF7ECProcessor\bin\crid_mod.exe",
            os.path.join(BASE_DIR, "crid_mod.exe"),
        ]
        crid_path = None
        for c in candidates:
            if os.path.exists(c):
                crid_path = c
                break

        target_local_crid = os.path.join(TOOLS_DIR, "crid_mod.exe")
        if crid_path and crid_path != target_local_crid and not os.path.exists(target_local_crid):
            try:
                shutil.copy2(crid_path, target_local_crid)
                crid_path = target_local_crid
                if logger:
                    logger.info(f"[TOOLS] Synchronized crid_mod.exe into: {target_local_crid}")
            except Exception as e:
                if logger:
                    logger.warning(f"[TOOLS] Could not copy crid_mod.exe to tools directory: {e}")

        if crid_path and os.path.exists(crid_path):
            if logger:
                logger.info(f"[TOOLS] Found crid_mod.exe at: {crid_path}")
            return crid_path
        if logger:
            logger.warning("[TOOLS] crid_mod.exe was not found in known search paths.")
        return None

    @classmethod
    def locate_ffmpeg(cls, auto_download: bool = True, logger: Optional[logging.Logger] = None) -> Optional[str]:
        """Locates ffmpeg in system PATH or tools directory, with automatic installation fallback."""
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            local_ff = os.path.join(TOOLS_DIR, "ffmpeg.exe")
            if os.path.exists(local_ff):
                ffmpeg_path = local_ff
                os.environ["PATH"] = TOOLS_DIR + os.pathsep + os.environ.get("PATH", "")

        if ffmpeg_path:
            if logger:
                logger.info(f"[TOOLS] Found ffmpeg at: {ffmpeg_path}")
            return ffmpeg_path

        if logger:
            logger.warning("[TOOLS] ffmpeg was not detected in system PATH.")

        if auto_download:
            # Try winget first if available
            winget_path = shutil.which("winget")
            if winget_path:
                if logger:
                    logger.info("[TOOLS] Attempting automatic FFmpeg installation via winget...")
                try:
                    subprocess.run(
                        [winget_path, "install", "Gyan.FFmpeg", "--accept-source-agreements", "--accept-package-agreements", "-h"],
                        capture_output=True, text=True, timeout=120, startupinfo=cls.get_hidden_process_startupinfo()
                    )
                    ffmpeg_path = shutil.which("ffmpeg")
                except Exception:
                    pass

            if not ffmpeg_path:
                if logger:
                    logger.info("[TOOLS] Downloading official FFmpeg release essentials package...")
                try:
                    os.makedirs(TOOLS_DIR, exist_ok=True)
                    zip_path = os.path.join(TOOLS_DIR, "ffmpeg_temp.zip")
                    req = urllib.request.Request(FFMPEG_RELEASE_URL, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=45) as response, open(zip_path, "wb") as out_f:
                        shutil.copyfileobj(response, out_f)

                    with zipfile.ZipFile(zip_path, "r") as zf:
                        for member in zf.namelist():
                            if member.endswith("bin/ffmpeg.exe"):
                                with zf.open(member) as source, open(os.path.join(TOOLS_DIR, "ffmpeg.exe"), "wb") as target:
                                    shutil.copyfileobj(source, target)
                                break
                    try:
                        os.remove(zip_path)
                    except Exception:
                        pass

                    local_ff = os.path.join(TOOLS_DIR, "ffmpeg.exe")
                    if os.path.exists(local_ff):
                        ffmpeg_path = local_ff
                        os.environ["PATH"] = TOOLS_DIR + os.pathsep + os.environ.get("PATH", "")
                        if logger:
                            logger.info(f"[TOOLS] Installed ffmpeg.exe at: {ffmpeg_path}")
                except Exception as e:
                    if logger:
                        logger.error(f"[TOOLS] FFmpeg download failed: {e}")

        return ffmpeg_path

    @classmethod
    def locate_vgmstream(cls, auto_download: bool = True, logger: Optional[logging.Logger] = None) -> Optional[str]:
        """Locates vgmstream-cli.exe with automatic GitHub release download fallback."""
        candidates = [
            os.path.join(TOOLS_DIR, "vgmstream-cli.exe"),
            os.path.join(TOOLS_DIR, "vgmstream.exe"),
            shutil.which("vgmstream-cli"),
            shutil.which("vgmstream"),
            r"C:\FF7\Tools\vgmstream-cli.exe",
            r"C:\FF7\Tools\vgmstream.exe",
        ]
        vgmstream_path = None
        for v in candidates:
            if v and os.path.exists(v):
                vgmstream_path = v
                break

        if vgmstream_path and os.path.exists(vgmstream_path):
            if logger:
                logger.info(f"[TOOLS] Found vgmstream-cli at: {vgmstream_path}")
            return vgmstream_path

        if logger:
            logger.warning("[TOOLS] vgmstream-cli was not detected.")

        if auto_download:
            if logger:
                logger.info("[TOOLS] Downloading official vgmstream package for CRIWARE ACB/AWB decoding...")
            try:
                os.makedirs(TOOLS_DIR, exist_ok=True)
                zip_path = os.path.join(TOOLS_DIR, "vgmstream_temp.zip")
                req = urllib.request.Request(VGMSTREAM_RELEASE_URL, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=45) as resp, open(zip_path, "wb") as out_f:
                    shutil.copyfileobj(resp, out_f)

                with zipfile.ZipFile(zip_path, "r") as zf:
                    for member in zf.namelist():
                        if member.endswith((".exe", ".dll")):
                            zf.extract(member, TOOLS_DIR)

                try:
                    os.remove(zip_path)
                except Exception:
                    pass

                local_vgm = os.path.join(TOOLS_DIR, "vgmstream-cli.exe")
                if os.path.exists(local_vgm):
                    vgmstream_path = local_vgm
                    os.environ["PATH"] = TOOLS_DIR + os.pathsep + os.environ.get("PATH", "")
                    if logger:
                        logger.info(f"[TOOLS] Installed vgmstream-cli at: {vgmstream_path}")
            except Exception as e:
                if logger:
                    logger.error(f"[TOOLS] Failed to download vgmstream: {e}")

        return vgmstream_path

    @classmethod
    def ensure_tools(cls, logger: logging.Logger, auto_download: bool = True) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Ensures all three required binaries are available.
        Returns: (crid_mod_path, ffmpeg_path, vgmstream_path)
        """
        os.makedirs(TOOLS_DIR, exist_ok=True)
        crid = cls.locate_crid_mod(logger)
        ffmpeg = cls.locate_ffmpeg(auto_download=auto_download, logger=logger)
        vgm = cls.locate_vgmstream(auto_download=auto_download, logger=logger)
        return crid, ffmpeg, vgm


# Functional alias for backward compatibility
ensure_tools = ToolManager.ensure_tools
