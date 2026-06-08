import pytest

from src.ragforge.core.exceptions import AuthenticationError
from src.ragforge.db.base import Base
from src.ragforge.db.session import SessionLocal, engine
from src.ragforge.dependencies.auth import get_current_user
from src.ragforge.services.auth_service import auth_service, create_access_token


def test_get_current_user_valid_token():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        user = auth_service.register(db, email="dev@example.com", password="something")

        token = create_access_token(user_id=user.id, email=user.email)

        resolved_user = get_current_user(token=token, db=db)

        assert resolved_user.id == user.id
        assert resolved_user.email == "dev@example.com"
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_get_current_user_invalid_token():
    db = SessionLocal()
    try:
        with pytest.raises(AuthenticationError):
            get_current_user(token="random-token-string", db=db)
    finally:
        db.close()
