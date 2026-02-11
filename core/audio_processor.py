"""
Audio Processor - Audio utilities for Stoic Wisdom Shorts

Handles: audio normalization, ambient sound selection and mixing,
duration measurement, silence trimming, file cleanup.
"""
import os
import random
from pathlib import Path
from typing import Optional

from loguru import logger
from pydub import AudioSegment

from config.settings import (
    AMBIENT_DIR,
    AUDIO_DIR,
    AMBIENT_VOLUME_RATIO,
    AMBIENT_FADE_IN_MS,
    AMBIENT_FADE_OUT_MS,
)


# ══════════════════════════════════════════════════════════════════════
# FFmpeg Discovery
# ══════════════════════════════════════════════════════════════════════

def find_ffmpeg() -> Optional[str]:
    """Find FFmpeg binary path."""
    custom_path = os.getenv("FFMPEG_PATH", "")
    if custom_path and os.path.exists(custom_path):
        return custom_path

    # Try common locations
    common_paths = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        "/usr/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
    ]
    for p in common_paths:
        if os.path.exists(p):
            return p

    # Assume it's in PATH
    return "ffmpeg"


# Configure pydub
FFMPEG_BIN = find_ffmpeg()
if FFMPEG_BIN:
    AudioSegment.converter = FFMPEG_BIN


# ══════════════════════════════════════════════════════════════════════
# Audio Utilities
# ══════════════════════════════════════════════════════════════════════

def normalize_audio(audio: AudioSegment, target_dbfs: float = -20.0) -> AudioSegment:
    """
    Normalize audio volume to a target dBFS level.

    Args:
        audio: Input audio segment.
        target_dbfs: Target loudness in dBFS.

    Returns:
        Normalized AudioSegment.
    """
    change_in_dbfs = target_dbfs - audio.dBFS
    return audio.apply_gain(change_in_dbfs)


def trim_silence(
    audio: AudioSegment,
    silence_thresh: float = -50.0,
    chunk_size: int = 10,
) -> AudioSegment:
    """
    Trim leading and trailing silence from audio.

    Args:
        audio: Input audio segment.
        silence_thresh: Volume threshold for silence (dBFS).
        chunk_size: Size of chunks to check in ms.

    Returns:
        Trimmed AudioSegment.
    """
    # Find start of sound
    start_trim = 0
    for i in range(0, len(audio), chunk_size):
        if audio[i:i + chunk_size].dBFS > silence_thresh:
            start_trim = max(0, i - chunk_size)
            break

    # Find end of sound
    end_trim = len(audio)
    for i in range(len(audio) - chunk_size, 0, -chunk_size):
        if audio[i:i + chunk_size].dBFS > silence_thresh:
            end_trim = min(len(audio), i + chunk_size * 2)
            break

    return audio[start_trim:end_trim]


def get_audio_duration(path: Path) -> float:
    """Get the duration of an audio file in seconds."""
    try:
        audio = AudioSegment.from_file(str(path))
        return len(audio) / 1000.0
    except Exception as e:
        logger.error(f"Error getting audio duration: {e}")
        return 0.0


# ══════════════════════════════════════════════════════════════════════
# Ambient Sound
# ══════════════════════════════════════════════════════════════════════

def get_ambient_sound() -> Optional[Path]:
    """
    Pick a random ambient background music file from the ambient directory.

    Returns:
        Path to an ambient music file, or None if none available.
    """
    ambient_dir = Path(AMBIENT_DIR)
    if not ambient_dir.exists():
        return None

    extensions = [".mp3", ".wav", ".ogg", ".m4a"]
    files = [
        f for f in ambient_dir.iterdir()
        if f.suffix.lower() in extensions
    ]

    if not files:
        logger.debug("No ambient music files found")
        return None

    selected = random.choice(files)
    logger.debug(f"Selected ambient: {selected.name}")
    return selected


def mix_audio_with_ambient(
    main_audio_path: Path,
    output_path: Path,
    total_duration: float,
    ambient_volume: float = AMBIENT_VOLUME_RATIO,
) -> Path:
    """
    Mix main audio (TTS) with ambient background music.

    Args:
        main_audio_path: Path to the main (TTS) audio file.
        output_path: Where to save the mixed output.
        total_duration: Total duration of the video in seconds.
        ambient_volume: Volume ratio for ambient music (0-1).

    Returns:
        Path to the mixed audio file.
    """
    main_audio = AudioSegment.from_file(str(main_audio_path))
    main_audio = normalize_audio(main_audio)

    ambient_path = get_ambient_sound()
    if not ambient_path:
        logger.info("No ambient music available, using TTS audio only")
        main_audio.export(str(output_path), format="mp3", bitrate="192k")
        return output_path

    ambient = AudioSegment.from_file(str(ambient_path))

    # Loop ambient to cover full duration
    target_ms = int(total_duration * 1000)
    while len(ambient) < target_ms:
        ambient = ambient + ambient

    ambient = ambient[:target_ms]

    # Adjust volumes
    ambient = ambient - (20 * (1 - ambient_volume))  # reduce ambient volume
    ambient = ambient.fade_in(AMBIENT_FADE_IN_MS).fade_out(AMBIENT_FADE_OUT_MS)

    # Overlay main audio on ambient
    mixed = ambient.overlay(main_audio)
    mixed.export(str(output_path), format="mp3", bitrate="192k")

    logger.info(f"Mixed audio exported: {output_path.name}")
    return output_path


# ══════════════════════════════════════════════════════════════════════
# Cleanup
# ══════════════════════════════════════════════════════════════════════

def cleanup_audio_files(directory: Path = None) -> int:
    """
    Clean up temporary audio files.

    Args:
        directory: Directory to clean. Defaults to AUDIO_DIR.

    Returns:
        Number of files deleted.
    """
    if directory is None:
        directory = Path(AUDIO_DIR)

    count = 0
    for f in directory.glob("_tts_*"):
        try:
            f.unlink()
            count += 1
        except Exception:
            pass

    if count > 0:
        logger.debug(f"Cleaned up {count} temporary audio files")
    return count
