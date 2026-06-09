"""Pedagogy strategy selection."""

from enum import StrEnum
from typing import Any


class TeachingStrategy(StrEnum):
    """Supported tutoring strategies."""

    SOCRATIC = "socratic"
    STEP_BY_STEP = "step_by_step"
    DIRECT_EXPLANATION = "direct"
    HINT_FIRST = "hint_first"
    WORKED_EXAMPLE = "worked_example"
    METACOGNITIVE = "metacognitive"


class BloomLevel(StrEnum):
    """Bloom taxonomy target levels."""

    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class PedagogySelector:
    """Select strategy, Bloom target, and scaffolding from learner state and intent."""

    def select(self, user_state: Any, intent: Any) -> TeachingStrategy:
        """Choose a teaching strategy with misconception and load overrides."""
        if user_state.cognitive_load_estimate > 0.8:
            return TeachingStrategy.DIRECT_EXPLANATION
        if user_state.misconception_detected:
            return TeachingStrategy.STEP_BY_STEP

        intent_name = getattr(intent, "question_type", str(intent))
        hint_dependent = getattr(user_state, "hint_dependency_level", 0.5) > 0.6
        key = (user_state.learner_type, intent_name, hint_dependent)
        matrix: dict[tuple[str, str, bool | None], TeachingStrategy] = {
            ("struggling", "problem_solving", True): TeachingStrategy.HINT_FIRST,
            ("struggling", "problem_solving", False): TeachingStrategy.STEP_BY_STEP,
            ("struggling", "concept_explanation", None): TeachingStrategy.DIRECT_EXPLANATION,
            ("average", "problem_solving", None): TeachingStrategy.WORKED_EXAMPLE,
            ("average", "concept_explanation", None): TeachingStrategy.SOCRATIC,
            ("advanced", "problem_solving", None): TeachingStrategy.SOCRATIC,
            ("advanced", "concept_explanation", None): TeachingStrategy.METACOGNITIVE,
        }
        return (
            matrix.get(key)
            or matrix.get((user_state.learner_type, intent_name, None))
            or TeachingStrategy.DIRECT_EXPLANATION
        )

    def get_bloom_target(self, user_state: Any) -> BloomLevel:
        """Map learner type and mastery to a Bloom target level."""
        mastery_values = list(user_state.topic_context.values())
        mastery = sum(mastery_values) / len(mastery_values) if mastery_values else 0.5
        if user_state.learner_type == "struggling":
            return BloomLevel.REMEMBER if mastery < 0.25 else BloomLevel.UNDERSTAND
        if user_state.learner_type == "average":
            return BloomLevel.APPLY if mastery < 0.6 else BloomLevel.ANALYZE
        return BloomLevel.EVALUATE if mastery < 0.85 else BloomLevel.CREATE

    def get_scaffolding_depth(self, user_state: Any) -> int:
        """Return scaffolding depth from 1 to 5."""
        base = {"struggling": 4, "average": 3, "advanced": 2}.get(user_state.learner_type, 3)
        if user_state.cognitive_load_estimate > 0.7:
            base += 1
        if user_state.cognitive_load_estimate < 0.3:
            base -= 1
        return max(1, min(5, base))
