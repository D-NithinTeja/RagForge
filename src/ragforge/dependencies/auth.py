"""Authentication dependency for protected routes."""

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.ragforge.dependencies.db import get_db
from src.ragforge.models.user import User
from src.ragforge.services.auth_service import auth_service, decode_token

# Automatically scans HTTP request headers looking for 'Authorization: Bearer <token>'
# tokenUrl informs Swagger docs where to send credentials to receive a token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """Intercept incoming request tokens, decode credentials, and return the active User record.
    Raises an explicit HTTP 401 error or 403 response if tokens are missing, expired,
    or map to an inactive system profile.
    """

    payload = decode_token(token)
    user_id: str = payload.get("sub")
    return auth_service.get_by_id(db, user_id)
