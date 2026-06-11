"""Admin user management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.user import UserProfileRead, UserRead
from app.db.models.user import User, UserProfile
from app.db.session import get_db_session
from app.dependencies import verify_admin_api_key
from app.utils.logging import get_logger

router = APIRouter(dependencies=[Depends(verify_admin_api_key)])
logger = get_logger(__name__)


@router.get("/users", response_model=list[UserRead])
async def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    search: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> list[User]:
    """List all users with optional email search."""
    stmt = select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
    if search:
        stmt = stmt.where(User.email.ilike(f"%{search}%"))
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.get("/users/count")
async def count_users(
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Return total number of users."""
    result = await session.execute(select(func.count()).select_from(User))
    return {"total": result.scalar() or 0}


@router.get("/users/{user_id}", response_model=UserRead)
async def get_user_detail(
    user_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """Get a single user by ID."""
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


@router.get("/users/{user_id}/profile", response_model=UserProfileRead)
async def get_user_profile(
    user_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> UserProfile:
    """Get a user's full learning profile."""
    profile = await session.get(UserProfile, user_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
    return profile


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: UUID,
    payload: dict,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Change a user's role (e.g. promote to admin, demote to student)."""
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    new_role = payload.get("role")
    if new_role not in ("student", "admin"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Role must be 'student' or 'admin'.",
        )

    user.role = new_role
    await session.commit()
    await session.refresh(user)
    logger.info("admin_user_role_updated", user_id=str(user_id), role=new_role)
    return {"id": str(user.id), "email": user.email, "role": user.role}


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a user and all associated data (cascade)."""
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    await session.delete(user)
    await session.commit()
    logger.info("admin_user_deleted", user_id=str(user_id))
