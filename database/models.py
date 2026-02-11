"""
Database Models - SQLAlchemy models for Stoic Wisdom Shorts

Tables:
  - QuoteProgress: Tracks current position in the quotes database
  - QuoteHistory: Logs each generated/uploaded video
  - AppSettings: Key-value settings store
"""
from datetime import datetime
from pathlib import Path

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from loguru import logger

from config.settings import DATABASE_URL, DATABASE_PATH


Base = declarative_base()


# ══════════════════════════════════════════════════════════════════════
# Models
# ══════════════════════════════════════════════════════════════════════

class QuoteProgress(Base):
    """Tracks sequential progress through the quotes database."""
    __tablename__ = "quote_progress"

    id = Column(Integer, primary_key=True)
    current_index = Column(Integer, default=0, nullable=False)
    total_quotes = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<QuoteProgress index={self.current_index}/{self.total_quotes}>"


class QuoteHistory(Base):
    """Logs each generated/uploaded video."""
    __tablename__ = "quote_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quote_id = Column(Integer, nullable=False)
    philosopher = Column(String(100), nullable=False)
    category = Column(String(50))
    quote_text = Column(Text)
    video_path = Column(String(500))
    youtube_id = Column(String(50))
    duration = Column(Float)
    status = Column(String(20), default="generated")  # generated, uploaded, failed
    generated_at = Column(DateTime, default=datetime.utcnow)
    uploaded_at = Column(DateTime)

    def __repr__(self):
        return (
            f"<QuoteHistory #{self.id} quote={self.quote_id} "
            f"phil={self.philosopher} status={self.status}>"
        )


class AppSettings(Base):
    """Simple key-value settings store."""
    __tablename__ = "app_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AppSettings {self.key}={self.value}>"


# ══════════════════════════════════════════════════════════════════════
# Engine & Session
# ══════════════════════════════════════════════════════════════════════

_engine = None
_Session = None


def get_engine():
    """Get or create the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(DATABASE_URL, echo=False)
    return _engine


def get_db_session():
    """Get a new database session."""
    global _Session
    if _Session is None:
        _Session = sessionmaker(bind=get_engine())
    return _Session()


def init_database():
    """Create all tables if they don't exist."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    logger.debug("Database initialized")


# ══════════════════════════════════════════════════════════════════════
# Settings Helpers
# ══════════════════════════════════════════════════════════════════════

def get_setting(key: str, default: str = None) -> str:
    """Get a setting value from the database."""
    session = get_db_session()
    try:
        setting = session.query(AppSettings).filter_by(key=key).first()
        return setting.value if setting else default
    finally:
        session.close()


def set_setting(key: str, value: str) -> None:
    """Set a setting value in the database."""
    session = get_db_session()
    try:
        setting = session.query(AppSettings).filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = AppSettings(key=key, value=value)
            session.add(setting)
        session.commit()
    finally:
        session.close()
