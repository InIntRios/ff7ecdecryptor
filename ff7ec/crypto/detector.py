"""
File Type Identification and Binary Metadata Extraction
Detects CRI USM original video filenames and binary file signatures.
"""

import os
import re
from typing import Tuple

from ff7ec.constants import (
    SUBDIR_BUNDLES,
    SUBDIR_AUDIO_CRIWARE,
    SUBDIR_VIDEOS_RAW,
    SUBDIR_OTHER_RAW,
    MAGIC_UNITYFS,
    MAGIC_CRI_ACB,
    MAGIC_CRI_AWB,
    MAGIC_CRI_USM,
    MAGIC_OGG,
    MAGIC_RIFF,
    MAGIC_FTYP,
)


class FileDetector:
    """Detects file categories, extensions, and embedded media metadata."""

    @staticmethod
    def detect_file_info(data: bytes) -> Tuple[str, str]:
        """
        Identifies the underlying file type using binary magic headers.
        Returns: (category_folder, extension)
        """
        data_len = len(data)
        if data_len >= 7 and data[:7] == MAGIC_UNITYFS:
            return (SUBDIR_BUNDLES, ".bundle")
        if data_len >= 4:
            if data[:4] == MAGIC_CRI_ACB:
                return (SUBDIR_AUDIO_CRIWARE, ".acb")
            if data[:4] == MAGIC_CRI_AWB:
                return (SUBDIR_AUDIO_CRIWARE, ".awb")
            if data[:4] == MAGIC_CRI_USM:
                return (SUBDIR_VIDEOS_RAW, ".usm")
            if data[:4] == MAGIC_OGG:
                return ("audio", ".ogg")
            if data[:4] == MAGIC_RIFF:
                return ("audio", ".wav")
        if data_len >= 8 and data[4:8] == MAGIC_FTYP:
            return (SUBDIR_VIDEOS_RAW, ".mp4")
        if data_len > 0 and data[0] == 0x01:
            return (SUBDIR_BUNDLES, ".bundle")
        return (SUBDIR_OTHER_RAW, ".bin")

    @staticmethod
    def extract_crid_original_name(data: bytes, fallback_name: str) -> str:
        """
        Extracts the original embedded filename from the CRI USM header.
        Examples:
          d:\\jenkins-agent\\...\\story_ac_001.usm -> story_ac_001
          gacha_weapon_49007s.usm -> gacha_weapon_49007s
        """
        try:
            header_text = data[:65536].decode("latin1", errors="ignore")
            match = re.search(r"[\\/]([a-zA-Z0-9_\-]+)\.usm", header_text, re.IGNORECASE)
            if match:
                return match.group(1)
            match = re.search(r"\b([a-zA-Z0-9_\-]+)\.usm", header_text, re.IGNORECASE)
            if match:
                return match.group(1)
        except Exception:
            pass
        return fallback_name

    @classmethod
    def extract_crid_original_name_from_file(cls, usm_path: str) -> str:
        """Reads up to 64KB from a USM file on disk and extracts its original embedded name."""
        base = os.path.splitext(os.path.basename(usm_path))[0]
        try:
            with open(usm_path, "rb") as f:
                header_data = f.read(65536)
            return cls.extract_crid_original_name(header_data, base)
        except Exception:
            return base


# Functional aliases for backward compatibility
detect_file_info = FileDetector.detect_file_info
extract_crid_original_name = FileDetector.extract_crid_original_name
extract_crid_original_name_from_file = FileDetector.extract_crid_original_name_from_file
