"""User state interpretation for personalization."""

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from app.core.pedagogy_selector import BloomLevel, TeachingStrategy
from app.db.models.session import Session
from app.db.models.user import UserProfile


@dataclass(frozen=True)
class SessionSummary:
    """Recent session features used for cognitive-load estimation."""

    message_count: int
    topics_covered: list[str]

    @classmethod
    def from_model(cls, session: Session) -> "SessionSummary":
        """Build a summary from a persisted session."""
        return cls(message_count=session.message_count, topics_covered=session.topics_covered or [])


@dataclass(frozen=True)
class UserStateSnapshot:
    """Request-time snapshot of a student's learning state."""

    user_id: UUID
    learner_type: Literal["struggling", "average", "advanced"]
    topic_context: dict[str, float]
    misconception_detected: list[str]
    cognitive_load_estimate: float
    recommended_strategy: TeachingStrategy
    bloom_target_level: BloomLevel
    weak_topics_relevant: list[str]
    scaffolding_depth: int
    hint_dependency_level: float


class UserStateInterpreter:
    """Infer learner state from profile, recent sessions, and detected query topics."""

    async def interpret(
        self,
        user_profile: UserProfile,
        recent_sessions: list[SessionSummary],
        current_query: str,
        detected_topics: list[str],
    ) -> UserStateSnapshot:
        """Return a personalization snapshot for the current request."""
        topic_context = {
            topic: float(user_profile.topic_mastery.get(topic, 0.5)) for topic in detected_topics
        }
        mastery_values = list(topic_context.values()) or [0.5]
        avg_mastery = sum(mastery_values) / len(mastery_values)
        learner_type: Literal["struggling", "average", "advanced"]
        if avg_mastery < 0.4:
            learner_type = "struggling"
        elif avg_mastery <= 0.7:
            learner_type = "average"
        else:
            learner_type = "advanced"

        session_load = min(1.0, sum(s.message_count for s in recent_sessions[:3]) / 60)
        cognitive_load = min(
            1.0,
            (
                user_profile.error_recurrence_rate * 0.4
                + user_profile.hint_dependency_level * 0.3
                + session_load * 0.3
            ),
        )
        misconceptions = self._active_misconceptions(
            user_profile.misconception_patterns,
            current_query,
            detected_topics,
        )
        weak_relevant = [
            topic for topic in detected_topics if topic in (user_profile.weak_topics or [])
        ]
        strategy = self._initial_strategy(learner_type, cognitive_load, bool(misconceptions))
        bloom = self._bloom(learner_type, avg_mastery)
        scaffolding = self._scaffolding(learner_type, cognitive_load)
        return UserStateSnapshot(
            user_id=user_profile.user_id,
            learner_type=learner_type,
            topic_context=topic_context,
            misconception_detected=misconceptions,
            cognitive_load_estimate=cognitive_load,
            recommended_strategy=strategy,
            bloom_target_level=bloom,
            weak_topics_relevant=weak_relevant,
            scaffolding_depth=scaffolding,
            hint_dependency_level=user_profile.hint_dependency_level,
        )

    def _active_misconceptions(
        self,
        patterns: list[dict],
        query: str,
        topics: list[str],
    ) -> list[str]:
        query_lower = query.lower()
        active = []
        for pattern in patterns or []:
            topic = str(pattern.get("topic", ""))
            label = str(pattern.get("label") or pattern.get("description") or topic)
            if topic in topics or (topic and topic.lower() in query_lower):
                active.append(label)
        return active

    def _initial_strategy(
        self,
        learner_type: str,
        cognitive_load: float,
        has_misconception: bool,
    ) -> TeachingStrategy:
        if cognitive_load > 0.8:
            return TeachingStrategy.DIRECT_EXPLANATION
        if has_misconception:
            return TeachingStrategy.STEP_BY_STEP
        if learner_type == "struggling":
            return TeachingStrategy.STEP_BY_STEP
        if learner_type == "advanced":
            return TeachingStrategy.SOCRATIC
        return TeachingStrategy.WORKED_EXAMPLE

    def _bloom(self, learner_type: str, mastery: float) -> BloomLevel:
        if learner_type == "struggling":
            return BloomLevel.REMEMBER if mastery < 0.25 else BloomLevel.UNDERSTAND
        if learner_type == "average":
            return BloomLevel.APPLY if mastery < 0.6 else BloomLevel.ANALYZE
        return BloomLevel.EVALUATE if mastery < 0.85 else BloomLevel.CREATE

    def _scaffolding(self, learner_type: str, cognitive_load: float) -> int:
        base = {"struggling": 4, "average": 3, "advanced": 2}.get(learner_type, 3)
        if cognitive_load > 0.7:
            base += 1
        return max(1, min(5, base))
