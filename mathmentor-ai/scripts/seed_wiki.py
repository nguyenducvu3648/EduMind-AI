"""Seed wiki content through the ingestion pipeline."""

import asyncio
from pathlib import Path

from app.db.session import AsyncSessionLocal
from app.utils.logging import get_logger
from app.wiki.embedding_service import BGEEmbeddingService
from app.wiki.ingestion_pipeline import WikiIngestionPipeline

logger = get_logger(__name__)


async def main() -> None:
    """Ingest bundled wiki markdown with embeddings."""
    async with AsyncSessionLocal() as session:
        report = await WikiIngestionPipeline(
            session,
            embedding_service=BGEEmbeddingService(),
        ).ingest_directory(str(Path("wiki_content")))
        logger.info("seed_wiki_completed", stage="wiki_ingestion", report=report.__dict__)


if __name__ == "__main__":
    asyncio.run(main())
