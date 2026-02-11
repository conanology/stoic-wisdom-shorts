"""
Quote Scheduler - Manages sequential progress through the quotes database.
Replaces verse_scheduler.py for Stoic Wisdom content.
"""
import random
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger

from database.models import (
    get_db_session,
    QuoteProgress,
    QuoteHistory,
    init_database,
)
from core.quotes_api import get_quotes_manager


class QuoteSchedulerError(Exception):
    """Raised on scheduler logic errors."""
    pass


# Ensure the database is initialized
init_database()


def get_current_progress() -> Dict[str, Any]:
    """
    Get the current position in the quotes database.

    Returns:
        Dict with current_index, total_quotes, percent_complete
    """
    manager = get_quotes_manager()
    total = manager.get_total_quotes()

    session = get_db_session()
    try:
        progress = session.query(QuoteProgress).first()
        if progress:
            current = progress.current_index
        else:
            current = 0
    finally:
        session.close()

    percent = (current / total * 100) if total > 0 else 0

    return {
        "current_index": current,
        "total_quotes": total,
        "percent_complete": round(percent, 1),
    }


def get_next_quote(
    philosopher: Optional[str] = None,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get the next quote to generate a video for.

    If philosopher or category is specified, picks a random matching quote.
    Otherwise, returns the next sequential quote.

    Args:
        philosopher: Optional philosopher key to filter by.
        category: Optional category to filter by.

    Returns:
        Quote dict formatted for video (via QuotesManager.format_for_video).
    """
    manager = get_quotes_manager()

    if philosopher or category:
        # Filtered random selection
        raw_quote = manager.get_random_quote(
            philosopher=philosopher, category=category
        )
        logger.info(
            f"Selected filtered quote #{raw_quote['id']} "
            f"by {manager.get_philosopher_name(raw_quote['author'])}"
        )
        return manager.format_for_video(raw_quote)

    # Sequential mode
    session = get_db_session()
    try:
        progress = session.query(QuoteProgress).first()
        if progress:
            current_index = progress.current_index
        else:
            current_index = 0
            progress = QuoteProgress(current_index=0, total_quotes=manager.get_total_quotes())
            session.add(progress)
            session.commit()
    finally:
        session.close()

    # Wrap around if we've reached the end
    total = manager.get_total_quotes()
    if current_index >= total:
        current_index = 0
        logger.info("Reached end of quotes database, wrapping to beginning")

    raw_quote = manager.get_quote_by_index(current_index)
    if raw_quote is None:
        raise QuoteSchedulerError(
            f"No quote found at index {current_index}. Database may be empty."
        )

    logger.info(
        f"Next quote #{raw_quote['id']} (index {current_index}/{total}): "
        f"\"{raw_quote['text'][:50]}...\" — {manager.get_philosopher_name(raw_quote['author'])}"
    )

    return manager.format_for_video(raw_quote)


def advance_progress() -> int:
    """
    Move to the next quote in the sequence.

    Returns:
        The new current index.
    """
    manager = get_quotes_manager()
    total = manager.get_total_quotes()

    session = get_db_session()
    try:
        progress = session.query(QuoteProgress).first()
        if progress:
            progress.current_index += 1
            if progress.current_index >= total:
                progress.current_index = 0
                logger.info("Quote database complete! Wrapping to beginning.")
            progress.last_updated = datetime.utcnow()
        else:
            progress = QuoteProgress(current_index=1, total_quotes=total)
            session.add(progress)

        session.commit()
        new_index = progress.current_index
    finally:
        session.close()

    logger.debug(f"Advanced to quote index {new_index}")
    return new_index


def record_quote_history(
    quote_id: int,
    philosopher: str,
    category: str,
    quote_text: str,
    video_path: str,
    duration: float,
) -> int:
    """
    Record that a video was generated for a quote.

    Returns:
        The ID of the new history record.
    """
    session = get_db_session()
    try:
        record = QuoteHistory(
            quote_id=quote_id,
            philosopher=philosopher,
            category=category,
            quote_text=quote_text[:200],  # truncate for DB
            video_path=video_path,
            duration=duration,
            status="generated",
            generated_at=datetime.utcnow(),
        )
        session.add(record)
        session.commit()
        record_id = record.id
    finally:
        session.close()

    logger.info(f"Recorded quote history: record #{record_id}")
    return record_id


def update_quote_youtube_id(record_id: int, youtube_id: str) -> None:
    """Update a history record with the YouTube video ID after upload."""
    session = get_db_session()
    try:
        record = session.query(QuoteHistory).filter_by(id=record_id).first()
        if record:
            record.youtube_id = youtube_id
            record.status = "uploaded"
            record.uploaded_at = datetime.utcnow()
            session.commit()
            logger.info(f"Updated record #{record_id} with YouTube ID: {youtube_id}")
    finally:
        session.close()


def get_quote_history(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent quote generation/upload history."""
    session = get_db_session()
    try:
        records = (
            session.query(QuoteHistory)
            .order_by(QuoteHistory.generated_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": r.id,
                "quote_id": r.quote_id,
                "philosopher": r.philosopher,
                "category": r.category,
                "quote_text": r.quote_text,
                "youtube_id": r.youtube_id,
                "status": r.status,
                "generated_at": r.generated_at.isoformat() if r.generated_at else None,
                "uploaded_at": r.uploaded_at.isoformat() if r.uploaded_at else None,
            }
            for r in records
        ]
    finally:
        session.close()


def set_position(index: int) -> None:
    """
    Manually set the current position in the quotes database.

    Args:
        index: Zero-based index to set.

    Raises:
        QuoteSchedulerError: If index is out of bounds.
    """
    manager = get_quotes_manager()
    total = manager.get_total_quotes()

    if index < 0 or index >= total:
        raise QuoteSchedulerError(
            f"Invalid index {index}. Must be between 0 and {total - 1}."
        )

    session = get_db_session()
    try:
        progress = session.query(QuoteProgress).first()
        if progress:
            progress.current_index = index
            progress.last_updated = datetime.utcnow()
        else:
            progress = QuoteProgress(current_index=index, total_quotes=total)
            session.add(progress)
        session.commit()
    finally:
        session.close()

    logger.info(f"Set position to index {index}")


def get_statistics() -> Dict[str, Any]:
    """Get comprehensive generation statistics."""
    manager = get_quotes_manager()
    progress = get_current_progress()

    session = get_db_session()
    try:
        total_generated = session.query(QuoteHistory).count()
        total_uploaded = (
            session.query(QuoteHistory)
            .filter(QuoteHistory.status == "uploaded")
            .count()
        )

        # Philosopher breakdown
        from sqlalchemy import func

        philosopher_counts = (
            session.query(
                QuoteHistory.philosopher,
                func.count(QuoteHistory.id),
            )
            .group_by(QuoteHistory.philosopher)
            .all()
        )
    finally:
        session.close()

    return {
        **progress,
        "total_generated": total_generated,
        "total_uploaded": total_uploaded,
        "philosopher_breakdown": {
            p: c for p, c in philosopher_counts
        },
    }
