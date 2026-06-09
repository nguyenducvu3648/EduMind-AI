"""Evaluation run model."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, created_at_col, uuid_pk


class EvaluationRun(Base):
    """Offline evaluation execution record."""

    __tablename__ = "evaluation_runs"

    id: Mapped[UUID] = uuid_pk()
    run_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    sample_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    triggered_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = created_at_col()
