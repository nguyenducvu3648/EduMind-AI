"""Quick RAG query script — skip ingestion, query existing DB directly.

Usage:
    python -m scripts.query_rag "cách giải phương trình bậc 2"
"""

import asyncio
import sys
import time

from app.config import Settings, get_settings
from app.db.session import AsyncSessionLocal, create_engine
from app.db.models.wiki_chunk import WikiChunk
from app.rag.retriever import HybridRetriever
from app.rag.reranker import CrossEncoderReranker
from app.rag.types import RetrievedChunk
from app.wiki.embedding_service import BGEEmbeddingService


def print_results(
    query: str,
    semantic: list[RetrievedChunk],
    bm25: list[RetrievedChunk],
    fused: list[RetrievedChunk],
    reranked: list[RetrievedChunk],
) -> None:
    import json

    print("\n" + "=" * 80)
    print(f"🔎 Query: {query}")
    print(f"📊 Semantic results: {len(semantic)}  |  BM25 results: {len(bm25)}")
    print(f"🔀 After RRF fusion: {len(fused)}  |  After rerank: {len(reranked)}")
    print("=" * 80)

    for i, chunk in enumerate(reranked, 1):
        print(f"\n{'─' * 60}")
        print(f"  #{i}  score={chunk.score:.4f}  method={chunk.retrieval_method}")
        print(f"      title: {chunk.title}")
        if chunk.section:
            print(f"      section: {chunk.section}")
        print(f"      subject: {chunk.subject}")
        print(f"      grade: {chunk.grade}")
        print(f"\n      {chunk.content[:300]}...")
        print(f"{'─' * 60}\n")

    if not reranked:
        print("  (no results found)\n")


async def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else "cách giải phương trình bậc 2"
    settings = get_settings()

    print(f"🔌 Connecting to: {settings.database_url}")
    print("⬇  Loading embedding model (BAAI/bge-m3)...")
    embed_service = BGEEmbeddingService()
    print("⬇  Loading reranker (cross-encoder)...")
    reranker = CrossEncoderReranker()

    async with AsyncSessionLocal() as session:
        retriever = HybridRetriever(session, embedding_service=embed_service)

        # --- STEP 1: Check DB ---
        from sqlalchemy import select, func
        count_result = await session.execute(select(func.count()).select_from(WikiChunk))
        total = count_result.scalar() or 0
        print(f"\n📦 DB has {total} wiki chunks\n")

        if total == 0:
            print("❌ No data in wiki_chunks. Run seed first.")
            return

        # --- STEP 2: Run hybrid retrieval ---
        queries = [query]
        metadata_filter: dict = {}

        t0 = time.perf_counter()

        # Semantic search
        print("🔍 Semantic search (embedding)...")
        semantic = await retriever.semantic_search(queries, metadata_filter, top_k=20)

        # BM25 search
        print("🔍 BM25 full-text search (content)...")
        bm25 = await retriever.bm25_search(queries, metadata_filter, top_k=20)

        # RRF fusion (thủ công để debug)
        from app.rag.rrf import reciprocal_rank_fusion
        fused = reciprocal_rank_fusion([semantic, bm25])

        # Rerank
        print("🎯 Cross-encoder reranking...")
        reranked = await reranker.rerank(query, fused, top_k=5)

        elapsed = time.perf_counter() - t0

        print(f"\n⏱  Total: {elapsed:.2f}s")
        print_results(query, semantic, bm25, fused, reranked)


if __name__ == "__main__":
    asyncio.run(main())
