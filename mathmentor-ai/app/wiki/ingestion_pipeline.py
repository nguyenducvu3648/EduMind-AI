"""Basic wiki ingestion pipeline for Phase 1."""

import time
from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.wiki_chunk import WikiChunk
from app.utils.logging import get_logger
from app.wiki.chunker import MarkdownChunker, WikiChunkDraft
from app.wiki.embedding_service import BGEEmbeddingService

logger = get_logger(__name__)


@dataclass(frozen=True)
class IngestionReport:
    """Summary of a wiki ingestion run."""

    total_articles: int
    total_chunks: int
    errors: list[str] = field(default_factory=list)
    duration_ms: int = 0


class WikiIngestionPipeline:
    """Validate, chunk, embed when configured, and persist wiki markdown articles."""

    def __init__(
        self,
        db_session: AsyncSession,
        chunker: MarkdownChunker | None = None,
        embedding_service: BGEEmbeddingService | None = None,
    ) -> None:
        self.db_session = db_session
        self.chunker = chunker or MarkdownChunker()
        self.embedding_service = embedding_service

    async def ingest_article(self, filepath: str) -> list[UUID]:
        """Ingest a single markdown article and return persisted chunk IDs."""
        started = time.perf_counter()
        logger.info("wiki_ingestion_started", stage="wiki_ingestion", filepath=filepath)
        drafts = self.chunker.chunk(filepath)
        embeddings = await self._embed_drafts(drafts)
        chunk_ids: list[UUID] = []
        for draft, embedding in zip(drafts, embeddings, strict=True):
            chunk = await self._upsert_chunk(draft, embedding)
            chunk_ids.append(chunk.id)
        await self.db_session.commit()
        logger.info(
            "wiki_ingestion_completed",
            stage="wiki_ingestion",
            filepath=filepath,
            chunks=len(chunk_ids),
            duration_ms=int((time.perf_counter() - started) * 1000),
            status="success",
        )
        return chunk_ids

    async def ingest_directory(self, directory: str) -> IngestionReport:
        """Ingest all markdown files under a directory sequentially for Phase 1."""
        started = time.perf_counter()
        root = Path(directory)
        errors: list[str] = []
        total_chunks = 0
        article_count = 0
        for path in sorted(root.rglob("*.md")):
            article_count += 1
            try:
                chunk_ids = await self.ingest_article(str(path))
                total_chunks += len(chunk_ids)
            except Exception as exc:  # noqa: BLE001 - errors are surfaced in report
                await self.db_session.rollback()
                errors.append(f"{path}: {exc}")
                logger.info(
                    "wiki_ingestion_failed",
                    stage="wiki_ingestion",
                    filepath=str(path),
                    status="error",
                    error=str(exc),
                )
        return IngestionReport(
            total_articles=article_count,
            total_chunks=total_chunks,
            errors=errors,
            duration_ms=int((time.perf_counter() - started) * 1000),
        )

    async def _embed_drafts(self, drafts: list[WikiChunkDraft]) -> list[list[float] | None]:
        if self.embedding_service is None:
            return [None for _ in drafts]
        return await self.embedding_service.embed_texts([draft.content for draft in drafts])

    async def _upsert_chunk(
        self,
        draft: WikiChunkDraft,
        embedding: list[float] | None = None,
    ) -> WikiChunk:
        result = await self.db_session.execute(
            select(WikiChunk).where(
                WikiChunk.article_id == draft.article_id,
                WikiChunk.chunk_index == draft.chunk_index,
            )
        )
        chunk = result.scalar_one_or_none()
        if chunk is None:
            chunk = WikiChunk()
            self.db_session.add(chunk)

        chunk.article_id = draft.article_id
        chunk.article_title = draft.article_title
        chunk.section_header = draft.section_header
        chunk.content = draft.content
        chunk.content_type = draft.content_type
        chunk.subject = draft.subject
        chunk.grade_min = draft.grade_min
        chunk.grade_max = draft.grade_max
        chunk.difficulty = draft.difficulty
        chunk.tags = draft.tags
        chunk.concepts = draft.concepts
        chunk.skills = draft.skills
        chunk.prerequisites = draft.prerequisites
        chunk.source_refs = draft.source_refs
        if embedding is not None:
            chunk.embedding = embedding
        chunk.token_count = draft.token_count
        chunk.chunk_index = draft.chunk_index
        await self.db_session.flush()
        return chunk
