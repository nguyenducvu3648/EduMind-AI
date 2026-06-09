"""Pydantic validation for LLM-Wiki markdown frontmatter."""

from datetime import date

from pydantic import BaseModel, Field, field_validator


class WikiSchemaError(ValueError):
    """Raised when a wiki article does not satisfy the required schema."""


class WikiArticleMetadata(BaseModel):
    """Validated metadata inherited by all chunks from a wiki article."""

    title: str = Field(min_length=1, max_length=500)
    subject: str = "Toán"
    grade_range: tuple[int, int]
    difficulty: float = Field(ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    last_updated: date

    @field_validator("grade_range")
    @classmethod
    def validate_grade_range(cls, value: tuple[int, int]) -> tuple[int, int]:
        """Ensure article grades are high-school math grades in ascending order."""
        grade_min, grade_max = value
        if grade_min < 10 or grade_max > 12 or grade_min > grade_max:
            raise ValueError("grade_range must be within [10, 12] and ascending.")
        return value


def validate_metadata(raw_metadata: dict) -> WikiArticleMetadata:
    """Validate raw frontmatter and wrap Pydantic errors in a domain error."""
    try:
        return WikiArticleMetadata.model_validate(raw_metadata)
    except ValueError as exc:
        raise WikiSchemaError(str(exc)) from exc
