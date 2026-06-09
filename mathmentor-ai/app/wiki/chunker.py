"""LaTeX-aware markdown chunking for wiki articles."""

import re
from dataclasses import dataclass
from pathlib import Path

import frontmatter

from app.utils.latex_utils import extract_latex_expressions, validate_safe_latex
from app.wiki.schema_validator import WikiArticleMetadata, validate_metadata

H2_PATTERN = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
H3_PATTERN = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class WikiChunkDraft:
    """Chunk representation before persistence and embedding."""

    article_id: str
    article_title: str
    section_header: str
    content: str
    content_type: str
    subject: str
    grade_min: int
    grade_max: int
    difficulty: float
    tags: list[str]
    concepts: list[str]
    skills: list[str]
    prerequisites: list[str]
    source_refs: list[str]
    token_count: int
    chunk_index: int


class MarkdownChunker:
    """Header-based markdown chunker that never splits inside LaTeX blocks."""

    max_section_tokens: int = 800
    min_chunk_tokens: int = 50

    def chunk(self, article_path: str) -> list[WikiChunkDraft]:
        """Parse, validate, and chunk one markdown wiki article."""
        path = Path(article_path)
        post = frontmatter.load(path)
        metadata = validate_metadata(dict(post.metadata))
        validate_safe_latex(post.content)

        sections = self._split_sections(post.content)
        drafts: list[WikiChunkDraft] = []
        for section_header, section_body in sections:
            for body in self._split_large_section(section_body):
                normalized = body.strip()
                if not normalized:
                    continue
                drafts.append(
                    self._build_draft(
                        article_id=path.stem,
                        metadata=metadata,
                        section_header=section_header,
                        content=normalized,
                        chunk_index=len(drafts),
                    )
                )

        return self._merge_small_chunks(drafts)

    def _split_sections(self, content: str) -> list[tuple[str, str]]:
        matches = list(H2_PATTERN.finditer(content))
        if not matches:
            return [("Article", content)]
        sections: list[tuple[str, str]] = []
        for index, match in enumerate(matches):
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
            sections.append((match.group(1).strip(), content[start:end]))
        return sections

    def _split_large_section(self, content: str) -> list[str]:
        if self._count_tokens(content) <= self.max_section_tokens:
            return [content]
        blocks = self._split_on_h3_outside_latex(content)
        return blocks if len(blocks) > 1 else [content]

    def _split_on_h3_outside_latex(self, content: str) -> list[str]:
        protected_ranges = self._latex_block_ranges(content)
        matches = [
            match
            for match in H3_PATTERN.finditer(content)
            if not any(start <= match.start() <= end for start, end in protected_ranges)
        ]
        if not matches:
            return [content]
        chunks: list[str] = []
        for index, match in enumerate(matches):
            start = match.start()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
            chunks.append(content[start:end])
        return chunks

    def _latex_block_ranges(self, content: str) -> list[tuple[int, int]]:
        return [match.span() for match in re.finditer(r"\$\$.*?\$\$", content, flags=re.DOTALL)]

    def _build_draft(
        self,
        article_id: str,
        metadata: WikiArticleMetadata,
        section_header: str,
        content: str,
        chunk_index: int,
    ) -> WikiChunkDraft:
        original_latex = extract_latex_expressions(content)
        validate_safe_latex(content)
        if any(expr not in content for expr in original_latex):
            raise ValueError("LaTeX expression was corrupted during chunking.")
        grade_min, grade_max = metadata.grade_range
        return WikiChunkDraft(
            article_id=article_id,
            article_title=metadata.title,
            section_header=section_header,
            content=content,
            content_type=self._content_type_for(section_header),
            subject=metadata.subject,
            grade_min=grade_min,
            grade_max=grade_max,
            difficulty=metadata.difficulty,
            tags=metadata.tags,
            concepts=metadata.concepts,
            skills=metadata.skills,
            prerequisites=metadata.prerequisites,
            source_refs=metadata.source_refs,
            token_count=self._count_tokens(content),
            chunk_index=chunk_index,
        )

    def _merge_small_chunks(self, drafts: list[WikiChunkDraft]) -> list[WikiChunkDraft]:
        if len(drafts) < 2:
            return drafts
        merged: list[WikiChunkDraft] = []
        pending: WikiChunkDraft | None = None
        for draft in drafts:
            if pending is None:
                pending = draft
                continue
            if pending.token_count < self.min_chunk_tokens:
                pending = WikiChunkDraft(
                    **{
                        **pending.__dict__,
                        "section_header": f"{pending.section_header} / {draft.section_header}",
                        "content": f"{pending.content}\n\n{draft.content}",
                        "token_count": pending.token_count + draft.token_count,
                    }
                )
            else:
                merged.append(pending)
                pending = draft
        if pending is not None:
            merged.append(pending)
        return [
            WikiChunkDraft(**{**draft.__dict__, "chunk_index": index})
            for index, draft in enumerate(merged)
        ]

    def _content_type_for(self, section_header: str) -> str:
        normalized = section_header.lower()
        if "example" in normalized or "ví dụ" in normalized:
            return "example"
        if "mistake" in normalized or "lỗi" in normalized:
            return "mistake"
        if "formula" in normalized or "công thức" in normalized:
            return "definition"
        return "concept"

    def _count_tokens(self, content: str) -> int:
        return len(re.findall(r"\S+", content))
