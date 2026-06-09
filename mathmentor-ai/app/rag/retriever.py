"""Hybrid pgvector and PostgreSQL full-text retriever — aligned with actual DB schema."""

import asyncio
import time
from dataclasses import replace
from typing import Any

from sqlalchemy import Select, and_, bindparam, func, literal, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.wiki_chunk import WikiChunk
from app.rag.rrf import reciprocal_rank_fusion
from app.rag.types import RetrievedChunk
from app.utils.logging import get_logger
from app.utils.metrics import RAG_RETRIEVAL_LATENCY
from app.wiki.embedding_service import BGEEmbeddingService

logger = get_logger(__name__)


class HybridRetriever:
    """Retrieve wiki chunks using pgvector semantic search plus PostgreSQL BM25 ranking."""

    def __init__(
        self,
        db_session: AsyncSession,
        embedding_service: BGEEmbeddingService | None = None,
    ) -> None:
        self.db_session = db_session
        self.embedding_service = embedding_service or BGEEmbeddingService()

    async def retrieve(
        self,
        queries: list[str],
        metadata_filter: dict,
        user_profile: object | None = None,
        top_k_semantic: int = 20,
        top_k_bm25: int = 20,
        final_top_k: int = 10,
    ) -> list[RetrievedChunk]:
        """Run semantic and BM25 retrieval in parallel, fuse with RRF, then apply filters."""
        normalized_queries = [query.strip() for query in queries if query.strip()]
        if not normalized_queries:
            return []

        started = time.perf_counter()
        semantic_task = self.semantic_search(normalized_queries, metadata_filter, top_k_semantic)
        bm25_task = self.bm25_search(normalized_queries, metadata_filter, top_k_bm25)

        try:
            semantic_results, bm25_results = await asyncio.gather(semantic_task, bm25_task)
        except Exception as exc:
            logger.info(
                "semantic_search_failed",
                stage="rag_retrieval",
                status="fallback_bm25_only",
                error=str(exc),
            )
            bm25_results = await self.bm25_search(normalized_queries, metadata_filter, top_k_bm25)
            final = sorted(bm25_results, key=lambda chunk: chunk.score, reverse=True)[:final_top_k]
            duration = time.perf_counter() - started
            RAG_RETRIEVAL_LATENCY.labels(stage="hybrid").observe(duration)
            logger.info(
                "hybrid_retrieval_completed",
                stage="rag_retrieval",
                status="success_bm25_fallback",
                queries=len(normalized_queries),
                bm25_results=len(bm25_results),
                final_results=len(final),
                duration_ms=int(duration * 1000),
            )
            return final

        fused = reciprocal_rank_fusion([semantic_results, bm25_results])
        final = sorted(fused, key=lambda chunk: chunk.score, reverse=True)[:final_top_k]

        duration = time.perf_counter() - started
        RAG_RETRIEVAL_LATENCY.labels(stage="hybrid").observe(duration)
        logger.info(
            "hybrid_retrieval_completed",
            stage="rag_retrieval",
            status="success",
            queries=len(normalized_queries),
            semantic_results=len(semantic_results),
            bm25_results=len(bm25_results),
            final_results=len(final),
            duration_ms=int(duration * 1000),
        )
        return final

    async def semantic_search(
        self,
        queries: list[str],
        metadata_filter: dict,
        top_k: int = 20,
    ) -> list[RetrievedChunk]:
        """Search pgvector embeddings by cosine distance for each query variant."""
        started = time.perf_counter()
        embeddings = await self.embedding_service.embed_texts(queries)
        ranked_lists = await asyncio.gather(
            *[
                self._semantic_search_one(embedding, metadata_filter, top_k)
                for embedding in embeddings
            ]
        )
        results = reciprocal_rank_fusion(ranked_lists)
        RAG_RETRIEVAL_LATENCY.labels(stage="semantic").observe(time.perf_counter() - started)
        return results[:top_k]

    async def bm25_search(
        self,
        queries: list[str],
        metadata_filter: dict,
        top_k: int = 20,
    ) -> list[RetrievedChunk]:
        """Search PostgreSQL full-text index with BM25-like ts_rank_cd scoring."""
        started = time.perf_counter()
        ranked_lists = await asyncio.gather(
            *[self._bm25_search_one(query, metadata_filter, top_k) for query in queries]
        )
        results = reciprocal_rank_fusion(ranked_lists)
        RAG_RETRIEVAL_LATENCY.labels(stage="bm25").observe(time.perf_counter() - started)
        return results[:top_k]

    async def _semantic_search_one(
        self,
        embedding: list[float],
        metadata_filter: dict,
        top_k: int,
    ) -> list[RetrievedChunk]:
        distance = WikiChunk.embedding.cosine_distance(embedding).label("distance")
        statement = select(WikiChunk, (1.0 - distance).label("score")).where(
            WikiChunk.embedding.is_not(None)
        )
        statement = self._apply_metadata_filter(statement, metadata_filter)
        statement = statement.order_by(distance).limit(top_k)
        result = await self.db_session.execute(statement)
        return [
            self._to_retrieved_chunk(chunk, float(score or 0.0), "semantic")
            for chunk, score in result.all()
        ]

    async def _bm25_search_one(
        self,
        query: str,
        metadata_filter: dict,
        top_k: int,
    ) -> list[RetrievedChunk]:
        # Use 'pg_catalog.english' instead of 'english' to avoid undefined-text-config errors
        ts_vector = func.to_tsvector(WikiChunk.content)
        ts_query = func.plainto_tsquery(bindparam("query_text"))
        rank = func.ts_rank_cd(ts_vector, ts_query).label("score")
        statement = select(WikiChunk, rank).where(ts_vector.op("@@")(ts_query))
        statement = self._apply_metadata_filter(statement, metadata_filter)
        statement = statement.order_by(text("score DESC")).limit(top_k)
        result = await self.db_session.execute(statement, {"query_text": query})
        return [
            self._to_retrieved_chunk(chunk, float(score or 0.0), "bm25")
            for chunk, score in result.all()
        ]

    def _apply_metadata_filter(
        self,
        statement: Select[tuple[WikiChunk, Any]],
        metadata_filter: dict,
    ) -> Select[tuple[WikiChunk, Any]]:
        filters = []

        grade = metadata_filter.get("grade")
        if grade is not None:
            filters.append(WikiChunk.grade == grade)

        grade_min = metadata_filter.get("grade_min")
        if grade_min is not None:
            filters.append(WikiChunk.grade >= grade_min)

        grade_max = metadata_filter.get("grade_max")
        if grade_max is not None:
            filters.append(WikiChunk.grade <= grade_max)

        subject = metadata_filter.get("subject")
        if subject:
            filters.append(WikiChunk.subject == subject)

        topic = metadata_filter.get("topic")
        if topic:
            if isinstance(topic, list):
                filters.append(WikiChunk.topic.in_(topic))
            else:
                filters.append(WikiChunk.topic == topic)

        chunk_types = metadata_filter.get("content_types") or metadata_filter.get("chunk_types") or []
        if chunk_types:
            filters.append(WikiChunk.chunk_type.in_(chunk_types))

        if filters:
            return statement.where(and_(*filters))
        return statement

    def _to_retrieved_chunk(
        self,
        chunk: WikiChunk,
        score: float,
        retrieval_method: str,
    ) -> RetrievedChunk:
        return RetrievedChunk(
            id=chunk.id,
            chunk_id=chunk.chunk_id,
            title=chunk.title,
            section=chunk.section,
            content=chunk.content,
            subject=chunk.subject,
            subject_vn=chunk.subject_vn,
            grade=chunk.grade,
            topic=chunk.topic,
            document_id=chunk.document_id,
            source=chunk.source,
            chunk_type=chunk.chunk_type,
            has_formula=chunk.has_formula,
            length=chunk.length,
            chunk_index=chunk.chunk_index,
            score=score,
            retrieval_method=retrieval_method,
        )
