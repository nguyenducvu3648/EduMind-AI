"""Reciprocal Rank Fusion utilities."""

from collections.abc import Iterable, Sequence
from dataclasses import replace
from app.rag.types import RetrievedChunk

RRF_K = 60


def reciprocal_rank_fusion(
    ranked_lists: Sequence[Sequence[RetrievedChunk]],
    k: int = RRF_K,
) -> list[RetrievedChunk]:
    """Fuse ranked lists with the standard RRF formula.

    RRF_score(d) = sum(1 / (k + rank_i(d)))
    """
    scores: dict[int, float] = {}
    best_chunk_by_id: dict[int, RetrievedChunk] = {}

    for ranked_list in ranked_lists:
        for rank, chunk in enumerate(ranked_list, start=1):
            scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (k + rank)
            current_best = best_chunk_by_id.get(chunk.id)
            if current_best is None or chunk.score > current_best.score:
                best_chunk_by_id[chunk.id] = chunk

    return [
        replace(best_chunk_by_id[chunk_id], score=score, retrieval_method="hybrid_rrf")
        for chunk_id, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)
    ]


def deduplicate_chunks(chunks: Iterable[RetrievedChunk]) -> list[RetrievedChunk]:
    """Deduplicate chunks by ID while preserving first occurrence order."""
    seen: set[UUID] = set()
    unique: list[RetrievedChunk] = []
    for chunk in chunks:
        if chunk.id in seen:
            continue
        seen.add(chunk.id)
        unique.append(chunk)
    return unique
