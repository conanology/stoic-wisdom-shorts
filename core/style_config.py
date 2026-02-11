"""
Style Configuration - Centralized visual parameters for Stoic Wisdom Shorts
"""
from dataclasses import dataclass, field
from typing import Tuple

from config.settings import (
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    QUOTE_FONT_PATH,
    AUTHOR_FONT_PATH,
    BRANDING_FONT_PATH,
    QUOTE_COLOR,
    AUTHOR_COLOR,
    BRANDING_COLOR,
    TEXT_MAX_WIDTH,
    FONT_SIZE_CONFIG,
    AUTHOR_FONT_SIZE,
    BRANDING_FONT_SIZE,
    BRANDING_TEXT,
    QUOTE_Y_RATIO,
    AUTHOR_Y_RATIO,
    BRANDING_Y_RATIO,
    AYAH_PADDING_SECONDS,
    BACKGROUND_BRIGHTNESS,
    BACKGROUND_TINT,
    BACKGROUND_TINT_OPACITY,
    TEXT_FADE_IN_SECONDS,
    TEXT_FADE_OUT_SECONDS,
    VIDEO_FADE_SECONDS,
    KEN_BURNS_ZOOM,
    STROKE_COLOR,
    STROKE_WIDTH,
    SHADOW_COLOR,
    SHADOW_OFFSET,
    SHADOW_OPACITY,
    GLOW_RADIUS,
    GLOW_OPACITY,
    VIGNETTE_STRENGTH,
    QUOTE_MARK_SIZE,
    QUOTE_MARK_COLOR,
    QUOTE_MARK_OPACITY,
)


@dataclass
class StyleConfig:
    # Video dimensions
    video_width: int = VIDEO_WIDTH
    video_height: int = VIDEO_HEIGHT

    # Quote text
    quote_font_path: str = QUOTE_FONT_PATH
    quote_color: str = QUOTE_COLOR
    text_max_width: int = TEXT_MAX_WIDTH
    font_size_config: dict = field(default_factory=lambda: FONT_SIZE_CONFIG)

    # Author attribution
    author_font_path: str = AUTHOR_FONT_PATH
    author_color: str = AUTHOR_COLOR
    author_font_size: int = AUTHOR_FONT_SIZE
    author_y_ratio: float = AUTHOR_Y_RATIO

    # Branding
    branding_font_path: str = BRANDING_FONT_PATH
    branding_color: str = BRANDING_COLOR
    branding_font_size: int = BRANDING_FONT_SIZE
    branding_text: str = BRANDING_TEXT
    branding_y_ratio: float = BRANDING_Y_RATIO

    # Quote positioning
    quote_y_ratio: float = QUOTE_Y_RATIO

    # Stroke (text outline)
    stroke_color: str = STROKE_COLOR
    stroke_width: int = STROKE_WIDTH

    # Shadow
    shadow_color: str = SHADOW_COLOR
    shadow_offset: Tuple[int, int] = SHADOW_OFFSET
    shadow_opacity: float = SHADOW_OPACITY

    # Background grading
    background_brightness: float = BACKGROUND_BRIGHTNESS
    background_tint: Tuple[int, int, int] = BACKGROUND_TINT
    background_tint_opacity: float = BACKGROUND_TINT_OPACITY
    ken_burns_zoom: float = KEN_BURNS_ZOOM

    # Timing
    padding: float = AYAH_PADDING_SECONDS
    text_fade_in: float = TEXT_FADE_IN_SECONDS
    text_fade_out: float = TEXT_FADE_OUT_SECONDS
    video_fade: float = VIDEO_FADE_SECONDS

    # Glow effect
    glow_radius: int = GLOW_RADIUS
    glow_opacity: float = GLOW_OPACITY

    # Vignette
    vignette_strength: float = VIGNETTE_STRENGTH

    # Decorative quote marks
    quote_mark_size: int = QUOTE_MARK_SIZE
    quote_mark_color: str = QUOTE_MARK_COLOR
    quote_mark_opacity: float = QUOTE_MARK_OPACITY


# Default instance
DEFAULT_STYLE = StyleConfig()
