"""User profile endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.user import UserProfileRead, UserProfileUpdate, UserRead
from app.db.models.user import User, UserProfile
from app.db.session import get_db_session
from app.dependencies import get_current_user
from app.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/me", response_model=UserRead)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> User:
    """Return the authenticated user's info."""
    return current_user


def _assert_self(user_id: UUID, current_user: User) -> None:
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access another user."
        )


@router.get("/{user_id}/profile", response_model=UserProfileRead)
async def get_profile(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> UserProfile:
    """Return a user's learning profile."""
    _assert_self(user_id, current_user)
    profile = await session.get(UserProfile, user_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
    return profile


@router.patch("/{user_id}/profile", response_model=UserProfileRead)
async def update_profile_preferences(
    user_id: UUID,
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> UserProfile:
    """Update user-controlled behavioral preferences only."""
    _assert_self(user_id, current_user)
    profile = await session.get(UserProfile, user_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(profile, field, value)
    await session.commit()
    await session.refresh(profile)
    logger.info(
        "profile_preferences_updated", stage="profile", user_id=str(user_id), status="success"
    )
    return profile
