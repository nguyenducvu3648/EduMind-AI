"""Tests for markdown wiki chunking."""

from pathlib import Path

from app.wiki.chunker import MarkdownChunker


def test_chunker_preserves_latex_blocks() -> None:
    fixture = Path("wiki_content/grade_10/algebra/quadratic_equations.md")

    chunks = MarkdownChunker().chunk(str(fixture))

    assert chunks
    joined = "\n".join(chunk.content for chunk in chunks)
    assert "$$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$" in joined
    assert all(chunk.grade_min == 10 and chunk.grade_max == 12 for chunk in chunks)
