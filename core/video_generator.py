"""
Video Generator - Creates Stoic Wisdom short-form videos

4-Act Pipeline:
  1. Generate multi-segment TTS audio (hook + quote + author + reflection)
  2. Load/grade a cinematic background
  3. Create time-synced text overlays for each act
  4. Mix TTS with ambient background music
  5. Composite everything and export MP4
"""
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

import numpy as np
from loguru import logger
from PIL import Image

# Pillow 10+ compatibility
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS

# Configure ImageMagick for MoviePy
from config.settings import IMAGEMAGICK_BINARY
if os.path.exists(IMAGEMAGICK_BINARY):
    os.environ["IMAGEMAGICK_BINARY"] = IMAGEMAGICK_BINARY

# Explicit imports for MoviePy v1 API with v2 file structure
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.audio.AudioClip import CompositeAudioClip, concatenate_audioclips

# Effects and Transitions
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from moviepy.video.compositing.transitions import crossfadein, crossfadeout

from config.settings import (
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    VIDEO_FPS,
    VIDEO_CODEC,
    AUDIO_CODEC,
    AUDIO_BITRATE,
    VIDEO_BITRATE,
    VIDEOS_DIR,
    AUDIO_DIR,
    MIN_DURATION,
    MAX_DURATION,
    ENABLE_KEN_BURNS,
    AMBIENT_VOLUME_RATIO,
    AMBIENT_FADE_IN_MS,
    AMBIENT_FADE_OUT_MS,
)
from core.style_config import StyleConfig, DEFAULT_STYLE
from core.background import pick_random_background, load_and_grade_background
from core.stock_footage import get_dynamic_background
from core.text_renderer import (
    create_quote_clip,
    create_author_clip,
    create_branding_clip,
    create_decorative_line,
    create_hook_clip,
    create_reflection_clip,
    create_cta_clip,
)
from core.tts_engine import TTSEngine
from core.audio_processor import get_ambient_sound, normalize_audio


class VideoGeneratorError(Exception):
    """Raised on video generation failures."""
    pass


def get_audio_duration_moviepy(path: Path) -> float:
    """Get duration of an audio file using MoviePy."""
    try:
        clip = AudioFileClip(str(path))
        dur = clip.duration
        clip.close()
        return dur
    except Exception as e:
        logger.warning(f"Could not get duration via MoviePy: {e}")
        return 0.0


def generate_stoic_short(
    quote_data: Dict[str, Any],
    output_path: Optional[Path] = None,
    style: StyleConfig = DEFAULT_STYLE,
) -> Dict[str, Any]:
    """
    Generate a complete Stoic Wisdom short-form video with 4-act structure.

    Acts:
      1. Hook Intro — philosopher name, era, title with narrator intro
      2. Main Quote — the quote text, dramatically paced
      3. Reflection — modern-day takeaway
      4. CTA — "Follow for daily wisdom"
    """
    quote_text = quote_data["quote_text"]
    author_name = quote_data["author_name"]
    author_key = quote_data["author_key"]
    quote_id = quote_data["quote_id"]
    category = quote_data.get("category", "wisdom")
    hook_text = quote_data.get("hook_intro", "")
    reflection_text = quote_data.get("reflection", "")
    philosopher_meta = quote_data.get("philosopher_meta", {})

    logger.info(
        f"Generating 4-act Stoic short for quote #{quote_id}: "
        f"\"{quote_text[:60]}...\" — {author_name}"
    )

    # ── Step 1: Generate Multi-Segment TTS Audio ─────────────────────
    logger.info("Step 1/5: Generating multi-segment TTS audio...")
    tts = TTSEngine()
    audio_path, audio_duration, timing = tts.generate_full_audio(
        hook_text=hook_text,
        quote_text=quote_text,
        author_name=author_name,
        reflection_text=reflection_text,
        output_dir=AUDIO_DIR,
        filename=f"quote_{quote_id}_tts.mp3",
    )

    # Add CTA time at the end (5 seconds after narration)
    cta_duration = 4.0
    total_duration = min(audio_duration + cta_duration, MAX_DURATION)
    # Ensure min duration is respected (loop bg/extend elements if needed)
    total_duration = max(total_duration, MIN_DURATION)

    logger.info(
        f"Audio: {audio_duration:.1f}s, Total video: {total_duration:.1f}s"
    )

    # ── Step 2: Select and Grade Background ───────────────────────────
    logger.info("Step 2/5: Loading background...")
    bg_path = get_dynamic_background()
    if bg_path is None:
        bg_path = pick_random_background()

    graded_bg = load_and_grade_background(
        path=bg_path,
        total_duration=total_duration,
        style=style,
        enable_ken_burns=ENABLE_KEN_BURNS,
    )

    # ── Step 3: Create Time-Synced Text Overlays ─────────────────────
    logger.info("Step 3/5: Creating time-synced text overlays...")

    layers = [graded_bg]
    fade_in = style.text_fade_in

    # — ACT 1: Hook intro text (philosopher name + metadata) —
    hook_start = timing["hook_start"]
    hook_end = timing["hook_end"]
    hook_visual_duration = hook_end - hook_start + 1.0  # linger a bit

    if hook_text and hook_visual_duration > 0:
        hook_clip = create_hook_clip(
            author_name=author_name,
            meta=philosopher_meta,
            duration=hook_visual_duration,
            style=style,
        )
        hook_clip = hook_clip.set_start(max(0, hook_start - 0.3))
        hook_clip = hook_clip.fx(crossfadein, fade_in)
        hook_clip = hook_clip.fx(crossfadeout, 0.5)
        layers.append(hook_clip)

    # — ACT 2: Main Quote text —
    quote_start = timing["quote_start"]
    author_end = timing["author_end"]
    
    # Ensure legal duration
    if author_end <= quote_start:
         author_end = quote_start + 3.0

    quote_visual_duration = author_end - quote_start + 1.5  # visible through author

    quote_clip = create_quote_clip(
        text=quote_text,
        duration=quote_visual_duration,
        style=style,
    )
    quote_clip = quote_clip.set_start(quote_start - 0.2)
    quote_clip = quote_clip.fx(crossfadein, fade_in)
    quote_clip = quote_clip.fx(crossfadeout, 0.8)
    layers.append(quote_clip)

    # Decorative line between quote and author
    line_clip = create_decorative_line(
        duration=quote_visual_duration,
        style=style,
    )
    line_clip = line_clip.set_start(quote_start)
    line_clip = line_clip.fx(crossfadein, fade_in + 0.3)
    line_clip = line_clip.fx(crossfadeout, 0.8)
    layers.append(line_clip)

    # Author attribution
    author_start = timing["author_start"]
    author_visual_duration = author_end - author_start + 1.5
    
    if author_visual_duration > 0:
        author_clip = create_author_clip(
            author_name=author_name,
            duration=author_visual_duration,
            style=style,
        )
        author_clip = author_clip.set_start(author_start - 0.1)
        author_clip = author_clip.fx(crossfadein, fade_in + 0.2)
        author_clip = author_clip.fx(crossfadeout, 0.8)
        layers.append(author_clip)

    # — ACT 3: Reflection text —
    reflection_start = timing["reflection_start"]
    reflection_end = timing["reflection_end"]
    reflection_visual_duration = reflection_end - reflection_start + 1.5

    if reflection_text and reflection_visual_duration > 0:
        reflection_clip = create_reflection_clip(
            text=reflection_text,
            duration=reflection_visual_duration,
            style=style,
        )
        reflection_clip = reflection_clip.set_start(reflection_start - 0.3)
        reflection_clip = reflection_clip.fx(crossfadein, fade_in)
        reflection_clip = reflection_clip.fx(crossfadeout, 0.8)
        layers.append(reflection_clip)

    # — ACT 4: CTA at the end —
    cta_start = max(reflection_end + 0.5, total_duration - cta_duration)
    cta_visual_duration = total_duration - cta_start

    if cta_visual_duration > 1.0:
        cta_clip = create_cta_clip(
            duration=cta_visual_duration,
            style=style,
        )
        cta_clip = cta_clip.set_start(cta_start)
        cta_clip = cta_clip.fx(crossfadein, fade_in)
        layers.append(cta_clip)

    # Branding at bottom (visible throughout)
    branding_clip = create_branding_clip(
        duration=total_duration,
        style=style,
    )
    branding_clip = branding_clip.set_start(0).fx(crossfadein, fade_in + 0.5)
    layers.append(branding_clip)

    # ── Step 4: Build Audio Track ─────────────────────────────────────
    logger.info("Step 4/5: Building audio track...")

    # Load TTS audio
    tts_audio = AudioFileClip(str(audio_path))

    # Try to mix with ambient background music
    try:
        ambient_path = get_ambient_sound()
        if ambient_path:
            ambient = AudioFileClip(str(ambient_path))
            # Loop ambient to cover full duration
            if ambient.duration < total_duration:
                # MoviePy v2 compatible loop (concat)
                loops_needed = int(total_duration / ambient.duration) + 1
                ambient = concatenate_audioclips([ambient] * loops_needed)
            
            # v1 API uses set_duration or subclip
            ambient = ambient.subclip(0, total_duration)
            ambient = ambient.volumex(AMBIENT_VOLUME_RATIO)

            # Combine TTS + ambient
            final_audio = CompositeAudioClip([ambient, tts_audio])
        else:
            final_audio = tts_audio
    except Exception as e:
        logger.warning(f"Ambient mixing failed, using TTS only: {e}")
        final_audio = tts_audio

    # Export audio to temp file for MoviePy
    temp_audio = AUDIO_DIR / f"quote_{quote_id}_mixed.mp3"
    final_audio.write_audiofile(
        str(temp_audio),
        fps=44100,
        nbytes=2,
        codec="libmp3lame",
        bitrate=AUDIO_BITRATE,
        logger=None,
    )

    # ── Step 5: Composite and Export ──────────────────────────────────
    logger.info("Step 5/5: Compositing and exporting video...")

    final_video = CompositeVideoClip(
        layers,
        size=(VIDEO_WIDTH, VIDEO_HEIGHT),
    ).set_duration(total_duration)

    # Apply video fade in/out
    final_video = final_video.fx(fadein, style.video_fade).fx(fadeout, style.video_fade)

    # Add mixed audio
    mixed_audio_clip = AudioFileClip(str(temp_audio))
    final_video = final_video.set_audio(mixed_audio_clip)

    # Output path
    if output_path is None:
        safe_author = author_key.replace(" ", "_")
        output_path = VIDEOS_DIR / f"stoic_{quote_id}_{safe_author}.mp4"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Export
    final_video.write_videofile(
        str(output_path),
        fps=VIDEO_FPS,
        codec=VIDEO_CODEC,
        audio_codec=AUDIO_CODEC,
        bitrate=VIDEO_BITRATE,
        preset="medium",
        threads=4,
        logger="bar",
    )

    # Cleanup
    try:
        tts_audio.close()
        mixed_audio_clip.close()
        final_video.close()
        graded_bg.close()
        temp_audio.unlink(missing_ok=True)
    except Exception:
        pass

    actual_duration = get_video_duration(output_path)

    logger.info(
        f"✅ Video generated: {output_path.name} "
        f"({actual_duration:.1f}s)"
    )

    return {
        "video_path": str(output_path),
        "duration": actual_duration,
        "quote_id": quote_id,
        "author_name": author_name,
        "author_key": author_key,
        "category": category,
        "quote_text": quote_text,
    }


def get_video_duration(path: Path) -> float:
    """Get the duration of a video file in seconds."""
    try:
        clip = VideoFileClip(str(path))
        dur = clip.duration
        clip.close()
        return dur
    except Exception:
        return 0.0
