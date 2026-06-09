"""Shared RAG data structures aligned with actual wiki_chunks schema."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RetrievedChunk:
    """Wiki chunk returned by retrieval — matches existing DB columns."""

    id: int
    chunk_id: str
    title: str
    section: str | None
    content: str
    subject: str | None
    subject_vn: str | None
    grade: int | None
    topic: str | None
    document_id: str | None
    source: str | None
    chunk_type: str | None
    has_formula: bool | None
    length: int | None
    chunk_index: int | None
    score: float = 0.0
    retrieval_method: str = "unknown"
