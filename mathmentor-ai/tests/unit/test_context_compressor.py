"""Tests for LaTeX-safe context compression."""

from uuid import uuid4

from app.rag.context_compressor import LaTeXSafeCompressor
from app.rag.types import RetrievedChunk


def test_context_compressor_preserves_latex_expression() -> None:
    chunk = RetrievedChunk(
        id=uuid4(),
        article_id="quadratic",
        article_title="Quadratic",
        section_header="Formula",
        content="The formula is $$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$. Use it.",
        content_type="definition",
        subject="Math",
        grade_min=10,
        grade_max=12,
        difficulty=0.4,
        score=1.0,
    )

    output = LaTeXSafeCompressor().compress([chunk], query="formula quadratic")

    assert "$$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$" in output
    assert "__LATEX_" not in output
