"""LaTeX-safe context compression."""

import re
import uuid

from app.rag.types import RetrievedChunk
from app.utils.latex_utils import (
    LATEX_BLOCK_PATTERN,
    LATEX_INLINE_PATTERN,
    extract_latex_expressions,
    validate_safe_latex,
)


class ContextCompressionError(ValueError):
    """Raised when context compression would corrupt mathematical notation."""


class LaTeXSafeCompressor:
    """Compress retrieved context while preserving complete LaTeX expressions."""

    LATEX_INLINE_PATTERN = LATEX_INLINE_PATTERN
    LATEX_BLOCK_PATTERN = LATEX_BLOCK_PATTERN

    def compress(
        self,
        chunks: list[RetrievedChunk],
        max_tokens: int = 2000,
        min_chunk_tokens: int = 50,
        query: str = "",
    ) -> str:
        """Return a compact markdown context bundle without truncating formulas."""
        if not chunks:
            return ""

        query_terms = self._terms(query)
        included: list[str] = []
        token_budget = max_tokens

        for chunk in chunks:
            protected, placeholders = self._protect_latex(chunk.content)
            sentences = self._rank_sentences(protected, query_terms)
            selected: list[str] = []
            selected_tokens = 0
            for sentence in sentences:
                count = self._count_tokens(sentence)
                if count == 0:
                    continue
                if selected and selected_tokens + count > token_budget:
                    continue
                if count > token_budget and selected:
                    continue
                selected.append(sentence)
                selected_tokens += count
                if selected_tokens >= token_budget:
                    break

            if selected_tokens < min_chunk_tokens and not selected:
                continue
            restored = self._restore_latex(" ".join(selected), placeholders).strip()
            if restored:
                header = f"### {chunk.title}"
                if chunk.section:
                    header = f"{header} / {chunk.section}"
                included.append(f"{header}\n{restored}")
                token_budget -= selected_tokens
            if token_budget <= 0:
                break

        output = "\n\n".join(included)
        if "__LATEX_" in output:
            raise ContextCompressionError("LaTeX placeholder leaked after compression.")
        validate_safe_latex(output)
        _ = extract_latex_expressions(output)
        return output

    def _protect_latex(self, text: str) -> tuple[str, dict[str, str]]:
        placeholders: dict[str, str] = {}

        def replace_block(match: re.Match[str]) -> str:
            placeholder = f"__LATEX_{uuid.uuid4().hex}__"
            placeholders[placeholder] = match.group(0)
            return placeholder

        protected = self.LATEX_BLOCK_PATTERN.sub(replace_block, text)
        protected = self.LATEX_INLINE_PATTERN.sub(replace_block, protected)
        return protected, placeholders

    def _restore_latex(self, text: str, placeholders: dict[str, str]) -> str:
        restored = text
        for placeholder, expression in placeholders.items():
            restored = restored.replace(placeholder, expression)
        return restored

    def _rank_sentences(self, text: str, query_terms: set[str]) -> list[str]:
        sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?。])\s+|\n+", text)]
        scored = []
        for index, sentence in enumerate(sentences):
            terms = self._terms(sentence)
            score = len(terms & query_terms) + (0.1 / (index + 1))
            if "__LATEX_" in sentence:
                score += 0.5
            scored.append((score, index, sentence))
        return [item[2] for item in sorted(scored, key=lambda item: (-item[0], item[1]))]

    def _terms(self, text: str) -> set[str]:
        return {term.lower() for term in re.findall(r"[\wÀ-ỹ]+", text, flags=re.UNICODE)}

    def _count_tokens(self, text: str) -> int:
        return len(re.findall(r"\S+", text))
