"""Tests for LaTeX validation helpers."""

import pytest

from app.utils.latex_utils import (
    LatexValidationError,
    extract_latex_expressions,
    validate_safe_latex,
)


def test_extract_latex_expressions_preserves_delimiters() -> None:
    text = "Inline $x^2$ and block $$x = \\frac{-b}{2a}$$."

    assert extract_latex_expressions(text) == ["$$x = \\frac{-b}{2a}$$", "$x^2$"]


def test_validate_safe_latex_rejects_unsafe_command() -> None:
    with pytest.raises(LatexValidationError):
        validate_safe_latex(r"$\input{secret}$")
