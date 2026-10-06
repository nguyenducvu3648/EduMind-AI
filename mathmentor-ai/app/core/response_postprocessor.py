"""LLM response validation and safety post-processing."""

import re

from app.utils.latex_utils import LatexValidationError, validate_safe_latex

LATEX_BLOCK_RE = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)
LATEX_INLINE_RE = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", re.DOTALL)

# Pattern for duplicate math operators inside LaTeX content
REPEATED_OP_RE = re.compile(r"(\^|\_|\=)\1+")  # ^^ -> ^, __ -> _, == -> =
# Pattern for double-wrapped braces (LLM hallucination): {{a}} -> {a}
DOUBLE_OPEN_BRACE_RE = re.compile(r"\{\{(.+?)\}\}")


def _normalize_latex_content(content: str) -> str:
    """Normalize LaTeX content by collapsing whitespace for comparison."""
    return re.sub(r"\s+", " ", content).strip()


# ── Deduplicate consecutive identical formulas ──────────────────────────────


def _dedup_latex_blocks(text: str) -> str:
    """Remove consecutive identical block LaTeX ($$...$$ $$...$$ -> $$...$$)."""
    matches = list(LATEX_BLOCK_RE.finditer(text))
    if not matches:
        return text
    result: list[str] = []
    prev_end = 0
    prev_norm = None
    for i, m in enumerate(matches):
        norm = _normalize_latex_content(m.group(1))
        is_adjacent = i > 0 and not text[prev_end : m.start()].strip()
        if i > 0 and norm and is_adjacent and norm == prev_norm:
            prev_end = m.end()
            continue
        result.append(text[prev_end : m.end()] if i > 0 else text[: m.end()])
        prev_end = m.end()
        prev_norm = norm
    result.append(text[prev_end:])
    return "".join(result)


def _dedup_inline(text: str) -> str:
    """Remove consecutive identical inline LaTeX ($...$ $...$ -> $...$)."""
    matches = list(LATEX_INLINE_RE.finditer(text))
    if not matches:
        return text
    result: list[str] = []
    prev_end = 0
    prev_norm = None
    for i, m in enumerate(matches):
        norm = _normalize_latex_content(m.group(1))
        is_adjacent = i > 0 and not text[prev_end : m.start()].strip()
        if i > 0 and norm and is_adjacent and norm == prev_norm:
            prev_end = m.end()
            continue
        result.append(text[prev_end : m.end()] if i > 0 else text[: m.end()])
        prev_end = m.end()
        prev_norm = norm
    result.append(text[prev_end:])
    return "".join(result)


# ── Fix duplicate operators/braces inside LaTeX math ────────────────────────


def _dedup_braces(content: str) -> str:
    """Collapse double-wrapped braces: {{a}} -> {a} (applied repeatedly)."""
    prev = None
    c = content
    while c != prev:
        prev = c
        c = DOUBLE_OPEN_BRACE_RE.sub(r"{\1}", c)
    return c


def _dedup_operators(content: str) -> str:
    """Collapse duplicate operators: ^^ -> ^, __ -> _, == -> =."""
    return REPEATED_OP_RE.sub(r"\1", content)


def _fix_inside_latex(text: str) -> str:
    """Fix duplicate operators and braces inside $$...$$ and $...$."""
    def fix_block(m: re.Match) -> str:
        c = m.group(1)
        c = _dedup_operators(c)
        c = _dedup_braces(c)
        return "$$" + c + "$$"

    def fix_inline(m: re.Match) -> str:
        c = m.group(1)
        c = _dedup_operators(c)
        c = _dedup_braces(c)
        return "$" + c + "$"

    text = LATEX_BLOCK_RE.sub(fix_block, text)
    text = LATEX_INLINE_RE.sub(fix_inline, text)
    return text


# ── Main processor class ────────────────────────────────────────────────────


class ResponsePostprocessor:
    """Validate, deduplicate, and normalize tutor responses.

    Fixes common LLM LaTeX errors:
      - Consecutive identical formulas: $$x^2$$ $$x^2$$ -> $$x^2$$
      - Duplicate operators inside math: $x^^2$ -> $x^2$
      - Duplicate braces inside math: ``\frac{{a}}{{b}}`` -> ``\frac{a}{b}``
    """

    def process(self, response: str) -> str:
        """Return a safe, deduplicated, normalized markdown response."""
        cleaned = response.strip()
        cleaned = re.sub(
            r"<script.*?>.*?</script>", "", cleaned,
            flags=re.IGNORECASE | re.DOTALL,
        )
        # Step 1: Deduplicate consecutive identical LaTeX blocks/inline
        cleaned = _dedup_latex_blocks(cleaned)
        cleaned = _dedup_inline(cleaned)
        # Step 2: Fix duplicate operators/braces inside math mode
        cleaned = _fix_inside_latex(cleaned)
        # Step 3: Validate & repair balanced delimiters
        try:
            validate_safe_latex(cleaned)
        except LatexValidationError:
            cleaned = self._repair_unbalanced_dollars(cleaned)
            validate_safe_latex(cleaned)
        return cleaned

    def _repair_unbalanced_dollars(self, response: str) -> str:
        if response.count("$$") % 2 != 0:
            response += "$$"
        without_blocks = re.sub(r"\$\$.*?\$\$", "", response, flags=re.DOTALL)
        if without_blocks.count("$") % 2 != 0:
            response += "$"
        return response
