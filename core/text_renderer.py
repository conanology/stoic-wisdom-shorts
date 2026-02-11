"""
Text Renderer - PIL-based text rendering for Stoic Wisdom Shorts

Renders English text with stroke, shadow, glow, and premium effects
onto transparent canvases for MoviePy compositing.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from loguru import logger

from moviepy.editor import VideoClip

from config.settings import (
    VIDEO_WIDTH,
    VIDEO_HEIGHT,
    QUOTE_FONT_PATH,
    CINZEL_FONT_PATH,
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
        logger.warning(
            f"Font not found: {font_path}, falling back to {FALLBACK_FONT}"
        )
        try:
            return ImageFont.truetype(FALLBACK_FONT, size)
        except (OSError, IOError):
            logger.warning("Fallback font not found, using PIL default")
            return ImageFont.load_default()


def _add_glow(img: Image.Image, radius: int = 12, opacity: float = 0.35) -> Image.Image:
    """
    Add a cinematic glow effect behind a rendered text image.

    Creates a gaussian-blurred copy of the image composited behind the
    original, producing a soft luminous halo.

    Args:
        img: RGBA PIL Image with rendered text.
        radius: Gaussian blur radius (higher = more diffuse glow).
        opacity: Glow layer opacity (0-1).

    Returns:
        RGBA PIL Image with glow applied.
    """
    # Create the glow layer by blurring the original
    glow = img.copy()
    glow = glow.filter(ImageFilter.GaussianBlur(radius=radius))

    # Reduce glow opacity
    r, g, b, a = glow.split()
    a = a.point(lambda x: int(x * opacity))
    glow = Image.merge("RGBA", (r, g, b, a))

    # Composite: glow behind original
    result = Image.new("RGBA", img.size, (0, 0, 0, 0))
    result = Image.alpha_composite(result, glow)
    result = Image.alpha_composite(result, img)
    return result


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
        stroke_width: int = 3,
        shadow_color: str = "#000000",
        shadow_offset: tuple = (3, 3),
        shadow_opacity: float = 0.85,
        align: str = "center",
        enable_glow: bool = True,
        glow_radius: int = 12,
        glow_opacity: float = 0.35,
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
        cache_key = (text, font_path, font_size, color, words_per_line, align, enable_glow)
        if cache_key in self._cache:
            return self._cache[cache_key].copy()

        font = _load_font(font_path, font_size)
        wrapped = wrap_text(text, words_per_line)

        # Measure text dimensions — add extra padding for glow bleed
        glow_pad = 30 if enable_glow else 0
        dummy = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        dummy_draw = ImageDraw.Draw(dummy)
        bbox = dummy_draw.multiline_textbbox(
            (0, 0), wrapped, font=font, align=align,
            stroke_width=stroke_width
        )
        text_w = int(bbox[2] - bbox[0] + shadow_offset[0] + 20 + glow_pad * 2)
        text_h = int(bbox[3] - bbox[1] + shadow_offset[1] + 20 + glow_pad * 2)

        # Create canvas
        pad = 10 + glow_pad
        canvas = Image.new("RGBA", (text_w, text_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)

        # Draw shadow
        if shadow_opacity > 0:
            shadow_rgba = _hex_to_rgb(shadow_color) + (int(shadow_opacity * 255),)
            shadow_layer = Image.new("RGBA", (text_w, text_h), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_layer)
            shadow_draw.multiline_text(
                (pad + shadow_offset[0], pad + shadow_offset[1]),
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
            (pad, pad),
            wrapped,
            font=font,
            fill=text_color,
            align=align,
            stroke_width=stroke_width,
            stroke_fill=stroke_color,
        )

        # Apply glow effect
        if enable_glow:
            canvas = _add_glow(canvas, radius=glow_radius, opacity=glow_opacity)

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
        enable_glow=True,
        glow_radius=style.glow_radius,
        glow_opacity=style.glow_opacity,
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
    width: int = 260,
    color: str = "#D4AF37",
    style: StyleConfig = DEFAULT_STYLE,
) -> VideoClip:
    """
    Create an ornamental divider: ◆ ── ✦ ── ◆

    Args:
        duration: Clip duration.
        y_center: Vertical center position. Defaults to between quote and author.
        width: Total ornament width in pixels.
        color: Ornament color as hex string.
        style: Visual style configuration.

    Returns:
        MoviePy VideoClip.
    """
    canvas = Image.new("RGBA", (style.video_width, style.video_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    if y_center is None:
        y_center = int(style.video_height * (style.quote_y_ratio + style.author_y_ratio) / 2)

    ornament_color = _hex_to_rgb(color) + (200,)
    line_color = _hex_to_rgb(color) + (120,)  # softer lines
    cx = style.video_width // 2

    # Center diamond ✦
    d = 6  # diamond half-size
    draw.polygon(
        [(cx, y_center - d), (cx + d, y_center), (cx, y_center + d), (cx - d, y_center)],
        fill=ornament_color,
    )

    # Lines extending from center diamond
    line_gap = 14
    line_half = width // 2 - line_gap
    draw.line([(cx + line_gap, y_center), (cx + line_half, y_center)], fill=line_color, width=2)
    draw.line([(cx - line_gap, y_center), (cx - line_half, y_center)], fill=line_color, width=2)

    # End diamonds ◆
    for ex in [cx - line_half, cx + line_half]:
        sd = 4  # smaller end diamonds
        draw.polygon(
            [(ex, y_center - sd), (ex + sd, y_center), (ex, y_center + sd), (ex - sd, y_center)],
            fill=ornament_color,
        )

    # Apply glow to the ornament
    canvas = _add_glow(canvas, radius=8, opacity=0.5)

    frame = np.array(canvas)
    return create_pil_text_clip(frame, duration)


def create_vignette_overlay(
    duration: float,
    style: StyleConfig = DEFAULT_STYLE,
) -> VideoClip:
    """
    Create a radial vignette overlay (dark edges, transparent center).

    Draws viewer attention to the center of the frame where text appears.

    Args:
        duration: Clip duration.
        style: Visual style configuration.

    Returns:
        MoviePy VideoClip with vignette effect.
    """
    w, h = style.video_width, style.video_height
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    # Create radial gradient using distance from center
    cx, cy = w / 2, h / 2
    max_dist = (cx ** 2 + cy ** 2) ** 0.5

    # Build alpha channel for vignette
    alpha = np.zeros((h, w), dtype=np.uint8)
    y_coords, x_coords = np.mgrid[0:h, 0:w]
    dist = np.sqrt((x_coords - cx) ** 2 + (y_coords - cy) ** 2)
    # Normalize to 0-1 range
    norm_dist = dist / max_dist
    # Apply power curve for smooth vignette (more transparent in center)
    vignette_alpha = np.clip(norm_dist ** 1.8 * style.vignette_strength * 255, 0, 255).astype(np.uint8)

    # Black overlay with radial alpha
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[:, :, 3] = vignette_alpha  # only alpha channel, RGB stays black

    frame = rgba
    return create_pil_text_clip(frame, duration)


def create_decorative_quote_marks(
    duration: float,
    style: StyleConfig = DEFAULT_STYLE,
) -> VideoClip:
    """
    Create large decorative quotation marks framing the quote area.

    Renders opening " near top-left and closing " near bottom-right
    of the quote region in gold at low opacity.

    Args:
        duration: Clip duration.
        style: Visual style configuration.

    Returns:
        MoviePy VideoClip with quotation marks.
    """
    canvas = Image.new("RGBA", (style.video_width, style.video_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    mark_font = _load_font(style.quote_font_path, style.quote_mark_size)
    mark_color = _hex_to_rgb(style.quote_mark_color) + (int(style.quote_mark_opacity * 255),)

    # Opening quote mark " — top-left of quote area
    open_x = int(style.video_width * 0.08)
    open_y = int(style.video_height * style.quote_y_ratio - style.quote_mark_size * 1.2)
    draw.text((open_x, open_y), "\u201C", font=mark_font, fill=mark_color)

    # Closing quote mark " — bottom-right of quote area
    close_x = int(style.video_width * 0.82)
    close_y = int(style.video_height * style.quote_y_ratio + style.quote_mark_size * 0.3)
    draw.text((close_x, close_y), "\u201D", font=mark_font, fill=mark_color)

    # Apply soft glow to the marks
    canvas = _add_glow(canvas, radius=10, opacity=0.6)

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
    # Name line — larger, with letter spacing feel via spaced chars
    spaced_name = "  ".join(author_name.upper())
    name_img = _renderer.render_text(
        text=spaced_name,
        font_path=CINZEL_FONT_PATH,
        font_size=38,
        color=style.quote_color,
        max_width=style.text_max_width,
        words_per_line=50,  # keep on one line
        stroke_color=style.stroke_color,
        stroke_width=style.stroke_width,
        shadow_color=style.shadow_color,
        shadow_offset=style.shadow_offset,
        shadow_opacity=0.7,
        align="center",
        enable_glow=True,
        glow_radius=style.glow_radius,
        glow_opacity=style.glow_opacity,
    )

    # Golden horizontal rules above and below name
    rule_width = min(name_img.width - 40, 350)
    rule_color = _hex_to_rgb(style.author_color) + (140,)
    rule_height = 2

    # Subtitle line (era + title)
    subtitle_parts = []
    if meta and meta.get("era"):
        subtitle_parts.append(meta["era"])
    if meta and meta.get("title"):
        subtitle_parts.append(meta["title"])
    subtitle_text = " \u2022 ".join(subtitle_parts) if subtitle_parts else ""

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
            shadow_opacity=0.5,
            align="center",
            enable_glow=True,
            glow_radius=8,
            glow_opacity=0.25,
        )

        # Combine: rule + name + rule + subtitle
        gap = 12
        combined_w = max(name_img.width, subtitle_img.width, rule_width + 60)
        combined_h = rule_height + gap + name_img.height + gap + rule_height + gap + subtitle_img.height
        combined = Image.new("RGBA", (combined_w, combined_h), (0, 0, 0, 0))
        combined_draw = ImageDraw.Draw(combined)

        # Top rule
        rx = (combined_w - rule_width) // 2
        ry = 0
        combined_draw.line([(rx, ry), (rx + rule_width, ry)], fill=rule_color, width=rule_height)

        # Name
        ny = ry + rule_height + gap
        combined.paste(name_img, ((combined_w - name_img.width) // 2, ny), name_img)

        # Bottom rule
        ry2 = ny + name_img.height + gap
        combined_draw.line([(rx, ry2), (rx + rule_width, ry2)], fill=rule_color, width=rule_height)

        # Subtitle
        sy = ry2 + rule_height + gap
        combined.paste(subtitle_img, ((combined_w - subtitle_img.width) // 2, sy), subtitle_img)
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
