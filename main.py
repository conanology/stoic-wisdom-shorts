"""
Stoic Wisdom Shorts Generator — CLI Entry Point

Commands:
  generate    Generate a single video
  auto        Generate + upload (for automation)
  batch       Generate multiple videos
  status      Show quote progress stats
  history     Show recent upload history
  set-position Set current position in quotes database
  setup-youtube  Setup YouTube API credentials
"""
import sys
import argparse
from pathlib import Path
from loguru import logger

# Configure logging
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    level="INFO",
)
logger.add(
    "outputs/stoic_wisdom.log",
    rotation="5 MB",
    retention="7 days",
    level="DEBUG",
)


def cmd_generate(args):
    """Generate a Stoic Wisdom short video."""
    from core.quote_scheduler import get_next_quote, advance_progress, record_quote_history
    from core.video_generator import generate_stoic_short

    logger.info("🏛️  Stoic Wisdom — Generating video...")

    # Get the next quote
    quote_data = get_next_quote(
        philosopher=getattr(args, "philosopher", None),
        category=getattr(args, "category", None),
    )

    logger.info(
        f"Quote #{quote_data['quote_id']}: "
        f"\"{quote_data['quote_text'][:60]}...\" — {quote_data['author_name']}"
    )

    # Generate video
    result = generate_stoic_short(quote_data)

    # Record history
    record_quote_history(
        quote_id=quote_data["quote_id"],
        philosopher=quote_data["author_key"],
        category=quote_data["category"],
        quote_text=quote_data["quote_text"],
        video_path=result["video_path"],
        duration=result["duration"],
    )

    # Only advance progress if using sequential mode
    if not getattr(args, "philosopher", None) and not getattr(args, "category", None):
        advance_progress()

    print(f"\n✅ Video generated: {result['video_path']}")
    print(f"   Duration: {result['duration']:.1f}s")
    print(f"   Quote: \"{quote_data['quote_text'][:80]}...\"")
    print(f"   Author: {quote_data['author_name']}")


def cmd_auto(args):
    """Generate and upload automatically (for cron/GitHub Actions)."""
    from core.quote_scheduler import (
        get_next_quote, advance_progress,
        record_quote_history, update_quote_youtube_id,
    )
    from core.video_generator import generate_stoic_short
    from youtube.uploader import generate_metadata, upload_video, upload_as_private

    logger.info("🏛️  Stoic Wisdom — Auto mode (generate + upload)")

    # Generate
    quote_data = get_next_quote()
    result = generate_stoic_short(quote_data)

    record_id = record_quote_history(
        quote_id=quote_data["quote_id"],
        philosopher=quote_data["author_key"],
        category=quote_data["category"],
        quote_text=quote_data["quote_text"],
        video_path=result["video_path"],
        duration=result["duration"],
    )

    advance_progress()

    # Upload
    metadata = generate_metadata(
        quote_text=quote_data["quote_text"],
        author_name=quote_data["author_name"],
        author_key=quote_data["author_key"],
        source=quote_data.get("source", ""),
        category=quote_data.get("category", ""),
        philosopher_meta=quote_data.get("philosopher_meta"),
    )

    video_path = Path(result["video_path"])

    if getattr(args, "test", False):
        logger.info("Test mode — uploading as PRIVATE")
        youtube_id = upload_as_private(video_path, metadata)
    else:
        youtube_id = upload_video(video_path, metadata)

    if youtube_id:
        update_quote_youtube_id(record_id, youtube_id)
        url = f"https://youtube.com/shorts/{youtube_id}"
        print(f"\n✅ Uploaded: {url}")
        print(f"   Title: {metadata['title']}")

        # Telegram notification
        try:
            from notifications.telegram_bot import notify_upload_success, is_configured
            if is_configured():
                notify_upload_success(url)
        except Exception as e:
            logger.debug(f"Telegram notification skipped: {e}")
    else:
        logger.error("Upload failed")
        try:
            from notifications.telegram_bot import notify_upload_failure, is_configured
            if is_configured():
                notify_upload_failure("YouTube upload returned no video ID")
        except Exception:
            pass


def cmd_batch(args):
    """Generate multiple videos in sequence."""
    count = getattr(args, "count", 3)
    logger.info(f"🏛️  Stoic Wisdom — Batch mode: generating {count} videos")

    for i in range(count):
        logger.info(f"\n{'='*50}")
        logger.info(f"Video {i+1}/{count}")
        logger.info(f"{'='*50}")

        try:
            if getattr(args, "upload", False):
                cmd_auto(args)
            else:
                cmd_generate(args)
        except Exception as e:
            logger.error(f"Video {i+1} failed: {e}")
            continue


def cmd_status(args):
    """Show current quote progress and statistics."""
    from core.quote_scheduler import get_statistics

    stats = get_statistics()

    print("\n🏛️  Stoic Wisdom — Status")
    print("=" * 40)
    print(f"  📍 Current position: {stats['current_index']}/{stats['total_quotes']}")
    print(f"  📊 Progress: {stats['percent_complete']}%")
    print(f"  🎬 Total generated: {stats['total_generated']}")
    print(f"  ✅ Total uploaded: {stats['total_uploaded']}")

    if stats.get("philosopher_breakdown"):
        print("\n  📚 By philosopher:")
        for phil, count in sorted(
            stats["philosopher_breakdown"].items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            print(f"    {phil}: {count}")


def cmd_history(args):
    """Show recent generation/upload history."""
    from core.quote_scheduler import get_quote_history
    from core.quotes_api import get_quotes_manager

    limit = getattr(args, "limit", 10)
    history = get_quote_history(limit=limit)
    manager = get_quotes_manager()

    print(f"\n🏛️  Stoic Wisdom — Last {len(history)} Videos")
    print("=" * 60)

    for record in history:
        philosopher_name = manager.get_philosopher_name(record["philosopher"])
        status_icon = "✅" if record["status"] == "uploaded" else "🎬"
        yt_info = f" → {record['youtube_id']}" if record.get("youtube_id") else ""

        print(
            f"  {status_icon} #{record['quote_id']} | "
            f"{philosopher_name} | "
            f"{record['category']}"
            f"{yt_info}"
        )
        text = record.get("quote_text", "")
        if text:
            print(f"     \"{text[:70]}...\"")


def cmd_set_position(args):
    """Set current position in the quotes database."""
    from core.quote_scheduler import set_position

    index = args.index
    set_position(index)
    print(f"✅ Position set to index {index}")


def cmd_setup_youtube(args):
    """Setup YouTube API credentials."""
    from youtube.auth import setup_credentials
    setup_credentials()


def main():
    parser = argparse.ArgumentParser(
        description="🏛️ Stoic Wisdom Shorts Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python main.py generate                  Generate next video
  python main.py generate --philosopher seneca
  python main.py generate --category resilience
  python main.py auto                      Generate + upload
  python main.py auto --test               Generate + upload as private
  python main.py batch --count 5           Generate 5 videos
  python main.py status                    Show stats
  python main.py history                   Show recent uploads
  python main.py set-position 50           Jump to quote #50
  python main.py setup-youtube             Setup YouTube credentials
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # generate
    gen_parser = subparsers.add_parser("generate", help="Generate a video")
    gen_parser.add_argument("--philosopher", help="Filter by philosopher key")
    gen_parser.add_argument("--category", help="Filter by category")

    # auto
    auto_parser = subparsers.add_parser("auto", help="Generate + upload")
    auto_parser.add_argument("--test", action="store_true", help="Upload as private")

    # batch
    batch_parser = subparsers.add_parser("batch", help="Generate multiple videos")
    batch_parser.add_argument("--count", type=int, default=3, help="Number of videos")
    batch_parser.add_argument("--upload", action="store_true", help="Also upload each")
    batch_parser.add_argument("--test", action="store_true", help="Upload as private")

    # status
    subparsers.add_parser("status", help="Show progress stats")

    # history
    hist_parser = subparsers.add_parser("history", help="Show recent history")
    hist_parser.add_argument("--limit", type=int, default=10, help="Number of records")

    # set-position
    pos_parser = subparsers.add_parser("set-position", help="Set quote position")
    pos_parser.add_argument("index", type=int, help="Zero-based index")

    # setup-youtube
    subparsers.add_parser("setup-youtube", help="Setup YouTube credentials")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    commands = {
        "generate": cmd_generate,
        "auto": cmd_auto,
        "batch": cmd_batch,
        "status": cmd_status,
        "history": cmd_history,
        "set-position": cmd_set_position,
        "setup-youtube": cmd_setup_youtube,
    }

    try:
        commands[args.command](args)
    except KeyboardInterrupt:
        print("\n⛔ Interrupted")
    except Exception as e:
        logger.exception(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
