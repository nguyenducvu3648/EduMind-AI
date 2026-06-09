"""Wiki ingestion and LLM-Wiki article API schemas."""

from pydantic import BaseModel, Field


class WikiIngestRequest(BaseModel):
    """Admin request to ingest a markdown file or directory."""

    path: str = Field(min_length=1, max_length=1000)
    generate_embeddings: bool = True


class WikiIngestResponse(BaseModel):
    """Wiki ingestion result."""

    total_articles: int
    total_chunks: int
    errors: list[str]
    duration_ms: int


class WikiArticleCreate(BaseModel):
    """Create a new LLM-Wiki article."""

    slug: str = Field(min_length=1, max_length=255, pattern=r"^[a-z0-9_-]+$")
    title: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1)
    summary: str | None = None
    subject: str | None = None
    grade: int | None = Field(None, ge=10, le=12)
    difficulty: float | None = Field(None, ge=0.0, le=1.0)
    tags: list[str] | None = None
    concepts: list[str] | None = None
    has_examples: bool = False
    has_common_mistakes: bool = False
    has_formula: bool = False
    related_slugs: list[str] | None = None
    source: str | None = None
    is_published: bool = True


class WikiArticleUpdate(BaseModel):
    """Update an LLM-Wiki article (partial)."""

    title: str | None = None
    content: str | None = None
    summary: str | None = None
    subject: str | None = None
    grade: int | None = Field(None, ge=10, le=12)
    difficulty: float | None = Field(None, ge=0.0, le=1.0)
    tags: list[str] | None = None
    concepts: list[str] | None = None
    has_examples: bool | None = None
    has_common_mistakes: bool | None = None
    has_formula: bool | None = None
    related_slugs: list[str] | None = None
    source: str | None = None
    is_published: bool | None = None
