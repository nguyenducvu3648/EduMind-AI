"""Wiki chunk model aligned with actual DB schema."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    from sqlalchemy.types import UserDefinedType

    class Vector(UserDefinedType):
        cache_ok = True

        def __init__(self, dimensions: int) -> None:
            self.dimensions = dimensions

        def get_col_spec(self, **_: object) -> str:
            return f"VECTOR({self.dimensions})"


from app.db.base import Base


class WikiChunk(Base):
    """Wiki chunk — schema matches existing DB."""

    __tablename__ = "wiki_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chunk_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    subject: Mapped[str | None] = mapped_column(Text, nullable=True)
    subject_vn: Mapped[str | None] = mapped_column(Text, nullable=True)
    grade: Mapped[int | None] = mapped_column(Integer, nullable=True)
    topic: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    section: Mapped[str | None] = mapped_column(Text, nullable=True)
    has_formula: Mapped[bool | None] = mapped_column(Boolean, default=False)
    length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now(), nullable=True
    )
