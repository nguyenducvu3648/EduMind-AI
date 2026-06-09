"""Tests for Reciprocal Rank Fusion."""

from uuid import uuid4

from app.rag.rrf import reciprocal_rank_fusion
from app.rag.types import RetrievedChunk


def _chunk(chunk_id=None, score: float = 1.0) -> RetrievedChunk:
    return RetrievedChunk(
        id=chunk_id or uuid4(),
        article_id="quadratic_equations",
        article_title="Phuong trinh bac hai",
        section_header="Concept",
        content="content",
        content_type="concept",
        subject="Toan",
        grade_min=10,
        grade_max=12,
        difficulty=0.4,
        score=score,
    )


def test_reciprocal_rank_fusion_combines_duplicate_documents() -> None:
    shared_id = uuid4()
    first = _chunk(shared_id, score=0.8)
    second = _chunk(shared_id, score=0.7)
    other = _chunk(score=0.9)

    fused = reciprocal_rank_fusion([[first, other], [second]])

    assert fused[0].id == shared_id
    assert fused[0].score == (1 / 61) + (1 / 61)
    assert fused[0].retrieval_method == "hybrid_rrf"
