"""User and profile API schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Registration request payload."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    grade_level: int = Field(ge=10, le=12)


class UserRead(BaseModel):
    """Public user representation."""

    id: UUID
    email: EmailStr
    grade_level: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT login response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    """Access-token-only response."""

    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """JSON login request payload."""

    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh-token request payload."""

    refresh_token: str = Field(min_length=1)


class UserProfileRead(BaseModel):
    """Full personalized profile representation."""

    user_id: UUID
    topic_mastery: dict[str, float]
    concept_dependency_map: dict
    misconception_patterns: list[dict]
    learning_speed: float
    retention_strength: float
    error_recurrence_rate: float
    cognitive_load_tolerance: float
    response_preference: str
    hint_dependency_level: float
    step_by_step_preference: float
    weak_topics: list[str]
    strong_topics: list[str]
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    """User-controlled behavioral preference update payload."""

    response_preference: (
        Literal["short", "long", "explain_first", "solve_first", "balanced"] | None
    ) = None
    hint_dependency_level: float | None = Field(default=None, ge=0.0, le=1.0)
    step_by_step_preference: float | None = Field(default=None, ge=0.0, le=1.0)
