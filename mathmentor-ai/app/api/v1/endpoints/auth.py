"""Authentication endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.user import (
    AccessTokenResponse,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserRead,
)
from app.config import Settings, get_settings
from app.core.security import (
    AuthenticationError,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.db.models.user import User, UserProfile
from app.db.session import get_db_session
from app.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserCreate,
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """Register a new student and initialize a learning profile."""
    result = await session.execute(select(User).where(User.email == payload.email.lower()))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered."
        )

    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        grade_level=payload.grade_level,
    )
    user.profile = UserProfile()
    session.add(user)
    await session.commit()
    await session.refresh(user)
    logger.info("user_registered", stage="auth", user_id=str(user.id), status="success")
    return user


@router.post("/login", response_model=TokenResponse)
async def login_user(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """Authenticate a user with email and password."""
    result = await session.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    logger.info("user_login", stage="auth", user_id=str(user.id), status="success")
    return TokenResponse(
        access_token=create_access_token(str(user.id), settings),
        refresh_token=create_refresh_token(str(user.id), settings),
    )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_access_token(
    payload: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> AccessTokenResponse:
    """Validate a refresh token and issue a new access token."""
    try:
        token_payload = decode_refresh_token(payload.refresh_token, settings)
        user_id = UUID(token_payload["sub"])
    except (AuthenticationError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        ) from exc

    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")

    logger.info("token_refreshed", stage="auth", user_id=str(user.id), status="success")
    return AccessTokenResponse(access_token=create_access_token(str(user.id), settings))
