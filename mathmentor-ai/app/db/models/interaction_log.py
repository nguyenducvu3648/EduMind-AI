"""Interaction log model."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, created_at_col, uuid_pk


class InteractionLog(Base):
    """Immutable record of one tutoring interaction and its pipeline metadata."""

    __tablename__ = "interaction_logs"

    id: Mapped[UUID] = uuid_pk()
    session_id: Mapped[UUID] = mapped_column(ForeignKey("sessions.id"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    intent_detected: Mapped[str | None] = mapped_column(String(100), nullable=True)
    topics_detected: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    teaching_strategy: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bloom_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    learner_type_at_time: Mapped[str | None] = mapped_column(String(50), nullable=True)
    context_chunks_used: Mapped[list[UUID] | None] = mapped_column(
        ARRAY(PG_UUID(as_uuid=True)), nullable=True
    )
    hint_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    response_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_feedback: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    created_at: Mapped[datetime] = created_at_col()
