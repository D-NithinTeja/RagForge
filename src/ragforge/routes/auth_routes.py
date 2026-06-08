"""Authentication routes: register, login, and current user."""

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.ragforge.dependencies.auth import get_current_user
from src.ragforge.dependencies.db import get_db
from src.ragforge.models.user import User
from src.ragforge.schemas.auth import RegisterRequest, TokenResponse, UserResponse
from src.ragforge.services.auth_service import auth_service, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={
        status.HTTP_409_CONFLICT: {
            "description": "An account with this email already exists"
        }
    },
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = auth_service.register(
        db=db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
    )
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive a JWT token",
    description="Submit your registered email address inside the standard **username** field.",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid email or password combination"
        }
    },
)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth_service.authenticate(db, form.username, form.password)
    token = create_access_token(user.id, user.email)
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Provided authentication token is invalid or has expired"
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Access denied: Account is deactivated"
        },
    },
)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )
