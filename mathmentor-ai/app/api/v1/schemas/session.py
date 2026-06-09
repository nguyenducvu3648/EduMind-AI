"""Session API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MessageRead(BaseModel):
    """One chat message in a session."""

    id: UUID
    query: str
    response: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionRead(BaseModel):
    """Chat session representation (list view)."""

    id: UUID
    user_id: UUID
    started_at: datetime
    ended_at: datetime | None
    message_count: int
    topics_covered: list[str]
    last_message: str | None = None

    model_config = {"from_attributes": True}


class SessionDetailRead(BaseModel):
    """Chat session with full message history."""

    id: UUID
    user_id: UUID
    started_at: datetime
    ended_at: datetime | None
    message_count: int
    topics_covered: list[str]
    messages: list[MessageRead]

    model_config = {"from_attributes": True}
