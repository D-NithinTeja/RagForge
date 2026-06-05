from sqlalchemy.orm import Session

from src.ragforge.dependencies.db import get_db


def test_database_dependency_lifecycle():
    """Verify that get_db successfully creates and tears down a database session."""

    db_generator = get_db()

    db_session = next(db_generator)  # Trigger execution up to the yield point

    assert isinstance(db_session, Session)
    assert db_session.is_active is True

    try:
        next(db_generator)
    except StopIteration:
        pass
