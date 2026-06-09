"""SQLAlchemy declarative base and shared column helpers."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""


def uuid_pk() -> Mapped[UUID]:
    """Return a UUID primary-key mapped column."""
    return mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)


def created_at_col() -> Mapped[datetime]:
    """Return a creation timestamp column."""
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def updated_at_col() -> Mapped[datetime]:
    """Return an update timestamp column."""
    return mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
