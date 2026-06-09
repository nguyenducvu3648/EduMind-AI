"""Evaluation API schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class EvaluationRunRequest(BaseModel):
    """Admin request to run an evaluation pipeline."""

    run_type: Literal["rag_quality", "response_quality", "personalization"]
    sample_size: int = Field(default=50, ge=1, le=1000)
