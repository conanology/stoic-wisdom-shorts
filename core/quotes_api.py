"""
Quotes API - Manages the curated philosophy quotes database
"""
import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger


# Path to the quotes database
QUOTES_DB_PATH = Path(__file__).parent.parent / "quotes_database.json"
PHILOSOPHERS_PATH = Path(__file__).parent.parent / "philosophers.json"


class QuotesManager:
    """Manages loading, filtering, and sequential access to the quotes database."""

    def __init__(self):
        self._quotes: List[Dict[str, Any]] = []
        self._philosophers: Dict[str, Dict[str, Any]] = {}
        self._categories: List[str] = []
        self._loaded = False

    def _ensure_loaded(self):
        """Lazy-load quotes and philosophers on first access."""
        if self._loaded:
            return

        # Load quotes
        if not QUOTES_DB_PATH.exists():
            raise FileNotFoundError(
                f"Quotes database not found at {QUOTES_DB_PATH}. "
                "Please ensure quotes_database.json exists in the project root."
            )

        with open(QUOTES_DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._quotes = data.get("quotes", [])
        metadata = data.get("metadata", {})
        self._categories = metadata.get("categories", [])

        # Load philosophers
        if PHILOSOPHERS_PATH.exists():
            with open(PHILOSOPHERS_PATH, "r", encoding="utf-8") as f:
                phil_data = json.load(f)
            for p in phil_data.get("philosophers", []):
                self._philosophers[p["key"]] = p

        self._loaded = True
        logger.info(
            f"Loaded {len(self._quotes)} quotes from "
            f"{len(self._philosophers)} philosophers"
        )

    # ── Core Access ───────────────────────────────────────────────────

    def get_total_quotes(self) -> int:
        """Return total number of quotes in the database."""
        self._ensure_loaded()
        return len(self._quotes)

    def get_quote_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Get a quote by its zero-based index in the database.

        Args:
            index: Zero-based position in the quotes list.

        Returns:
            Quote dict or None if index is out of bounds.
        """
        self._ensure_loaded()
        if 0 <= index < len(self._quotes):
            return self._quotes[index]
        return None

    def get_quote_by_id(self, quote_id: int) -> Optional[Dict[str, Any]]:
        """Get a quote by its unique ID field."""
        self._ensure_loaded()
        for q in self._quotes:
            if q.get("id") == quote_id:
                return q
        return None

    # ── Filtering ─────────────────────────────────────────────────────

    def get_quotes_by_philosopher(self, philosopher_key: str) -> List[Dict[str, Any]]:
        """Return all quotes from a specific philosopher."""
        self._ensure_loaded()
        return [q for q in self._quotes if q.get("author") == philosopher_key]

    def get_quotes_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Return all quotes in a specific category."""
        self._ensure_loaded()
        return [q for q in self._quotes if q.get("category") == category]

    def get_random_quote(
        self,
        philosopher: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a random quote, optionally filtered by philosopher or category.

        Args:
            philosopher: Optional philosopher key to filter by.
            category: Optional category to filter by.

        Returns:
            A random quote dict.

        Raises:
            ValueError: If no quotes match the filters.
        """
        self._ensure_loaded()
        pool = self._quotes

        if philosopher:
            pool = [q for q in pool if q.get("author") == philosopher]
        if category:
            pool = [q for q in pool if q.get("category") == category]

        if not pool:
            raise ValueError(
                f"No quotes found for philosopher='{philosopher}', category='{category}'"
            )

        return random.choice(pool)

    def get_categories(self) -> List[str]:
        """Return all available categories."""
        self._ensure_loaded()
        return list(self._categories)

    def get_philosopher_keys(self) -> List[str]:
        """Return all available philosopher keys."""
        self._ensure_loaded()
        return list(self._philosophers.keys())

    # ── Philosopher Metadata ──────────────────────────────────────────

    def get_philosopher(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get full philosopher metadata by key.

        Returns:
            Dict with name, era, title, tradition, notable_work or None.
        """
        self._ensure_loaded()
        return self._philosophers.get(key)

    def get_philosopher_name(self, key: str) -> str:
        """Get display name for a philosopher. Falls back to title-cased key."""
        phil = self.get_philosopher(key)
        if phil:
            return phil["name"]
        return key.replace("_", " ").title()

    # ── Video Formatting ──────────────────────────────────────────────

    def format_for_video(self, quote: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare a quote for the video generator with all display fields.

        Args:
            quote: Raw quote dict from the database.

        Returns:
            Dict with keys: quote_text, author_name, author_key, source,
            category, word_count, philosopher_meta, hook_intro, reflection
        """
        self._ensure_loaded()
        author_key = quote.get("author", "unknown")
        author_name = self.get_philosopher_name(author_key)
        text = quote.get("text", "")
        category = quote.get("category", "wisdom")
        meta = self.get_philosopher(author_key)

        result = {
            "quote_id": quote.get("id"),
            "quote_text": text,
            "author_name": author_name,
            "author_key": author_key,
            "source": quote.get("source", ""),
            "category": category,
            "word_count": len(text.split()),
            "philosopher_meta": meta,
        }

        # Add generated hook and reflection
        result["hook_intro"] = self.generate_hook_intro(author_name, meta)
        result["reflection"] = self.generate_reflection(text, category)

        return result

    # ── Narration Generators ──────────────────────────────────────────

    def generate_hook_intro(
        self,
        author_name: str,
        meta: Optional[Dict[str, Any]],
    ) -> str:
        """
        Generate a compelling narrator intro using philosopher metadata.

        Examples:
          "Over 2,000 years ago, Marcus Aurelius, the last great
           Emperor of Rome, wrote in his Meditations..."
        """
        if meta is None:
            return f"{author_name} once said."

        era = meta.get("era", "")
        title = meta.get("title", "")
        work = meta.get("notable_work", "")
        name = meta.get("name", author_name)

        templates = []

        # Templates that use era + title
        if era and title:
            templates += [
                f"In {era}, {name}, {title}, left behind words that still echo today.",
                f"{name} was a {title} who lived in {era}. This is one of his most powerful teachings.",
                f"Centuries ago, {name}, known as a {title}, shared a truth that has only grown more relevant.",
            ]

        # Templates that use notable_work
        if work:
            templates += [
                f"In the pages of {work}, {name} wrote something that would outlast empires.",
                f"{name} wrote these words in {work}, and they still hold power today.",
            ]

        # Templates that use title only
        if title:
            templates += [
                f"{name}, {title}, once shared a truth the world still needs to hear.",
                f"Listen carefully to the words of {name}, {title}.",
            ]

        # Generic fallback
        if not templates:
            templates = [
                f"Listen to the timeless words of {name}.",
                f"{name} once shared a truth that still resonates today.",
            ]

        return random.choice(templates)

    def generate_reflection(self, quote_text: str, category: str) -> str:
        """
        Generate a 1-2 sentence modern reflection on the quote's meaning.

        Returns a brief, thought-provoking takeaway connecting the ancient
        wisdom to modern life.
        """
        reflections = {
            "discipline": [
                "Discipline is not about punishment. It is about choosing who you want to become, every single day.",
                "The hardest battles are fought within. Master yourself, and the world will follow.",
                "Freedom is not the absence of rules. It is the strength to govern yourself.",
            ],
            "wisdom": [
                "Wisdom is not knowing everything. It is knowing what truly matters.",
                "In a world full of noise, the wisest voice is often the quietest.",
                "True understanding begins the moment you admit how little you actually know.",
            ],
            "resilience": [
                "You were not built to break. You were built to bend, adapt, and rise again.",
                "Suffering is not the enemy. Surrendering to it is.",
                "The obstacle in your path is not blocking the way. It is the way.",
            ],
            "virtue": [
                "Character is not built in comfort. It is forged in the moments you choose to do what is right, not what is easy.",
                "The world does not need more talented people. It needs more people with integrity.",
                "Your reputation is what others think of you. Your character is who you truly are.",
            ],
            "mindfulness": [
                "Be here. Not in yesterday's regret, not in tomorrow's worry. Right here, right now.",
                "The present moment is the only moment that truly belongs to you. Do not waste it.",
                "Silence your mind, and you will hear the answers you have been searching for.",
            ],
            "purpose": [
                "A life without purpose is a ship without a rudder, drifting wherever the current takes it.",
                "You do not find your purpose. You build it, one meaningful choice at a time.",
                "Wake up with intention. The world rewards those who know exactly why they rise.",
            ],
            "adversity": [
                "Every setback carries a lesson. The question is whether you are willing to learn it.",
                "Pain is temporary. The strength you gain from enduring it is permanent.",
                "When life knocks you down, remember: you have gotten back up every single time before.",
            ],
            "inner_peace": [
                "Peace is not the absence of chaos. It is the ability to remain calm in the middle of it.",
                "You cannot control the world around you. But you can always control the world within you.",
                "Stillness is not weakness. It is the most powerful form of strength.",
            ],
        }

        # Get reflections for the category, or fall back to wisdom
        options = reflections.get(category, reflections.get("wisdom", []))
        if not options:
            options = [
                "Let these words sit with you. Sometimes the greatest truths take time to unfold.",
                "Ancient wisdom does not expire. It only becomes more necessary.",
            ]

        return random.choice(options)


# ── Module-level singleton ────────────────────────────────────────────

_manager: Optional[QuotesManager] = None


def get_quotes_manager() -> QuotesManager:
    """Get or create the global QuotesManager instance."""
    global _manager
    if _manager is None:
        _manager = QuotesManager()
    return _manager
