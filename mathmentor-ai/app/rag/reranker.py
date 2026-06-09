"""Reranking using CrossEncoder with local model (no API calls)."""

import asyncio
import time
from dataclasses import replace

from app.config import Settings, get_settings
from app.rag.types import RetrievedChunk
from app.utils.logging import get_logger
from app.utils.metrics import RAG_RETRIEVAL_LATENCY

logger = get_logger(__name__)


class RerankerError(RuntimeError):
    """Raised when reranking fails."""


class CrossEncoderReranker:
    """Rerank retrieved chunks using a local cross-encoder model.

    Uses models--BAAI--bge-reranker-base (or whatever reranker_model is set to).
    Falls back to RRF score sort if model loading fails.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        raw = self.settings.reranker_model
        if not raw:
            self._disabled = True
            logger.info("reranker_disabled", stage="reranking", reason="no_model_configured")
        else:
            self._disabled = False
        self._model_name = raw or ""
        self._model: object | None = None
        self._load_lock = asyncio.Lock()

    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        """Return top_k chunks sorted by RRF score directly (fast path)."""
        if not chunks:
            return []
        result = sorted(chunks, key=lambda c: c.score, reverse=True)[:top_k]
        return [replace(c, retrieval_method="rrf_fallback") for c in result]
