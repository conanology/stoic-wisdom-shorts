"""
Text Renderer - PIL-based text rendering for Stoic Wisdom Shorts

Renders English text with stroke, shadow, and optional fade effects
onto transparent canvases for MoviePy compositing.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from loguru import logger

from moviepy.editor import VideoClip

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
    FALLBACK_FONT,
)
from core.style_config import StyleConfig, DEFAULT_STYLE


# ══════════════════════════════════════════════════════════════════════
# Utility Functions
# ══════════════════════════════════════════════════════════════════════

def _hex_to_rgb(hex_color: str):
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _load_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a TrueType font with fallback to system default."""
    try:
        return ImageFont.truetype(font_path, size)
    except (OSError, IOError):
        logger.warning(f"Font not found: {font_path}, trying fallback: {FALLBACK_FONT}")
        try:
            return ImageFont.truetype(FALLBACK_FONT, size)
        except (OSError, IOError):
            logger.warning("Fallback font not found, using PIL default")
            return ImageFont.load_default()


def wrap_text(text: str, words_per_line: int) -> str:
    """Wrap text by inserting newlines every N words."""
    words = text.split()
    lines = []
    for i in range(0, len(words), words_per_line):
        lines.append(" ".join(words[i:i + words_per_line]))
    return "\n".join(lines)


def get_font_settings(word_count: int) -> dict:
    """
    Get appropriate font size and words-per-line based on word count.

    Returns:
        Dict with font_size, words_per_line keys.
    """
    for tier_name, cfg in FONT_SIZE_CONFIG.items():
        if word_count <= cfg["max_words"]:
            return {"font_size": cfg["font_size"], "words_per_line": cfg["words_per_line"]}
    # Fallback to last tier
    last = list(FONT_SIZE_CONFIG.values())[-1]
    return {"font_size": last["font_size"], "words_per_line": last["words_per_line"]}


# ══════════════════════════════════════════════════════════════════════
# PIL Text Renderer
# ══════════════════════════════════════════════════════════════════════

class PILTextRenderer:
    """Renders text to PIL images with stroke, shadow, and centering."""

    def __init__(self):
        self._cache = {}

    def render_text(
        self,
        text: str,
        font_path: str,
        font_size: int,
        color: str = "#FFFFFF",
        max_width: int = TEXT_MAX_WIDTH,
        words_per_line: int = 5,
        stroke_color: str = "#000000",
        stroke_width: int = 2,
        shadow_color: str = "#000000",
        shadow_offset: tuple = (2, 2),
        shadow_opacity: float = 0.7,
        align: str = "center",
    ) -> Image.Image:
        """
        Render text onto a transparent PIL image.

        Args:
            text: Text to render.
            font_path: Path to the .ttf font file.
            font_size: Font size in pixels.
            color: Text color as hex string.
            max_width: Maximum width for the text area.
            words_per_line: How many words before wrapping.
            stroke_color: Outline color.
            stroke_width: Outline thickness.
            shadow_color: Drop shadow color.
            shadow_offset: Shadow X, Y offset.
            shadow_opacity: Shadow opacity (0-1).
            align: Text alignment (left, center, right).

        Returns:
            RGBA PIL Image with rendered text.
        """
        # Cache key
        cache_key = (text, font_path, font_size, color, words_per_line, align)
        if cache_key in self._cache:
            return self._cache[cache_key].copy()

        font = _load_font(font_path, font_size)
        wrapped = wrap_text(text, words_per_line)

        # Measure text dimensions
        dummy = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        dummy_draw = ImageDraw.Draw(dummy)
        bbox = dummy_draw.multiline_textbbox(
            (0, 0), wrapped, font=font, align=align,
            stroke_width=stroke_width
        )
        text_w = int(bbox[2] - bbox[0] + shadow_offset[0] + 20)
        text_h = int(bbox[3] - bbox[1] + shadow_offset[1] + 20)

        # Create canvas
        canvas = Image.new("RGBA", (text_w, text_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        # Draw shadow
        if shadow_opacity > 0:
            shadow_rgba = _hex_to_rgb(shadow_color) + (int(shadow_opacity * 255),)
            shadow_layer = Image.new("RGBA", (text_w, text_h), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_layer)
            shadow_draw.multiline_text(
                (10 + shadow_offset[0], 10 + shadow_offset[1]),
                wrapped,
                font=font,
                fill=shadow_rgba,
                align=align,
            )
            canvas = Image.alpha_composite(canvas, shadow_layer)
            draw = ImageDraw.Draw(canvas)

        # Draw main text with stroke
        text_color = _hex_to_rgb(color) + (255,)
        draw.multiline_text(
            (10, 10),
            wrapped,
            font=font,
            fill=text_color,
            align=align,
            stroke_width=stroke_width,
            stroke_fill=stroke_color,
        )

        self._cache[cache_key] = canvas.copy()
        return canvas

    def clear_cache(self):
        """Clear the rendering cache."""
        self._cache.clear()


# ── Module-level renderer ────────────────────────────────────────────

_renderer = PILTextRenderer()


# ══════════════════════════════════════════════════════════════════════
# Frame Helper
# ══════════════════════════════════════════════════════════════════════

def _make_centered_frame(
    text_img: Image.Image,
    canvas_w: int = VIDEO_WIDTH,
    canvas_h: int = VIDEO_HEIGHT,
    y_center: int = None,
    max_scale_w: float = 0.9,
) -> np.ndarray:
    """
    Place a rendered text image centered on a full-size transparent canvas.

    Args:
        text_img: RGBA PIL Image of rendered text.
        canvas_w: Width of the output canvas.
        canvas_h: Height of the output canvas.
        y_center: Y position for the center of the text. If None, centers vertically.
        max_scale_w: Maximum width as fraction of canvas_w.

    Returns:
        RGBA numpy array (H, W, 4).
    """
    tw, th = text_img.size
    max_w = int(canvas_w * max_scale_w)

    # Scale down if too wide
    if tw > max_w:
        ratio = max_w / tw
        new_w = max_w
        new_h = int(th * ratio)
        text_img = text_img.resize((new_w, new_h), Image.LANCZOS)
        tw, th = new_w, new_h

    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

    x = (canvas_w - tw) // 2
    if y_center is not None:
        y = y_center - (th // 2)
    else:
        y = (canvas_h - th) // 2

    y = max(0, min(y, canvas_h - th))
    canvas.paste(text_img, (x, y), text_img)

    return np.array(canvas)


# ══════════════════════════════════════════════════════════════════════
# Clip Generators (for MoviePy compositing)
# ══════════════════════════════════════════════════════════════════════

def create_pil_text_clip(
    frame_rgba: np.ndarray,
    duration: float,
) -> VideoClip:
    """
    Create a MoviePy VideoClip from a pre-rendered RGBA numpy array.

    Args:
        frame_rgba: RGBA numpy array (H, W, 4).
        duration: Clip duration in seconds.

    Returns:
        MoviePy VideoClip with alpha mask.
    """
    rgb = frame_rgba[:, :, :3]
    alpha = frame_rgba[:, :, 3] / 255.0

    clip = VideoClip(lambda t: rgb, ismask=False, duration=duration)
    mask = VideoClip(lambda t: alpha, ismask=True, duration=duration)
    clip = clip.set_mask(mask)

    return clip


def create_quote_clip(
    text: str,
    duration: float,
    style: StyleConfig = DEFAULT_STYLE,
) -> VideoClip:
    """
    Create a centered quote text clip.

    Args:
        text: Quote text to display.
        duration: How long the clip should last.
        style: Visual style configuration.

    Returns:
        MoviePy VideoClip positioned at quote_y_ratio.
    """
    word_count = len(text.split())
    settings = get_font_settings(word_count)

    text_img = _renderer.render_text(
        text=text,
        font_path=style.quote_font_path,
        font_size=settings["font_size"],
        color=style.quote_color,
        max_width=style.text_max_width,
        words_per_line=settings["words_per_line"],
        stroke_color=style.stroke_color,
        stroke_width=style.stroke_width,
        shadow_color=style.shadow_color,
        shadow_offset=style.shadow_offset,
        shadow_opacity=style.shadow_opacity,
        align="center",
    )

    y_center = int(style.video_height * style.quote_y_ratio)
    frame = _make_centered_frame(text_img, y_center=y_center)

    return create_pil_text_clip(frame, duration)


def create_author_clip(
    author_name: str,
    duration: float,
    style: StyleConfig = DEFAULT_STYLE,
) -> VideoClip:
    """
    Create an author attribution clip (e.g., "— Marcus Aurelius").

    Args:
        author_name: Philosopher name.
        duration: How long the clip should last.
        style: Visual style configuration.

    Returns:
        MoviePy VideoClip positioned at author_y_ratio.
    """
    display_text = f"— {author_name}"

    text_img = _renderer.render_text(
        text=display_text,
        font_path=style.author_font_path,
        font_size=style.author_font_size,
        color=style.author_color,
        max_width=style.text_max_width,
        words_per_line=20,  # keep on one line
        stroke_color=style.stroke_color,
        stroke_width=1,
        shadow_color=style.shadow_color,
        shadow_offset=(1, 1),
        shadow_opacity=0.5,
        align="center",
    )

    y_center = int(style.video_height * style.author_y_ratio)
    frame = _make_centered_frame(text_img, y_center=y_center)

    return create_pil_text_clip(frame, duration)


def create_branding_clip(
    duration: float,
    style: StyleConfig = DEFAULT_STYLE,
) -> VideoClip:
    """
    Create a small branding text clip at the bottom of the video.

    Args:
        duration: How long the clip should last.
        style: Visual style configuration.

    Returns:
        MoviePy VideoClip positioned at branding_y_ratio.
    """
    text_img = _renderer.render_text(
        text=style.branding_text,
        font_path=style.branding_font_path,
        font_size=style.branding_font_size,
        color=style.branding_color,
        max_width=style.text_max_width,
        words_per_line=20,
        stroke_color=style.stroke_color,
        stroke_width=1,
        shadow_color=style.shadow_color,
        shadow_offset=(1, 1),
        shadow_opacity=0.4,
        align="center",
    )

    y_center = int(style.video_height * style.branding_y_ratio)
    frame = _make_centered_frame(text_img, y_center=y_center)

    return create_pil_text_clip(frame, duration)


def create_decorative_line(
    duration: float,
    y_center: int = None,
    width: int = 200,
    color: str = "#D4AF37",
    style: StyleConfig = DEFAULT_STYLE,
) -> VideoClip:
    """
    Create a thin decorative horizontal line (separator between quote and author).

    Args:
        duration: Clip duration.
        y_center: Vertical center position. Defaults to between quote and author.
        width: Line width in pixels.
        color: Line color as hex string.
        style: Visual style configuration.

    Returns:
        MoviePy VideoClip.
    """
    canvas = Image.new("RGBA", (style.video_width, style.video_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    if y_center is None:
        y_center = int(style.video_height * (style.quote_y_ratio + style.author_y_ratio) / 2)

    line_color = _hex_to_rgb(color) + (180,)  # slightly transparent
    x_start = (style.video_width - width) // 2
    x_end = x_start + width

    draw.line([(x_start, y_center), (x_end, y_center)], fill=line_color, width=2)

    frame = np.array(canvas)
    return create_pil_text_clip(frame, duration)


def create_hook_clip(
    author_name: str,
    meta: dict,
    duration: float,
    style: StyleConfig = DEFAULT_STYLE,
) -> VideoClip:
    """
    Create a hook intro clip showing philosopher identity.

    Displays:
      PHILOSOPHER NAME
      Era • Title

    Args:
        author_name: Display name of the philosopher.
        meta: Philosopher metadata dict (era, title).
        duration: Clip duration in seconds.
        style: Visual style configuration.

    Returns:
        MoviePy VideoClip positioned in upper-center area.
    """
    # Name line
    name_img = _renderer.render_text(
        text=author_name.upper(),
        font_path=style.quote_font_path,
        font_size=42,
        color=style.quote_color,
        max_width=style.text_max_width,
        words_per_line=10,
        stroke_color=style.stroke_color,
        stroke_width=2,
        shadow_color=style.shadow_color,
        shadow_offset=(2, 2),
        shadow_opacity=0.6,
        align="center",
    )

    # Subtitle line (era + title)
    subtitle_parts = []
    if meta and meta.get("era"):
        subtitle_parts.append(meta["era"])
    if meta and meta.get("title"):
        subtitle_parts.append(meta["title"])
    subtitle_text = " • ".join(subtitle_parts) if subtitle_parts else ""

    if subtitle_text:
        subtitle_img = _renderer.render_text(
            text=subtitle_text,
            font_path=style.author_font_path,
            font_size=28,
            color=style.author_color,
            max_width=style.text_max_width,
            words_per_line=20,
            stroke_color=style.stroke_color,
            stroke_width=1,
            shadow_color=style.shadow_color,
            shadow_offset=(1, 1),
            shadow_opacity=0.4,
            align="center",
        )

        # Combine name + subtitle vertically
        gap = 15
        combined_w = max(name_img.width, subtitle_img.width)
        combined_h = name_img.height + gap + subtitle_img.height
        combined = Image.new("RGBA", (combined_w, combined_h), (0, 0, 0, 0))
        combined.paste(name_img, ((combined_w - name_img.width) // 2, 0), name_img)
        combined.paste(subtitle_img, ((combined_w - subtitle_img.width) // 2, name_img.height + gap), subtitle_img)
    else:
        combined = name_img

    y_center = int(style.video_height * 0.35)
    frame = _make_centered_frame(combined, y_center=y_center)

    return create_pil_text_clip(frame, duration)


def create_reflection_clip(
    text: str,
    duration: float,
    style: StyleConfig = DEFAULT_STYLE,
) -> VideoClip:
    """
    Create a reflection text clip (italic, slightly smaller than quote).

    Args:
        text: Reflection text to display.
        duration: Clip duration in seconds.
        style: Visual style configuration.

    Returns:
        MoviePy VideoClip.
    """
    text_img = _renderer.render_text(
        text=text,
        font_path=style.author_font_path,  # Lato italic for reflections
        font_size=36,
        color="#C8C8D0",  # slightly muted white
        max_width=style.text_max_width,
        words_per_line=6,
        stroke_color=style.stroke_color,
        stroke_width=1,
        shadow_color=style.shadow_color,
        shadow_offset=(1, 1),
        shadow_opacity=0.5,
        align="center",
    )

    y_center = int(style.video_height * 0.45)
    frame = _make_centered_frame(text_img, y_center=y_center)

    return create_pil_text_clip(frame, duration)


def create_cta_clip(
    duration: float,
    cta_text: str = "Follow for daily wisdom",
    style: StyleConfig = DEFAULT_STYLE,
) -> VideoClip:
    """
    Create a call-to-action clip at the bottom.

    Args:
        duration: Clip duration in seconds.
        cta_text: CTA message.
        style: Visual style configuration.

    Returns:
        MoviePy VideoClip.
    """
    # CTA text
    cta_img = _renderer.render_text(
        text=cta_text,
        font_path=style.branding_font_path,
        font_size=32,
        color="#D4AF37",  # gold accent
        max_width=style.text_max_width,
        words_per_line=20,
        stroke_color=style.stroke_color,
        stroke_width=1,
        shadow_color=style.shadow_color,
        shadow_offset=(1, 1),
        shadow_opacity=0.4,
        align="center",
    )

    y_center = int(style.video_height * 0.88)
    frame = _make_centered_frame(cta_img, y_center=y_center)

    return create_pil_text_clip(frame, duration)
