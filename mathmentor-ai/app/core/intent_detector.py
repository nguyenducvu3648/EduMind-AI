"""Rule-based math query intent detection."""

import re
from dataclasses import dataclass, field
from typing import Literal

QuestionType = Literal[
    "concept_explanation",
    "problem_solving",
    "hint_request",
    "review",
    "clarification",
]


@dataclass(frozen=True)
class QueryIntent:
    """Detected student intent and retrieval features."""

    question_type: QuestionType
    topic_tags: list[str] = field(default_factory=list)
    difficulty_estimate: float = 0.5
    math_entities: list[str] = field(default_factory=list)


class IntentDetector:
    """Detect query intent with deterministic, auditable rules."""

    TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
        "quadratic_equations": ("bậc hai", "quadratic", "delta", "discriminant", "parabol"),
        "linear_equations": ("bậc nhất", "linear", "first degree"),
        "trigonometry": ("sin", "cos", "tan", "lượng giác", "trigonometry"),
        "derivatives": ("đạo hàm", "derivative", "differentiate"),
        "integrals": ("tích phân", "integral", "antiderivative"),
        "vectors": ("vector", "vectơ", "dot product", "cross product"),
        "geometry": ("hình học", "triangle", "circle", "đường tròn", "tam giác"),
    }

    async def detect(self, query: str) -> QueryIntent:
        """Return intent classification and topic hints for a student query."""
        lower = query.lower()
        if any(token in lower for token in ("hint", "gợi ý", "đừng giải", "do not solve")):
            question_type: QuestionType = "hint_request"
        elif any(token in lower for token in ("review", "ôn", "recap", "tóm tắt")):
            question_type = "review"
        elif any(
            token in lower for token in ("why", "vì sao", "tại sao", "still confused", "chưa hiểu")
        ):
            question_type = "clarification"
        elif re.search(r"(solve|giải|tìm|calculate|compute|=)", lower):
            question_type = "problem_solving"
        else:
            question_type = "concept_explanation"

        topics = [
            topic
            for topic, keywords in self.TOPIC_KEYWORDS.items()
            if any(keyword in lower for keyword in keywords)
        ]
        entities = re.findall(r"\$\$.*?\$\$|\$(?!\$).*?\$(?!\$)", query, flags=re.DOTALL)
        difficulty = min(1.0, 0.35 + 0.1 * len(entities) + 0.05 * len(query.split()))
        return QueryIntent(
            question_type=question_type,
            topic_tags=topics,
            difficulty_estimate=difficulty,
            math_entities=entities,
        )
