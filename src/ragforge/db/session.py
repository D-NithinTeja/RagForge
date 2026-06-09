"""Database connection and transactional session management"""

import logging

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.ragforge.config import settings
from src.ragforge.db.base import Base

logger = logging.getLogger(__name__)

DEFAULT_DATABASE_URL: str = "sqlite:///./ragforge.db"


def get_database_url() -> str:
    """Validate configuration inputs and fall back safely to development SQLite if required."""
    try:
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgresql"):
            if "<" in db_url:
                logger.info(
                    "Placeholder caught in database configuration string. Falling back to SQLite."
                )
                return DEFAULT_DATABASE_URL
        return db_url
    except Exception:
        logger.warning(
            "Error resolving database parameters. Resorting to SQLite engine default."
        )
        return DEFAULT_DATABASE_URL


def create_db_engine(database_url: str | None = None):
    url = database_url or get_database_url()

    if url.startswith("sqlite"):
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        logger.info("SQLite engine mounted successfully: %s", url)

    else:
        try:
            pool_size = settings.DB_POOL_SIZE
            max_overflow = settings.DB_MAX_OVERFLOW
        except Exception:
            pool_size = 5
            max_overflow = 10

        engine = create_engine(
            url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # Test staleness on checkout to prevent 500 disconnect drops
            echo=False,
        )
        logger.info(
            "PostgreSQL production infrastructure mapped with pool_size=%d", pool_size
        )

    return engine


engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _apply_migrations() -> None:
    """Safely apply incremental updates onto local developer files"""

    migrations = [
        ("documents", "image_count", "INTEGER"),
        ("documents", "table_count", "INTEGER"),
    ]

    with engine.connect() as conn:
        for table, column, col_type in migrations:
            try:
                conn.execute(
                    text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
                )
                conn.commit()
                logger.info(
                    "Local development migration applied: added %s.%s", table, column
                )
            except Exception:
                pass


def init_db() -> None:
    """Create physical table mapped across models."""

    Base.metadata.create_all(bind=engine)
    _apply_migrations()
    logger.info("Database structural verification complete.")


def drop_db() -> None:
    Base.metadata.drop_all(bind=engine)
    logger.warning("Database dropped completely.")
