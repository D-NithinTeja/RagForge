from sqlalchemy import text

from src.ragforge.db.session import engine, get_database_url


def test_database_url_resolution():
    url = get_database_url()
    assert url.startswith("sqlite") or "ragforge.db" in url


def test_sqlite_foreign_key_pragma():
    """Ensure our connectivity pragma rule activates foreign key enforcement."""
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA foreign_keys;")).fetchone()
        # The pragma state returns a tuple check where position 0 maps to 1 (Enabled)
        assert result[0] == 1
