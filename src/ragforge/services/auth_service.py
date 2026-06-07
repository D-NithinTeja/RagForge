"""Authentication service: password hashing and JWT management."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from src.ragforge.config import settings
from src.ragforge.core.exceptions import (
    AuthenticationError,
    ConflictError,
    ForbiddenError,
)
from src.ragforge.models.user import User

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Transform plain-text passwords into secure blocks."""
    # bcrypt requires raw binary bytes for operations; encode before hashing
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError:
        raise AuthenticationError(
            "Provided authentication token is invalid or has expired"
        )

    if not payload.get("sub"):
        raise AuthenticationError(
            "Malformed token context signature: missing subject claim"
        )
    return payload


class AuthService:
    def register(
        self, db: Session, email: str, password: str, full_name: Optional[str] = None
    ) -> User:
        """Register a new user inside our database system if the email is available."""
        if db.query(User).filter(User.email == email).first():
            raise ConflictError(
                "An account associated with this email address already exists"
            )

        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Successfully registered and provisioned user profile: %s", email)
        return user

    def authenticate(self, db: Session, email: str, password: str) -> User:
        """Authenticate an incoming login request against stored database records."""
        user = (
            db.query(User).filter(User.email == email, User.is_active.is_(True)).first()
        )

        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email address or password entered")
        return user

    def get_by_id(self, db: Session, user_id: str) -> User:
        """Retrieve user entities securely using uuid."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise AuthenticationError("Target user record does not exist")
        if not user.is_active:
            raise ForbiddenError(
                "Access denied: This user account has been deactivated"
            )
        return user


# Instantiate a global singleton instance
auth_service = AuthService()
