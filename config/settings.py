"""
Settings - Centralized configuration for Stoic Wisdom Shorts Generator

All application-wide constants: video specs, font paths, colors,
TTS settings, YouTube metadata templates, directory paths.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ══════════════════════════════════════════════════════════════════════
# Project Paths
# ══════════════════════════════════════════════════════════════════════
BASE_DIR = Path(__file__).parent.parent
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
BACKGROUNDS_DIR = ASSETS_DIR / "backgrounds"
AMBIENT_DIR = ASSETS_DIR / "ambient"
OUTPUT_DIR = BASE_DIR / "outputs"
VIDEOS_DIR = OUTPUT_DIR / "videos"
AUDIO_DIR = OUTPUT_DIR / "audio"
THUMBNAILS_DIR = OUTPUT_DIR / "thumbnails"
DATABASE_DIR = BASE_DIR / "database"

# YouTube Auth Paths
YOUTUBE_CLIENT_SECRETS = BASE_DIR / "client_secrets.json"
YOUTUBE_TOKEN_PATH = BASE_DIR / "token.json"

# Create directories
for d in [ASSETS_DIR, FONTS_DIR, BACKGROUNDS_DIR, AMBIENT_DIR,
          OUTPUT_DIR, VIDEOS_DIR, AUDIO_DIR, THUMBNAILS_DIR, DATABASE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════
# Video Specifications
# ══════════════════════════════════════════════════════════════════════
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 30
VIDEO_CODEC = "libx264"
AUDIO_CODEC = "aac"
AUDIO_BITRATE = "192k"
VIDEO_BITRATE = "4000k"

# Duration constraints (YouTube Shorts must be <60s)
MIN_DURATION = 30
MAX_DURATION = 58

# ══════════════════════════════════════════════════════════════════════
# Font Configuration
# ══════════════════════════════════════════════════════════════════════
# Primary: Playfair Display Bold (elegant serif for quotes)
# Secondary: Lato (clean sans-serif for attribution/branding)
QUOTE_FONT_PATH = str(FONTS_DIR / "PlayfairDisplay-Bold.ttf")
CINZEL_FONT_PATH = str(FONTS_DIR / "Cinzel-Bold.ttf")
AUTHOR_FONT_PATH = str(FONTS_DIR / "Lato-Italic.ttf")
BRANDING_FONT_PATH = str(FONTS_DIR / "Lato-Regular.ttf")

# Fallback if custom fonts not installed
FALLBACK_FONT = "arial.ttf"

# ══════════════════════════════════════════════════════════════════════
# Color Scheme — Dark, Premium, Cinematic
# ══════════════════════════════════════════════════════════════════════
QUOTE_COLOR = "#FFFFFF"          # pure white for maximum contrast
AUTHOR_COLOR = "#E8C547"         # vibrant gold for author name
BRANDING_COLOR = "#8899AA"       # subtle gray-blue for branding
FONT_COLOR = QUOTE_COLOR         # alias for compatibility

# Background
BACKGROUND_BRIGHTNESS = 0.45     # slightly brighter to show footage
BACKGROUND_TINT = (8, 6, 18)    # deep navy/purple tint
BACKGROUND_TINT_OPACITY = 0.30   # let more scene color through

# Text effects
STROKE_COLOR = "#000000"
STROKE_WIDTH = 3
SHADOW_COLOR = "#000000"
SHADOW_OFFSET = (3, 3)
SHADOW_OPACITY = 0.85

# Glow effect (luminous halo behind text)
GLOW_RADIUS = 12
GLOW_OPACITY = 0.35

# Vignette (dark edges spotlight)
VIGNETTE_STRENGTH = 0.6

# Decorative quotation marks
QUOTE_MARK_SIZE = 100
QUOTE_MARK_COLOR = "#D4AF37"
QUOTE_MARK_OPACITY = 0.20

# ══════════════════════════════════════════════════════════════════════
# Text Layout
# ══════════════════════════════════════════════════════════════════════
TEXT_MAX_WIDTH = int(VIDEO_WIDTH * 0.82)  # 886px

# Quote text font size by word count
FONT_SIZE_CONFIG = {
    "short":  {"max_words": 12, "font_size": 72, "words_per_line": 4},
    "medium": {"max_words": 25, "font_size": 58, "words_per_line": 5},
    "long":   {"max_words": 45, "font_size": 48, "words_per_line": 6},
    "extra":  {"max_words": 999, "font_size": 40, "words_per_line": 7},
}

# Author attribution font size
AUTHOR_FONT_SIZE = 36

# Branding text
BRANDING_FONT_SIZE = 28
BRANDING_TEXT = "Stoic Wisdom"

# Vertical positions (as ratio of VIDEO_HEIGHT)
QUOTE_Y_RATIO = 0.38          # quote centered slightly above middle
AUTHOR_Y_RATIO = 0.62         # author below quote
BRANDING_Y_RATIO = 0.92       # small branding near bottom

# ══════════════════════════════════════════════════════════════════════
# Timing & Transitions
# ══════════════════════════════════════════════════════════════════════
TEXT_FADE_IN_SECONDS = 0.8
TEXT_FADE_OUT_SECONDS = 0.6
VIDEO_FADE_SECONDS = 0.8
AYAH_PADDING_SECONDS = 0.5   # kept for compatibility, padding after TTS

# Ken Burns zoom
KEN_BURNS_ZOOM = 1.10
ENABLE_KEN_BURNS = os.getenv("ENABLE_KEN_BURNS", "true").lower() == "true"

# ══════════════════════════════════════════════════════════════════════
# TTS (Text-to-Speech) Configuration
# ══════════════════════════════════════════════════════════════════════
TTS_VOICE = os.getenv("TTS_VOICE", "en-US-GuyNeural")
TTS_RATE = os.getenv("TTS_RATE", "-5%")
TTS_PITCH = os.getenv("TTS_PITCH", "-2Hz")
TTS_INCLUDE_AUTHOR = True       # speak author name in audio

# ══════════════════════════════════════════════════════════════════════
# YouTube Metadata Templates
# ══════════════════════════════════════════════════════════════════════
CHANNEL_NAME = "Stoic Wisdom"

# Title templates — rotated for variety
TITLE_TEMPLATES = [
    "{author} Said THIS About {category}...",
    "This {author} Quote Will Change Your Life",
    "{author}'s Most Powerful Words on {category}",
    "Ancient Wisdom You Need to Hear | {author}",
    "{author} on {category} | Timeless Truth",
    "The {author} Quote Everyone Should Know",
    "Listen to {author}'s Words on {category}",
    "{category}: A Lesson From {author}",
]

DESCRIPTION_TEMPLATE = """\"{quote_text}\"

— {author_name}, {source}

━━━━━━━━━━━━━━━━━━━━
📖 About this quote:
This powerful insight from {author_name} ({era}) teaches us about {category}. 
{author_name} was a {title} known for {notable_work}.

━━━━━━━━━━━━━━━━━━━━
🏛️ Follow Stoic Wisdom for daily philosophy quotes that transform the way you think.

#StoicWisdom #{author_tag} #Philosophy #Wisdom #Motivation #Shorts #PhilosophyQuotes #{category_tag} #DailyWisdom #StoicPhilosophy #MindsetShift #PersonalGrowth
"""

DEFAULT_TAGS = [
    "stoic wisdom", "philosophy quotes", "stoicism", "motivation",
    "wisdom", "stoic", "life advice", "mindset", "self improvement",
    "philosophy", "shorts", "motivational", "ancient wisdom",
    "daily wisdom", "personal growth", "marcus aurelius", "seneca",
    "epictetus", "stoic quotes",
]

# ══════════════════════════════════════════════════════════════════════
# Database
# ══════════════════════════════════════════════════════════════════════
DATABASE_PATH = DATABASE_DIR / "stoic_wisdom.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# ══════════════════════════════════════════════════════════════════════
# Ambient Sound
# ══════════════════════════════════════════════════════════════════════
AMBIENT_VOLUME_RATIO = 0.08      # 8% volume for background music
AMBIENT_FADE_IN_MS = 2000
AMBIENT_FADE_OUT_MS = 2000

# ══════════════════════════════════════════════════════════════════════
# External Tools
# ══════════════════════════════════════════════════════════════════════
IMAGEMAGICK_BINARY = os.getenv(
    "IMAGEMAGICK_BINARY",
    r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
)
FFMPEG_PATH = os.getenv("FFMPEG_PATH", "")

# ══════════════════════════════════════════════════════════════════════
# Notifications
# ══════════════════════════════════════════════════════════════════════
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
APPROVAL_REQUIRED = os.getenv("APPROVAL_REQUIRED", "true").lower() == "true"

# ══════════════════════════════════════════════════════════════════════
# Stock Footage (Pexels)
# ══════════════════════════════════════════════════════════════════════
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

# Dark/cinematic search queries for Stoic aesthetic
STOCK_SEARCH_QUERIES = [
    "dark clouds dramatic vertical",
    "ocean storm vertical",
    "ancient ruins vertical",
    "marble statue vertical",
    "rainy window vertical",
    "fog forest dark vertical",
    "fire flames dark vertical",
    "night sky stars vertical",
    "lightning storm vertical",
    "candle flame dark vertical",
    "mountain peak clouds vertical",
    "dark water reflection vertical",
]
