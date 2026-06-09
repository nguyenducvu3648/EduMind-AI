"""Public wiki endpoints — both RAG chunks and LLM-Wiki articles."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.models.wiki_article import WikiArticle
from app.db.models.wiki_chunk import WikiChunk
from app.db.session import get_db_session
from app.dependencies import get_current_user

router = APIRouter()


# ──────────────────────────────────────────────
# RAG Wiki Chunks (existing)
# ──────────────────────────────────────────────

@router.get("/chunks")
async def list_wiki_chunks(
    grade: int | None = Query(None),
    subject: str | None = Query(None),
    limit: int = Query(200, ge=1, le=5000),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    """List wiki chunks with optional filters."""
    stmt = select(WikiChunk).order_by(WikiChunk.grade, WikiChunk.title, WikiChunk.chunk_index)

    if grade is not None:
        stmt = stmt.where(WikiChunk.grade == grade)
    if subject is not None:
        stmt = stmt.where(WikiChunk.subject == subject)

    stmt = stmt.limit(limit)
    result = await session.execute(stmt)
    chunks = result.scalars().all()

    return [
        {
            "id": c.id,
            "chunk_id": c.chunk_id,
            "title": c.title,
            "content": c.content,
            "subject": c.subject,
            "subject_vn": c.subject_vn,
            "grade": c.grade,
            "topic": c.topic,
            "source": c.source,
            "chunk_type": c.chunk_type,
            "section": c.section,
            "has_formula": c.has_formula,
            "length": c.length,
        }
        for c in chunks
    ]


# ──────────────────────────────────────────────
# LLM-Wiki Articles
# ──────────────────────────────────────────────

@router.get("/articles")
async def list_wiki_articles(
    grade: int | None = Query(None),
    subject: str | None = Query(None),
    tag: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    """List published LLM-Wiki articles."""
    stmt = (
        select(WikiArticle)
        .where(WikiArticle.is_published == True)
        .order_by(WikiArticle.grade, WikiArticle.title)
    )

    if grade is not None:
        stmt = stmt.where(WikiArticle.grade == grade)
    if subject is not None:
        stmt = stmt.where(WikiArticle.subject == subject)
    if tag is not None:
        stmt = stmt.where(WikiArticle.tags.any(tag))

    stmt = stmt.limit(limit)
    result = await session.execute(stmt)
    articles = result.scalars().all()

    return [
        {
            "id": str(a.id),
            "slug": a.slug,
            "title": a.title,
            "summary": a.summary,
            "subject": a.subject,
            "grade": a.grade,
            "difficulty": a.difficulty,
            "tags": a.tags or [],
            "has_examples": a.has_examples,
            "has_common_mistakes": a.has_common_mistakes,
            "related_slugs": a.related_slugs or [],
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        }
        for a in articles
    ]


@router.get("/articles/{slug}")
async def get_wiki_article(
    slug: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get full content of one LLM-Wiki article."""
    result = await session.execute(
        select(WikiArticle).where(
            WikiArticle.slug == slug, WikiArticle.is_published == True
        )
    )
    article = result.scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found.")
    return {
        "id": str(article.id),
        "slug": article.slug,
        "title": article.title,
        "summary": article.summary,
        "content": article.content,
        "subject": article.subject,
        "grade": article.grade,
        "difficulty": article.difficulty,
        "tags": article.tags or [],
        "concepts": article.concepts or [],
        "has_examples": article.has_examples,
        "has_common_mistakes": article.has_common_mistakes,
        "has_formula": article.has_formula,
        "related_slugs": article.related_slugs or [],
        "source": article.source,
        "updated_at": article.updated_at.isoformat() if article.updated_at else None,
    }


@router.get("/articles/search")
async def search_wiki_articles(
    q: str = Query(min_length=1),
    grade: int | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    """Search LLM-Wiki articles by title/tags/concepts."""
    stmt = select(WikiArticle).where(WikiArticle.is_published == True)

    like = f"%{q.lower()}%"
    stmt = stmt.where(
        or_(
            WikiArticle.title.ilike(like),
            WikiArticle.summary.ilike(like),
            WikiArticle.tags.any(q),
            WikiArticle.concepts.any(q),
        )
    )

    if grade is not None:
        stmt = stmt.where(WikiArticle.grade == grade)

    stmt = stmt.order_by(WikiArticle.title).limit(limit)
    result = await session.execute(stmt)
    articles = result.scalars().all()

    return [
        {
            "id": str(a.id),
            "slug": a.slug,
            "title": a.title,
            "summary": a.summary,
            "subject": a.subject,
            "grade": a.grade,
            "tags": a.tags or [],
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        }
        for a in articles
    ]
