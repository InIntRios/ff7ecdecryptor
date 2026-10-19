"""
CRIWARE Audio Bank Decoder and Transcoder
Decodes CRI ACB/AWB wavebanks into individual audio tracks (MP3, FLAC, WAV) using vgmstream-cli.
"""

import os
import sys
import time
import shutil
import subprocess
import threading
import logging

from ff7ec.constants import (
    AUDIO_FORMAT_MP3,
    AUDIO_FORMAT_FLAC,
    AUDIO_FORMAT_WAV,
)
from ff7ec.tools.locator import ToolManager


class CriwareAudioTranscoder:
    """Decodes and transcodes CRIWARE ACB/AWB audio banks."""

    @staticmethod
    def convert_criware_audio(
        source_audio_file: str,
        target_dir: str,
        target_format: str,
        vgmstream_path: str,
        logger: logging.Logger,
    ) -> int:
        """
        Decodes a CRIWARE ACB or AWB bank (or standalone WAV/ADX) using vgmstream-cli,
        extracts all streams with their internal sound cue names, and transcodes them into MP3, FLAC, or WAV.
        All outputs are saved directly into target_dir (e.g., converted_audio/).
        Returns the count of successfully created audio tracks.
        """
        if not vgmstream_path or not os.path.exists(vgmstream_path):
            return 0

        os.makedirs(target_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(source_audio_file))[0]
        ext_lower = os.path.splitext(source_audio_file)[1].lower()

        # Temporary worker directory to hold extracted WAVs
        temp_dir = os.path.join(target_dir, f"_temp_{threading.get_ident()}_{int(time.time() * 1000) % 10000}")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            startupinfo = ToolManager.get_hidden_process_startupinfo()

            if ext_lower == ".acb":
                # Extract all cues using internal stream names (?n.wav)
                cmd = [vgmstream_path, "-i", "-s", "1", "-S", "0", "-o", os.path.join(temp_dir, "?n.wav"), source_audio_file]
            elif ext_lower == ".awb":
                # Extract subsongs with indexed names
                cmd = [vgmstream_path, "-i", "-s", "1", "-S", "0", "-o", os.path.join(temp_dir, f"{base_name}_track_?s.wav"), source_audio_file]
            else:
                # Standalone single audio file
                cmd = [vgmstream_path, "-i", "-o", os.path.join(temp_dir, f"{base_name}.wav"), source_audio_file]

            subprocess.run(cmd, capture_output=True, text=True, timeout=180, startupinfo=startupinfo)

            extracted_wavs = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.lower().endswith(".wav")]
            if not extracted_wavs:
                return 0

            fmt = target_format.lower().strip()
            count = 0

            for wav_path in extracted_wavs:
                raw_title = os.path.splitext(os.path.basename(wav_path))[0]
                if raw_title == "?n" or not raw_title:
                    raw_title = f"{base_name}_{count + 1}"

                dest_path = os.path.join(target_dir, f"{raw_title}.{fmt}")

                # Avoid file collisions
                idx = 1
                while os.path.exists(dest_path) and os.path.getsize(dest_path) == 0:
                    dest_path = os.path.join(target_dir, f"{raw_title}_{idx}.{fmt}")
                    idx += 1

                if fmt == AUDIO_FORMAT_WAV:
                    shutil.move(wav_path, dest_path)
                    count += 1
                elif fmt == AUDIO_FORMAT_FLAC:
                    cmd_ff = ["ffmpeg", "-y", "-i", wav_path, "-c:a", "flac", dest_path]
                    subprocess.run(cmd_ff, capture_output=True, text=True, timeout=60, startupinfo=startupinfo)
                    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
                        count += 1
                    try:
                        os.remove(wav_path)
                    except Exception:
                        pass
                else:
                    # Default MP3
                    cmd_ff = ["ffmpeg", "-y", "-i", wav_path, "-c:a", "libmp3lame", "-q:a", "2", dest_path]
                    subprocess.run(cmd_ff, capture_output=True, text=True, timeout=60, startupinfo=startupinfo)
                    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
                        count += 1
                    try:
                        os.remove(wav_path)
                    except Exception:
                        pass

            return count

        except Exception as e:
            logger.error(f"Error extracting audio from {source_audio_file}: {e}")
            return 0
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


# Functional alias for backward compatibility
convert_criware_audio = CriwareAudioTranscoder.convert_criware_audio
