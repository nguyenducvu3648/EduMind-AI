"""User and user profile models."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, Float, ForeignKey, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, created_at_col, updated_at_col, uuid_pk


class User(Base):
    """Authenticated student or administrator account."""

    __tablename__ = "users"
    __table_args__ = (CheckConstraint("grade_level BETWEEN 10 AND 12", name="ck_users_grade"),)

    id: Mapped[UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    grade_level: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="student", nullable=False)
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()

    profile: Mapped["UserProfile"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )


class UserProfile(Base):
    """Multi-layer personalized learning representation for a user."""

    __tablename__ = "user_profiles"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    topic_mastery: Mapped[dict[str, float]] = mapped_column(JSONB, default=dict, nullable=False)
    concept_dependency_map: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    misconception_patterns: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )
    learning_speed: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    retention_strength: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    error_recurrence_rate: Mapped[float] = mapped_column(Float, default=0.3, nullable=False)
    cognitive_load_tolerance: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    response_preference: Mapped[str] = mapped_column(String(50), default="balanced", nullable=False)
    hint_dependency_level: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    step_by_step_preference: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    weak_topics: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, nullable=False)
    strong_topics: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, nullable=False)
    updated_at: Mapped[datetime] = updated_at_col()

    user: Mapped[User] = relationship(back_populates="profile", lazy="selectin")
