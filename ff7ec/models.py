"""
Final Fantasy VII: Ever Crisis (FF7EC)
Domain Models and Data Transfer Objects (DTO)
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass(frozen=True)
class FileInfo:
    """Encapsulates detected file metadata and classification."""
    category_folder: str
    extension: str
    is_crid_video: bool = False
    is_cri_audio: bool = False
    detected_name: Optional[str] = None


@dataclass
class ScanReport:
    """Encapsulates the audit and inspection report of the game engine and decryption keys."""
    game_dir: str
    game_assembly_path: Optional[str] = None
    il2cpp_metadata_path: Optional[str] = None
    engine_type: str = "IL2CPP (Unity x64)"
    applibot_xor_mask: str = "0xAB standard (Applibot dynamic string cipher)"
    cri_usm_key_upper: str = "000011DA"
    cri_usm_key_lower: str = "4DE45ADE"
    hca_key_hex: str = "0x000011DA4DE45ADE"
    hca_key_description: str = "Square Enix / Applibot CRIWARE HCA Audio Decryption Key"
    nevercrisis_server_path: Optional[str] = None
    nevercrisis_server_running: bool = False
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProgressUpdate:
    """Represents a snapshot of batch extraction progress."""
    processed_count: int
    total_files: int
    success_count: int
    skipped_count: int
    speed_files_per_sec: float
    eta_seconds: float

    @property
    def percentage(self) -> float:
        return (self.processed_count / self.total_files * 100) if self.total_files > 0 else 0.0


@dataclass
class ExtractionJob:
    """Configuration parameter object for an extraction job."""
    source_dir: str
    output_dir: str
    mapping_path: str = ""
    crid_mod_path: str = ""
    vgmstream_path: str = ""
    convert_video: bool = True
    convert_audio: bool = True
    video_format: str = "mp4"
    audio_format: str = "mp3"
    extract_scope: str = "all"
    worker_threads: int = 16
    resume: bool = True
