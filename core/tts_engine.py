"""
TTS Engine - Text-to-Speech generation using ElevenLabs API

Uses ElevenLabs' neural voices for high-quality, cinematic narration.
Free tier: ~10,000 characters/month (~60-200 short quotes).
"""
import os
from pathlib import Path
from typing import Tuple

from loguru import logger
from pydub import AudioSegment

try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import VoiceSettings
except ImportError:
    ElevenLabs = None
    VoiceSettings = None
    logger.warning(
        "elevenlabs not installed. Run: pip install elevenlabs"
    )


# ── Default settings from environment ─────────────────────────────────

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

# Voice IDs — browse at https://elevenlabs.io/voice-library
# Henry (documentary, calm, thoughtful): 991lF4hc0xxfec4Y6B0i
# Adam (warm, deep): pNInz6obpgDQGcFmaJgB
# Drew (deep, soothing): 29vD33N1CtxCmqQRPOHJ
DEFAULT_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "991lF4hc0xxfec4Y6B0i")
DEFAULT_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")

# Voice tuning
DEFAULT_STABILITY = float(os.getenv("ELEVENLABS_STABILITY", "0.75"))
DEFAULT_SIMILARITY = float(os.getenv("ELEVENLABS_SIMILARITY", "0.85"))
DEFAULT_STYLE = float(os.getenv("ELEVENLABS_STYLE", "0.35"))


class TTSError(Exception):
    """Raised on TTS generation failures."""
    pass


class TTSEngine:
    """
    Generates speech audio from text using ElevenLabs API.
    High-quality neural voices with fine-tuned stability/style controls.
    """

    def __init__(
        self,
        api_key: str = ELEVENLABS_API_KEY,
        voice_id: str = DEFAULT_VOICE_ID,
        model: str = DEFAULT_MODEL,
        stability: float = DEFAULT_STABILITY,
        similarity: float = DEFAULT_SIMILARITY,
        style: float = DEFAULT_STYLE,
    ):
        if ElevenLabs is None:
            raise TTSError(
                "elevenlabs is not installed. Install with: pip install elevenlabs"
            )

        if not api_key:
            raise TTSError(
                "ELEVENLABS_API_KEY not set. Get a free key at https://elevenlabs.io"
            )

        self.client = ElevenLabs(api_key=api_key)
        self.voice_id = voice_id
        self.model = model
        self.voice_settings = VoiceSettings(
            stability=stability,
            similarity_boost=similarity,
            style=style,
            use_speaker_boost=True,
        )
        self.voice = voice_id  # for backward compat with sanity test

        logger.debug(
            f"ElevenLabs TTS initialized: voice_id={voice_id}, "
            f"model={model}, stability={stability}, similarity={similarity}"
        )

    # ── Core Generation ───────────────────────────────────────────────

    def generate_speech(
        self,
        text: str,
        output_path: Path,
    ) -> Path:
        """
        Generate speech audio from text.

        Args:
            text: Text to speak.
            output_path: Where to save the MP3 file.

        Returns:
            Path to the generated audio file.

        Raises:
            TTSError: If generation fails.
        """
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Call ElevenLabs API
            audio_generator = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=text,
                model_id=self.model,
                voice_settings=self.voice_settings,
                output_format="mp3_44100_128",
            )

            # Write audio bytes to file
            with open(output_path, "wb") as f:
                for chunk in audio_generator:
                    f.write(chunk)

            if not output_path.exists() or output_path.stat().st_size == 0:
                raise TTSError(f"TTS output file is empty or missing: {output_path}")

            logger.info(f"Generated TTS audio: {output_path.name} ({len(text)} chars)")
            return output_path

        except TTSError:
            raise
        except Exception as e:
            raise TTSError(f"ElevenLabs TTS generation failed: {e}") from e

    # ── Multi-Segment Generation ────────────────────────────────────────

    def generate_full_audio(
        self,
        hook_text: str,
        quote_text: str,
        author_name: str,
        reflection_text: str,
        output_dir: Path,
        filename: str = "quote_tts.mp3",
    ) -> Tuple[Path, float, dict]:
        """
        Generate complete 4-act audio narration.

        Audio structure:
          [silence 500ms]
          [ACT 1: hook intro]
          [pause 1200ms]
          [ACT 2: quote narration]
          [pause 800ms]
          [author name]
          [pause 1500ms]
          [ACT 3: reflection]
          [silence 800ms]

        Args:
            hook_text: Narrator intro text.
            quote_text: The quote to speak.
            author_name: Philosopher name.
            reflection_text: Modern reflection text.
            output_dir: Directory for output files.
            filename: Output filename.

        Returns:
            Tuple of (output_path, duration_seconds, timing_dict).
            timing_dict contains start/end timestamps for each segment.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        temp_files = []

        # ── Generate each segment ──────────────────────────────────────
        # Hook intro
        hook_path = output_dir / "_tts_hook.mp3"
        self.generate_speech(hook_text, hook_path)
        hook_audio = AudioSegment.from_file(str(hook_path))
        temp_files.append(hook_path)

        # Quote
        quote_path = output_dir / "_tts_quote.mp3"
        self.generate_speech(quote_text, quote_path)
        quote_audio = AudioSegment.from_file(str(quote_path))
        temp_files.append(quote_path)

        # Author
        author_path = output_dir / "_tts_author.mp3"
        self.generate_speech(author_name, author_path)
        author_audio = AudioSegment.from_file(str(author_path))
        temp_files.append(author_path)

        # Reflection
        reflection_path = output_dir / "_tts_reflection.mp3"
        self.generate_speech(reflection_text, reflection_path)
        reflection_audio = AudioSegment.from_file(str(reflection_path))
        temp_files.append(reflection_path)

        # ── Compose with pauses ────────────────────────────────────────
        intro_silence = AudioSegment.silent(duration=500)
        pause_after_hook = AudioSegment.silent(duration=1200)
        pause_after_quote = AudioSegment.silent(duration=800)
        pause_after_author = AudioSegment.silent(duration=1500)
        outro_silence = AudioSegment.silent(duration=800)

        # Build timeline and track positions
        cursor_ms = 0
        segments = []

        # Intro silence
        segments.append(intro_silence)
        cursor_ms += 500

        # Hook
        hook_start = cursor_ms
        segments.append(hook_audio)
        cursor_ms += len(hook_audio)
        hook_end = cursor_ms

        # Pause
        segments.append(pause_after_hook)
        cursor_ms += 1200

        # Quote
        quote_start = cursor_ms
        segments.append(quote_audio)
        cursor_ms += len(quote_audio)
        quote_end = cursor_ms

        # Pause
        segments.append(pause_after_quote)
        cursor_ms += 800

        # Author
        author_start = cursor_ms
        segments.append(author_audio)
        cursor_ms += len(author_audio)
        author_end = cursor_ms

        # Pause
        segments.append(pause_after_author)
        cursor_ms += 1500

        # Reflection
        reflection_start = cursor_ms
        segments.append(reflection_audio)
        cursor_ms += len(reflection_audio)
        reflection_end = cursor_ms

        # Outro
        segments.append(outro_silence)
        cursor_ms += 800

        # Combine all
        full_audio = segments[0]
        for seg in segments[1:]:
            full_audio = full_audio + seg

        # Cleanup temp files
        for f in temp_files:
            f.unlink(missing_ok=True)

        # Export final
        output_path = output_dir / filename
        full_audio.export(str(output_path), format="mp3", bitrate="192k")

        duration_seconds = len(full_audio) / 1000.0

        timing = {
            "hook_start": hook_start / 1000.0,
            "hook_end": hook_end / 1000.0,
            "quote_start": quote_start / 1000.0,
            "quote_end": quote_end / 1000.0,
            "author_start": author_start / 1000.0,
            "author_end": author_end / 1000.0,
            "reflection_start": reflection_start / 1000.0,
            "reflection_end": reflection_end / 1000.0,
            "total_duration": duration_seconds,
        }

        logger.info(
            f"Generated full narration: {duration_seconds:.1f}s — "
            f"hook={timing['hook_start']:.1f}-{timing['hook_end']:.1f}s, "
            f"quote={timing['quote_start']:.1f}-{timing['quote_end']:.1f}s, "
            f"author={timing['author_start']:.1f}-{timing['author_end']:.1f}s, "
            f"reflection={timing['reflection_start']:.1f}-{timing['reflection_end']:.1f}s"
        )

        return output_path, duration_seconds, timing

    # ── Legacy wrapper ────────────────────────────────────────────────

    def generate_quote_audio(
        self,
        quote_text: str,
        author_name: str,
        output_dir: Path,
        filename: str = "quote_tts.mp3",
        **kwargs,
    ) -> Tuple[Path, float]:
        """Legacy wrapper — returns (path, duration) without timing."""
        path, dur, _ = self.generate_full_audio(
            hook_text="",
            quote_text=quote_text,
            author_name=author_name,
            reflection_text="",
            output_dir=output_dir,
            filename=filename,
        )
        return path, dur

    # ── Utility ───────────────────────────────────────────────────────

    @staticmethod
    def get_audio_duration(audio_path: Path) -> float:
        """Get duration of an audio file in seconds."""
        audio = AudioSegment.from_file(str(audio_path))
        return len(audio) / 1000.0
