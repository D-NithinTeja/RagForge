import pytest

from src.ragforge.core.exceptions import AuthenticationError, ConflictError
from src.ragforge.db.base import Base
from src.ragforge.db.session import SessionLocal, engine
from src.ragforge.services.auth_service import (
    auth_service,
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_encryption_flow():
    raw_pass = "right_pass"
    hashed = hash_password(raw_pass)

    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("wrong_pass", hashed) is False


def test_token_issuance_and_decoding():
    token = create_access_token(user_id="yona", email="test@example.com")
    payload = decode_token(token)

    assert payload["sub"] == "yona"
    assert payload["email"] == "test@example.com"


def test_user_registration_service_lifecyle():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        user = auth_service.register(
            db, email="test@example.com", password="right_pass123"
        )
        assert user.id is not None
        assert user.email == "test@example.com"

        with pytest.raises(ConflictError):
            auth_service.register(
                db, email="test@example.com", password="right_pass123"
            )

    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
