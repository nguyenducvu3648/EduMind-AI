"""Admin authentication endpoints — login with email+password + role=admin check."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.user import AdminLoginRequest, AdminTokenResponse, UserRead
from app.config import Settings, get_settings
from app.core.security import create_access_token, verify_password
from app.db.models.user import User
from app.db.session import get_db_session
from app.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/login", response_model=AdminTokenResponse)
async def admin_login(
    payload: AdminLoginRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> AdminTokenResponse:
    """Authenticate an admin user with email + password + role='admin' check."""
    result = await session.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )

    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an admin account.",
        )

    logger.info("admin_login_ok", user_id=str(user.id), email=user.email)
    return AdminTokenResponse(
        access_token=create_access_token(str(user.id), settings),
        user=UserRead.model_validate(user),
    )
