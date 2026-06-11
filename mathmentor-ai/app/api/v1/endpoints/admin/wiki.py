"""Admin wiki endpoints — both RAG ingestion and LLM-Wiki article management."""

import tempfile
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.wiki import WikiArticleCreate, WikiArticleUpdate, WikiIngestRequest, WikiIngestResponse
from app.db.models.wiki_article import WikiArticle
from app.db.session import get_db_session
from app.dependencies import get_embedding_service, verify_admin_api_key
from app.wiki.embedding_service import BGEEmbeddingService
from app.wiki.ingestion_pipeline import WikiIngestionPipeline
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(dependencies=[Depends(verify_admin_api_key)])


# ──────────────────────────────────────────────
# RAG Ingestion (existing)
# ──────────────────────────────────────────────

@router.post("/ingest", response_model=WikiIngestResponse)
async def ingest_wiki(
    payload: WikiIngestRequest,
    session: AsyncSession = Depends(get_db_session),
    embedding_service: BGEEmbeddingService = Depends(get_embedding_service),
) -> WikiIngestResponse:
    """Trigger synchronous wiki ingestion for a file or directory."""
    target = Path(payload.path).resolve()
    if not target.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Path not found.")
    pipeline = WikiIngestionPipeline(
        session,
        embedding_service=embedding_service if payload.generate_embeddings else None,
    )
    if target.is_file():
        chunk_ids = await pipeline.ingest_article(str(target))
        return WikiIngestResponse(total_articles=1, total_chunks=len(chunk_ids), errors=[], duration_ms=0)
    report = await pipeline.ingest_directory(str(target))
    return WikiIngestResponse(
        total_articles=report.total_articles,
        total_chunks=report.total_chunks,
        errors=report.errors,
        duration_ms=report.duration_ms,
    )


@router.post("/ingest/upload", response_model=WikiIngestResponse)
async def ingest_wiki_upload(
    files: list[UploadFile],
    session: AsyncSession = Depends(get_db_session),
    embedding_service: BGEEmbeddingService = Depends(get_embedding_service),
) -> WikiIngestResponse:
    """Upload and ingest one or more .md files from the browser."""
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files uploaded.")
    pipeline = WikiIngestionPipeline(
        session,
        embedding_service=embedding_service,
    )
    errors: list[str] = []
    total_chunks = 0
    article_count = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        for f in files:
            if not f.filename or not f.filename.endswith(".md"):
                errors.append(f"'{f.filename}': only .md files are supported")
                continue
            try:
                content = await f.read()
                filepath = Path(tmpdir) / f.filename
                filepath.write_bytes(content)
                chunk_ids = await pipeline.ingest_article(str(filepath))
                total_chunks += len(chunk_ids)
                article_count += 1
                logger.info(
                    "upload_ingest_ok",
                    filename=f.filename,
                    chunks=len(chunk_ids),
                )
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{f.filename}: {exc}")
                await session.rollback()
                logger.info(
                    "upload_ingest_failed",
                    filename=f.filename,
                    error=str(exc),
                )

    return WikiIngestResponse(
        total_articles=article_count,
        total_chunks=total_chunks,
        errors=errors,
        duration_ms=0,
    )


# ──────────────────────────────────────────────
# LLM-Wiki Article CRUD
# ──────────────────────────────────────────────

@router.get("/articles")
async def list_all_articles(
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    """List all LLM-Wiki articles (including unpublished)."""
    result = await session.execute(
        select(WikiArticle).order_by(WikiArticle.grade, WikiArticle.title)
    )
    return [
        {
            "id": str(a.id),
            "slug": a.slug,
            "title": a.title,
            "summary": a.summary,
            "subject": a.subject,
            "grade": a.grade,
            "is_published": a.is_published,
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        }
        for a in result.scalars().all()
    ]


@router.post("/articles", status_code=status.HTTP_201_CREATED)
async def create_wiki_article(
    payload: WikiArticleCreate,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Create a new LLM-Wiki article."""
    existing = await session.execute(
        select(WikiArticle).where(WikiArticle.slug == payload.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Article with slug '{payload.slug}' already exists.",
        )

    article = WikiArticle(
        slug=payload.slug,
        title=payload.title,
        content=payload.content,
        summary=payload.summary,
        subject=payload.subject,
        grade=payload.grade,
        difficulty=payload.difficulty,
        tags=payload.tags or [],
        concepts=payload.concepts or [],
        has_examples=payload.has_examples,
        has_common_mistakes=payload.has_common_mistakes,
        has_formula=payload.has_formula,
        related_slugs=payload.related_slugs or [],
        source=payload.source,
        is_published=payload.is_published,
    )
    session.add(article)
    await session.commit()
    await session.refresh(article)
    return {"id": str(article.id), "slug": article.slug, "title": article.title}


@router.patch("/articles/{article_id}")
async def update_wiki_article(
    article_id: UUID,
    payload: WikiArticleUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Update an LLM-Wiki article."""
    article = await session.get(WikiArticle, article_id)
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found.")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(article, field, value)

    await session.commit()
    await session.refresh(article)
    return {"id": str(article.id), "slug": article.slug, "title": article.title}
