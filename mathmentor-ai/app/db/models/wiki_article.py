"""WikiArticle model for LLM-Wiki — curated knowledge articles."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, created_at_col, updated_at_col, uuid_pk


class WikiArticle(Base):
    """LLM-Wiki: curated knowledge article for one concept.

    Each row is a "standard article" — written in clean Markdown with
    consistent structure (definition, examples, common mistakes, etc.).
    This is the "trusted knowledge layer" between RAG and Orchestration.
    """

    __tablename__ = "wiki_articles"

    id: Mapped[UUID] = uuid_pk()
    slug: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Metadata
    subject: Mapped[str | None] = mapped_column(String(50), nullable=True)
    grade: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difficulty: Mapped[float | None] = mapped_column(Float, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    concepts: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)

    # Structure hints
    has_examples: Mapped[bool] = mapped_column(default=False, nullable=False)
    has_common_mistakes: Mapped[bool] = mapped_column(default=False, nullable=False)
    has_formula: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relations
    related_slugs: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Status
    is_published: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = created_at_col()
    updated_at: Mapped[datetime] = updated_at_col()
