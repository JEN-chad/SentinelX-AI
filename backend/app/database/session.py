"""SentinelX AI - Database Engine and Session Management

Configures connection pooling, session factories, and database health verification.
Provides seamless fallback to SQLite for local development and testing if PostgreSQL is unavailable.
"""

import logging
from typing import Any, Dict, Generator
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from .base import Base

logger = logging.getLogger("sentinelx.database")


def create_app_engine(database_url: str):
    """Create a resilient SQLAlchemy engine with SQLite test fallback."""
    is_sqlite = database_url.startswith("sqlite")
    connect_args = {"check_same_thread": False} if is_sqlite else {}

    try:
        engine = create_engine(
            database_url,
            connect_args=connect_args,
            echo=False,
            future=True,
        )
        # Verify connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        logger.warning(
            f"Failed to connect to primary database at '{database_url}': {e}. "
            f"Falling back to local SQLite database 'sqlite:///./sentinelx_fallback.db'."
        )
        fallback_url = "sqlite:///./sentinelx_fallback.db"
        return create_engine(
            fallback_url,
            connect_args={"check_same_thread": False},
            echo=False,
            future=True,
        )


engine = create_app_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(target_engine=None) -> None:
    """Create all database tables if they do not exist."""
    active_engine = target_engine or engine
    Base.metadata.create_all(bind=active_engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI request-scoped dependency providing a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_health(target_engine=None) -> Dict[str, Any]:
    """Verify database responsiveness and return connectivity status."""
    active_engine = target_engine or engine
    try:
        with active_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "dialect": active_engine.dialect.name,
            "connected": True,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "dialect": active_engine.dialect.name,
            "connected": False,
            "error": str(e),
        }
