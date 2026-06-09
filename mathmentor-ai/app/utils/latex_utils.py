"""LaTeX preservation and input validation helpers."""

import re

LATEX_INLINE_PATTERN = re.compile(r"\$(?!\$)(.+?)\$(?!\$)", re.DOTALL)
LATEX_BLOCK_PATTERN = re.compile(r"\$\$(.*?)\$\$", re.DOTALL)
UNSAFE_LATEX_PATTERN = re.compile(
    r"\\(?:write18|input|include|openout|read|catcode|csname|newwrite|immediate)\b",
    re.IGNORECASE,
)


class LatexValidationError(ValueError):
    """Raised when a text input contains malformed or unsafe LaTeX."""


def validate_safe_latex(text: str) -> None:
    """Validate that LaTeX snippets do not contain executable TeX patterns."""
    if UNSAFE_LATEX_PATTERN.search(text):
        raise LatexValidationError("Unsafe LaTeX command detected.")
    if text.count("$$") % 2 != 0:
        raise LatexValidationError("Unbalanced display LaTeX delimiters.")
    stripped_blocks = LATEX_BLOCK_PATTERN.sub("", text)
    if stripped_blocks.count("$") % 2 != 0:
        raise LatexValidationError("Unbalanced inline LaTeX delimiters.")


def extract_latex_expressions(text: str) -> list[str]:
    """Return all complete LaTeX expressions, preserving delimiters."""
    blocks = [f"$${match.group(1)}$$" for match in LATEX_BLOCK_PATTERN.finditer(text)]
    without_blocks = LATEX_BLOCK_PATTERN.sub("", text)
    inlines = [f"${match.group(1)}$" for match in LATEX_INLINE_PATTERN.finditer(without_blocks)]
    return blocks + inlines
