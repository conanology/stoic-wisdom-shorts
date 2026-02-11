"""
Setup Assets - Download fonts, backgrounds, and ambient music for Stoic Wisdom Shorts

Usage:
    python setup_assets.py
"""
import os
import sys
import subprocess
from pathlib import Path

ASSETS_DIR = Path(__file__).parent / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
BACKGROUNDS_DIR = ASSETS_DIR / "backgrounds"
AMBIENT_DIR = ASSETS_DIR / "ambient"


def download_file(url: str, output_path: Path) -> bool:
    """Download a file from URL."""
    try:
        import requests
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"  ✅ Downloaded: {output_path.name}")
        return True
    except Exception as e:
        print(f"  ❌ Failed: {output_path.name} — {e}")
        return False


def setup_fonts():
    """Download Google Fonts: Playfair Display + Lato."""
    FONTS_DIR.mkdir(parents=True, exist_ok=True)

    fonts = {
        "PlayfairDisplay-Bold.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf",
        "Lato-Italic.ttf": "https://github.com/google/fonts/raw/main/ofl/lato/Lato-Italic.ttf",
        "Lato-Regular.ttf": "https://github.com/google/fonts/raw/main/ofl/lato/Lato-Regular.ttf",
    }

    print("\n📝 Setting up fonts...")
    for filename, url in fonts.items():
        output = FONTS_DIR / filename
        if output.exists():
            print(f"  ⏭️  Already exists: {filename}")
        else:
            download_file(url, output)


def setup_backgrounds():
    """Setup backgrounds directory with instructions."""
    BACKGROUNDS_DIR.mkdir(parents=True, exist_ok=True)

    existing = list(BACKGROUNDS_DIR.glob("*.mp4"))

    print("\n🎬 Setting up backgrounds...")
    if existing:
        print(f"  ✅ Found {len(existing)} existing background(s):")
        for v in existing:
            print(f"     - {v.name}")
    else:
        print("""  ⚠️  No background videos found yet!

  To add background videos:
  1. Go to https://www.pexels.com/videos/
  2. Search for DARK/CINEMATIC videos:
     - "dark clouds dramatic"
     - "rain window dark"
     - "fire flames dark"
     - "ancient ruins"
     - "marble statue dark"
     - "fog forest dark"
     - "night sky stars"
  3. Download 3-5 videos (720p or 1080p, portrait preferred)
  4. Save them to: assets/backgrounds/

  Tip: The system also fetches from Pexels automatically
  if you set PEXELS_API_KEY in your .env file.""")


def setup_ambient():
    """Setup ambient music directory with instructions."""
    AMBIENT_DIR.mkdir(parents=True, exist_ok=True)

    existing = list(AMBIENT_DIR.glob("*"))
    audio_exts = [".mp3", ".wav", ".ogg", ".m4a"]
    audio_files = [f for f in existing if f.suffix.lower() in audio_exts]

    print("\n🎵 Setting up ambient music...")
    if audio_files:
        print(f"  ✅ Found {len(audio_files)} ambient track(s):")
        for f in audio_files:
            print(f"     - {f.name}")
    else:
        print("""  ⚠️  No ambient music found yet!

  To add ambient background music:
  1. Find royalty-free ambient/lo-fi tracks from:
     - https://pixabay.com/music/
     - https://freesound.org/
  2. Look for: dark ambient, cinematic, atmospheric, lo-fi
  3. Download 1-3 tracks (2-5 minutes each)
  4. Save them to: assets/ambient/

  The system will randomly select and loop ambient tracks.""")


def check_dependencies():
    """Check if required system dependencies are available."""
    print("\n🔍 Checking dependencies...")

    # Python packages
    try:
        import edge_tts
        print("  ✅ edge-tts installed")
    except ImportError:
        print("  ❌ edge-tts not found. Run: pip install edge-tts")

    try:
        import moviepy
        print("  ✅ moviepy installed")
    except ImportError:
        print("  ❌ moviepy not found. Run: pip install -r requirements.txt")

    try:
        from PIL import Image
        print("  ✅ Pillow installed")
    except ImportError:
        print("  ❌ Pillow not found. Run: pip install Pillow")

    # FFmpeg
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"  ✅ FFmpeg: {version[:60]}")
        else:
            print("  ⚠️  FFmpeg found but returned error")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("  ⚠️  FFmpeg not found in PATH")


def main():
    print("=" * 55)
    print("🏛️  Stoic Wisdom Shorts Generator — Asset Setup")
    print("=" * 55)

    setup_fonts()
    setup_backgrounds()
    setup_ambient()
    check_dependencies()

    print("\n" + "=" * 55)
    print("Setup complete! Next steps:")
    print("  1. Add background videos to assets/backgrounds/")
    print("  2. Add ambient music to assets/ambient/")
    print("  3. Copy .env.example to .env and configure")
    print("  4. Run: python main.py generate")
    print("=" * 55)


if __name__ == "__main__":
    main()
