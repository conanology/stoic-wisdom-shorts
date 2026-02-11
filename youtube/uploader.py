"""
YouTube Uploader - Upload Stoic Wisdom videos to YouTube via Data API v3
"""
import os
import random
import time
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from youtube.auth import get_authenticated_service
from config.settings import (
    TITLE_TEMPLATES,
    DESCRIPTION_TEMPLATE,
    DEFAULT_TAGS,
)


# ══════════════════════════════════════════════════════════════════════
# Metadata Generation
# ══════════════════════════════════════════════════════════════════════

def generate_metadata(
    quote_text: str,
    author_name: str,
    author_key: str,
    source: str,
    category: str,
    philosopher_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate YouTube-optimized title, description, and tags.

    Args:
        quote_text: The philosophy quote text.
        author_name: Display name of the philosopher.
        author_key: Internal key for the philosopher.
        source: Source work of the quote.
        category: Category of the quote (e.g., 'resilience').
        philosopher_meta: Full philosopher metadata dict.

    Returns:
        Dict with title, description, tags keys.
    """
    # Choose a random title template
    template = random.choice(TITLE_TEMPLATES)
    category_display = category.replace("_", " ").title()

    title = template.format(
        author=author_name,
        category=category_display,
    )
    # YouTube title max: 100 characters
    title = title[:100]

    # Build description
    meta = philosopher_meta or {}
    author_tag = author_name.replace(" ", "")
    category_tag = category_display.replace(" ", "")

    description = DESCRIPTION_TEMPLATE.format(
        quote_text=quote_text,
        author_name=author_name,
        source=source,
        era=meta.get("era", "Ancient"),
        title=meta.get("title", "Philosopher"),
        notable_work=meta.get("notable_work", source),
        category=category_display,
        author_tag=author_tag,
        category_tag=category_tag,
    )

    # Build tags
    tags = list(DEFAULT_TAGS)
    specific_tags = [
        author_name.lower(),
        f"{author_name.lower()} quotes",
        category.lower(),
        f"{category_display.lower()} quotes",
        source.lower() if source else "",
    ]
    tags.extend([t for t in specific_tags if t])
    tags = list(dict.fromkeys(tags))[:30]  # unique, max 30 tags

    return {
        "title": title,
        "description": description,
        "tags": tags,
    }


# ══════════════════════════════════════════════════════════════════════
# Upload
# ══════════════════════════════════════════════════════════════════════

def upload_video(
    video_path: Path,
    metadata: Dict[str, Any],
    privacy: str = "public",
    category_id: str = "22",  # People & Blogs
) -> Optional[str]:
    """
    Upload a video to YouTube.

    Args:
        video_path: Path to the MP4 file.
        metadata: Dict with title, description, tags.
        privacy: Privacy status (public, unlisted, private).
        category_id: YouTube category ID.

    Returns:
        YouTube video ID on success, None on failure.
    """
    youtube = get_authenticated_service()
    if youtube is None:
        logger.error("YouTube authentication failed")
        return None

    body = {
        "snippet": {
            "title": metadata["title"],
            "description": metadata["description"],
            "tags": metadata.get("tags", []),
            "categoryId": category_id,
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
            "madeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=256 * 1024,
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    video_id = _execute_with_retry(request)

    if video_id:
        url = f"https://youtube.com/shorts/{video_id}"
        logger.info(f"✅ Upload success: {url}")

    return video_id


def upload_as_private(video_path: Path, metadata: Dict[str, Any]) -> Optional[str]:
    """Upload video as private (for testing)."""
    return upload_video(video_path, metadata, privacy="private")


def _execute_with_retry(request, max_retries: int = 5) -> Optional[str]:
    """
    Execute an upload request with exponential backoff.

    Returns:
        YouTube video ID on success, None on failure.
    """
    response = None
    retry = 0

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                if progress % 25 == 0:
                    logger.info(f"Upload progress: {progress}%")
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504]:
                if retry < max_retries:
                    retry += 1
                    wait = 2 ** retry + random.random()
                    logger.warning(
                        f"Upload error {e.resp.status}, retry {retry}/{max_retries} "
                        f"in {wait:.1f}s"
                    )
                    time.sleep(wait)
                else:
                    logger.error(f"Upload failed after {max_retries} retries: {e}")
                    return None
            else:
                logger.error(f"Upload failed (HTTP {e.resp.status}): {e}")
                return None
        except Exception as e:
            logger.error(f"Upload unexpected error: {e}")
            return None

    if response:
        return response.get("id")
    return None
