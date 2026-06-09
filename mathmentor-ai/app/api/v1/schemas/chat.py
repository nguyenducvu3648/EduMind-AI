"""Chat API schemas reserved for Phase 5."""

from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Student chat request payload."""

    session_id: UUID | None = None
    message: str = Field(min_length=1, max_length=8000)


class ChunkReference(BaseModel):
    """Reference to a wiki chunk used as source context."""

    chunk_id: UUID
    article_title: str
    section_header: str | None = None


class ChatResponse(BaseModel):
    """Student chat response payload."""

    session_id: UUID
    message_id: UUID
    response: str
    teaching_strategy_used: str
    topics_covered: list[str]
    sources: list[ChunkReference]
    follow_up_suggestions: list[str]


class FeedbackRequest(BaseModel):
    """Feedback for a generated tutor message."""

    message_id: UUID
    rating: int = Field(ge=1, le=5)
    helpful: bool
    confusion_flag: bool = False
