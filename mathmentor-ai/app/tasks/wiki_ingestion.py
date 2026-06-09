"""Wiki ingestion tasks — inline (no Celery)."""

from app.db.session import AsyncSessionLocal
from app.wiki.embedding_service import BGEEmbeddingService
from app.wiki.ingestion_pipeline import WikiIngestionPipeline


async def batch_ingest_wiki_task(directory: str) -> dict:
    """Ingest a wiki directory with embeddings."""
    async with AsyncSessionLocal() as session:
        report = await WikiIngestionPipeline(
            session,
            embedding_service=BGEEmbeddingService(),
        ).ingest_directory(directory)
        return {
            "total_articles": report.total_articles,
            "total_chunks": report.total_chunks,
            "errors": report.errors,
            "duration_ms": report.duration_ms,
        }
