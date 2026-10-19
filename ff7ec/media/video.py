"""
CRI USM Video Demuxing and Container Transcoding
Demuxes CRI USM containers, extracts embedded audio, and muxes video + audio into MP4 or WebM via FFmpeg.
"""

import os
import sys
import time
import shutil
import subprocess
import threading
import logging
from typing import Optional

from ff7ec.constants import (
    CRI_USM_KEY_UPPER,
    CRI_USM_KEY_LOWER,
    VIDEO_FORMAT_WEBM,
)
from ff7ec.tools.locator import ToolManager


class UsmVideoTranscoder:
    """Handles CRI USM video extraction and container transcoding to MP4/WebM."""

    @staticmethod
    def convert_usm_video(
        usm_path: str,
        output_video_path: str,
        target_format: str,
        crid_mod_path: str,
        vgmstream_path: Optional[str],
        logger: logging.Logger,
    ) -> bool:
        """
        Decodes a CRI USM container into raw streams, extracts and decodes any embedded HCA or ADX audio
        to uncompressed WAV via vgmstream-cli, then muxes video + audio into standard MP4 or WebM via FFmpeg.
        Target output file is saved into output_video_path (e.g., converted_videos/name.mp4).
        """
        if not crid_mod_path or not os.path.exists(crid_mod_path):
            return False

        os.makedirs(os.path.dirname(os.path.abspath(output_video_path)), exist_ok=True)

        # Isolated worker temp folder to prevent multi-threaded file collisions
        temp_dir = os.path.join(
            os.path.dirname(output_video_path),
            f"_usm_{threading.get_ident()}_{int(time.time() * 1000) % 100000}_{os.getpid()}",
        )
        os.makedirs(temp_dir, exist_ok=True)
        temp_usm = os.path.join(temp_dir, "input.usm")

        try:
            shutil.copy2(usm_path, temp_usm)

            # Demux using crid_mod WITHOUT -c flag (so HCA audio stream is demuxed without corruption)
            cmd_crid = [
                crid_mod_path,
                "-b", CRI_USM_KEY_UPPER,
                "-a", CRI_USM_KEY_LOWER,
                "-v", "-x", "-i",
                temp_usm,
            ]

            startupinfo = ToolManager.get_hidden_process_startupinfo()
            subprocess.run(
                cmd_crid,
                capture_output=True,
                text=True,
                timeout=180,
                startupinfo=startupinfo,
                cwd=temp_dir,
            )

            # Detect demuxed video and audio files in temp_dir
            video_file = None
            raw_audio_file = None

            for fname in os.listdir(temp_dir):
                fp = os.path.join(temp_dir, fname)
                if fname == "input.usm" or not os.path.isfile(fp) or os.path.getsize(fp) == 0:
                    continue
                fext = os.path.splitext(fname)[1].lower()
                if fext in (".m2v", ".ivf"):
                    video_file = fp
                elif fext in (".adx", ".hca", ".wav", ".ogg"):
                    raw_audio_file = fp

            if not video_file:
                return False

            # Decode raw audio stream to standard PCM WAV
            wav_audio_file = None
            if raw_audio_file and os.path.exists(raw_audio_file) and os.path.getsize(raw_audio_file) > 0:
                try:
                    with open(raw_audio_file, "rb") as af:
                        hdr = af.read(16)
                except Exception:
                    hdr = b""

                # If header is CRI HCA (either masked \xc8\xc3\xc1 or standard HCA\x00)
                if hdr.startswith(b"\xc8\xc3\xc1") or hdr.startswith(b"HCA"):
                    hca_target = os.path.join(temp_dir, "stream.hca")
                    if raw_audio_file != hca_target:
                        try:
                            shutil.move(raw_audio_file, hca_target)
                            raw_audio_file = hca_target
                        except Exception:
                            pass

                if vgmstream_path and os.path.exists(vgmstream_path):
                    out_wav = os.path.join(temp_dir, "stream.wav")
                    cmd_vgm = [vgmstream_path, "-o", out_wav, raw_audio_file]
                    subprocess.run(cmd_vgm, capture_output=True, text=True, timeout=120, startupinfo=startupinfo)
                    if os.path.exists(out_wav) and os.path.getsize(out_wav) > 0:
                        wav_audio_file = out_wav
                elif raw_audio_file.lower().endswith(".wav"):
                    wav_audio_file = raw_audio_file

            # Transcode & mux container with FFmpeg
            fmt = target_format.lower().strip()
            if fmt == VIDEO_FORMAT_WEBM:
                if wav_audio_file:
                    cmd_ffmpeg = [
                        "ffmpeg", "-y", "-i", video_file, "-i", wav_audio_file,
                        "-c:v", "copy", "-c:a", "libopus", "-b:a", "192k", "-shortest", output_video_path,
                    ]
                else:
                    cmd_ffmpeg = ["ffmpeg", "-y", "-i", video_file, "-c:v", "copy", output_video_path]
            else:
                # Default MP4
                if wav_audio_file:
                    cmd_ffmpeg = [
                        "ffmpeg", "-y", "-i", video_file, "-i", wav_audio_file,
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", output_video_path,
                    ]
                else:
                    cmd_ffmpeg = ["ffmpeg", "-y", "-i", video_file, "-c:v", "copy", output_video_path]

            subprocess.run(cmd_ffmpeg, capture_output=True, text=True, timeout=300, startupinfo=startupinfo)

            return os.path.exists(output_video_path) and os.path.getsize(output_video_path) > 0

        except Exception as e:
            logger.error(f"FFmpeg video conversion error for {output_video_path}: {e}")
            return False
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


# Functional alias for backward compatibility
convert_usm_video = UsmVideoTranscoder.convert_usm_video
