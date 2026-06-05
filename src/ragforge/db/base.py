"""SQLAlchemy declarative base configuration."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all relational database models inside RAGForge."""

    pass
