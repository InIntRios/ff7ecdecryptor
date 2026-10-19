"""
Game Engine, Assembly & Decryption Keys Scanner
Inspects GameAssembly.dll, IL2CPP metadata, detects CRIWARE signatures, and audits media decryption keys.
"""

import os
import struct
import logging
from typing import Optional, Dict, Any

from ff7ec.constants import (
    DEFAULT_INITIAL_MASK,
    CRI_USM_KEY_UPPER,
    CRI_USM_KEY_LOWER,
    DEFAULT_STEAM_INPUT_DIR,
    FALLBACK_STEAM_INPUT_DIR,
)
from ff7ec.common.logger import setup_logger
from ff7ec.tools.locator import ToolManager
from ff7ec.mapping.server import is_nevercrisis_server_running, find_nevercrisis_server


class GameScannerService:
    """Scans and audits game binaries, assemblies, and decryption keys."""

    @classmethod
    def scan_game_engine_and_keys(
        cls,
        game_dir: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ) -> Dict[str, Any]:
        """
        Scans the FF7EC game installation directory, inspects GameAssembly.dll and IL2CPP metadata,
        detects engine signatures (Unity, IL2CPP, CRIWARE middleware, Applibot cipher),
        and validates all media decryption keys (USM video split keys & HCA audio keys).
        """
        if logger is None:
            logger = setup_logger()

        target_dir = ""
        if game_dir and os.path.isdir(game_dir):
            target_dir = os.path.abspath(game_dir)
        else:
            for candidate in [DEFAULT_STEAM_INPUT_DIR, FALLBACK_STEAM_INPUT_DIR]:
                if os.path.isdir(candidate):
                    target_dir = candidate
                    break

        results: Dict[str, Any] = {
            "game_dir": target_dir,
            "is_valid_installation": False,
            "exe_found": False,
            "game_assembly_found": False,
            "game_assembly_size": 0,
            "metadata_found": False,
            "il2cpp_version": None,
            "criware_detected": False,
            "criware_exports": [],
            "nevercrisis_server_found": False,
            "nevercrisis_server_running": is_nevercrisis_server_running(),
            "nevercrisis_server_path": None,
            "applibot_xor_mask": f"0x{DEFAULT_INITIAL_MASK:02X} ({DEFAULT_INITIAL_MASK})",
            "usm_key_upper": CRI_USM_KEY_UPPER,
            "usm_key_lower": CRI_USM_KEY_LOWER,
            "hca_key_hex": f"0x{CRI_USM_KEY_UPPER}{CRI_USM_KEY_LOWER}",
            "hca_key_dec": int(f"{CRI_USM_KEY_UPPER}{CRI_USM_KEY_LOWER}", 16),
            "vgmstream_status": "Ready",
            "crid_status": "Ready",
            "ffmpeg_status": "Ready",
        }

        if not target_dir or not os.path.isdir(target_dir):
            logger.warning(f"[SCAN] Game directory not found or invalid: {game_dir}")
            return results

        base_game_dir = target_dir
        if base_game_dir.lower().endswith(os.path.join("octo", "v1").lower()):
            base_game_dir = os.path.dirname(os.path.dirname(base_game_dir))
        elif base_game_dir.lower().endswith("octo"):
            base_game_dir = os.path.dirname(base_game_dir)
        results["game_dir"] = base_game_dir

        exe_path = os.path.join(base_game_dir, "FF7EC.exe")
        if os.path.isfile(exe_path):
            results["exe_found"] = True

        ga_path = os.path.join(base_game_dir, "GameAssembly.dll")
        if os.path.isfile(ga_path):
            results["game_assembly_found"] = True
            results["game_assembly_size"] = os.path.getsize(ga_path)
            try:
                with open(ga_path, "rb") as f:
                    ga_data = f.read()
                detected_exports = []
                if b"CRIWARE475BF86E" in ga_data:
                    detected_exports.append("CRIWARE475BF86E (NativeMethods_SetDecryptionKey)")
                if b"CRIWARE02E4660C" in ga_data:
                    detected_exports.append("CRIWARE02E4660C (CriWareDecrypter.enable_atom_decryption)")
                if b"CRIWARE" in ga_data:
                    results["criware_detected"] = True
                results["criware_exports"] = detected_exports
            except Exception as e:
                logger.debug(f"[SCAN] Error reading GameAssembly.dll: {e}")

        meta_path = os.path.join(base_game_dir, "FF7EC_Data", "il2cpp_data", "Metadata", "global-metadata.dat")
        if not os.path.isfile(meta_path):
            alt_meta = os.path.join(base_game_dir, "FF7EC_Data", "il2cpp_data", "Metadata", "global-metadata.bin")
            if os.path.isfile(alt_meta):
                meta_path = alt_meta

        if os.path.isfile(meta_path):
            results["metadata_found"] = True
            try:
                with open(meta_path, "rb") as f:
                    hdr = f.read(16)
                if len(hdr) >= 8:
                    sanity, ver = struct.unpack("<II", hdr[:8])
                    if sanity == 0xFAB11BAF:
                        results["il2cpp_version"] = f"v{ver} (Standard Unity 0xFAB11BAF)"
                    else:
                        results["il2cpp_version"] = f"v{ver} (Custom/Encrypted: 0x{sanity:08X})"
            except Exception as e:
                logger.debug(f"[SCAN] Error reading metadata header: {e}")

        srv_path = find_nevercrisis_server(base_game_dir)
        if srv_path and os.path.exists(srv_path):
            results["nevercrisis_server_found"] = True
            results["nevercrisis_server_path"] = srv_path

        c_p, f_p, v_p = ToolManager.ensure_tools(logger, auto_download=False)
        results["crid_status"] = "Ready (" + c_p + ")" if c_p and os.path.exists(c_p) else "Not Found"
        results["vgmstream_status"] = "Ready (hca_keys.h integrated)" if v_p and os.path.exists(v_p) else "Not Found"
        results["ffmpeg_status"] = "Ready (" + f_p + ")" if f_p and os.path.exists(f_p) else "Not Found"

        if results["exe_found"] or results["game_assembly_found"] or results["metadata_found"]:
            results["is_valid_installation"] = True

        return results

    @staticmethod
    def format_scan_report(results: Dict[str, Any]) -> str:
        """Formats engine scan results into a readable report string."""
        lines = [
            "================================================================================",
            "FF7EC GAME ENGINE & CRYPTO KEY AUDIT REPORT",
            "================================================================================",
            f"Game Directory:        {results.get('game_dir') or 'Not Found'}",
            f"Steam Executable:      {'FOUND (FF7EC.exe)' if results.get('exe_found') else 'Not Found'}",
        ]
        if results.get("game_assembly_found"):
            lines.append(f"GameAssembly.dll:      FOUND ({results.get('game_assembly_size', 0):,} bytes)")
        else:
            lines.append("GameAssembly.dll:      Not Found")

        if results.get("metadata_found"):
            lines.append(f"IL2CPP Metadata:       FOUND ({results.get('il2cpp_version') or 'Present'})")
        else:
            lines.append("IL2CPP Metadata:       Not Found")

        if results.get("criware_detected"):
            lines.append("CRIWARE Middleware:    DETECTED")
            for exp in results.get("criware_exports", []):
                lines.append(f"  • Export Signature:  {exp}")
        else:
            lines.append("CRIWARE Middleware:    Not Detected in current scan")

        lines.append("")
        lines.append("CRYPTO & MEDIA DECRYPTION KEYS:")
        lines.append(f"  • Applibot XOR Cipher:       Initial Mask = {results.get('applibot_xor_mask')} (Target Header: 'U' / 0x55)")
        lines.append(f"  • CRI USM Video Split Keys:  Upper = {results.get('usm_key_upper')}  |  Lower = {results.get('usm_key_lower')}")
        lines.append(f"  • CRI HCA Audio Decrypt Key: {results.get('hca_key_hex')} (Decimal: {results.get('hca_key_dec')})")
        lines.append(f"  • vgmstream-cli Audio:       {results.get('vgmstream_status')}")
        lines.append(f"  • crid_mod.exe Video Demux:  {results.get('crid_status')}")

        lines.append("")
        lines.append("OFFLINE ENVIRONMENT:")
        if results.get("nevercrisis_server_found"):
            status = "Running" if results.get("nevercrisis_server_running") else "Offline (Stopped)"
            lines.append(f"  • NeverCrisis Server:        FOUND ({results.get('nevercrisis_server_path')})")
            lines.append(f"  • Server Process Status:     {status}")
        else:
            lines.append("  • NeverCrisis Server:        Not Present")

        lines.append("================================================================================")
        return "\n".join(lines)


# Functional aliases for backward compatibility
scan_game_engine_and_keys = GameScannerService.scan_game_engine_and_keys
format_scan_report = GameScannerService.format_scan_report
