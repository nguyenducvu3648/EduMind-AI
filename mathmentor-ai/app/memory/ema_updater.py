"""EMA-based memory update logic."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.interaction_log import InteractionLog
from app.db.models.user import UserProfile
from app.memory.misconception_detector import MisconceptionDetector


@dataclass(frozen=True)
class InteractionSignal:
    """Signals extracted from one tutoring interaction."""

    user_id: UUID
    topics: list[str]
    user_feedback: int | None = None
    hint_used: bool = False
    viewed_over_30s: bool = True
    clarification_followup: bool = False


def update_mastery(old_value: float, signal: float, alpha: float = 0.35) -> float:
    """Apply exponential moving average update to a mastery score."""
    return max(0.0, min(1.0, alpha * signal + (1 - alpha) * old_value))


class EMAUpdater:
    """Apply memory updates to a user profile."""

    def __init__(
        self,
        alpha: float = 0.35,
        misconception_detector: MisconceptionDetector | None = None,
    ) -> None:
        self.alpha = alpha
        self.misconception_detector = misconception_detector or MisconceptionDetector()

    async def apply(self, session: AsyncSession, signal: InteractionSignal) -> UserProfile | None:
        """Persist profile updates driven by an interaction signal."""
        profile = await session.get(UserProfile, signal.user_id)
        if profile is None:
            return None

        correctness = 0.5 if signal.user_feedback is None else float(signal.user_feedback >= 4)
        hint_component = 0.0 if signal.hint_used else 1.0
        engagement = 1.0 if signal.viewed_over_30s else 0.0
        repetition = await self._repetition_frequency(session, signal.user_id, signal.topics)
        repetition_component = 0.0 if repetition >= 3 else 1.0
        confusion_component = 0.0 if signal.clarification_followup else 1.0
        mastery_signal = (
            correctness * 0.35
            + hint_component * 0.20
            + engagement * 0.15
            + repetition_component * 0.15
            + confusion_component * 0.15
        )

        topic_mastery = dict(profile.topic_mastery or {})
        for topic in signal.topics:
            old = float(topic_mastery.get(topic, 0.5))
            topic_mastery[topic] = update_mastery(old, mastery_signal, self.alpha)
        profile.topic_mastery = topic_mastery
        profile.weak_topics = sorted(
            [topic for topic, value in topic_mastery.items() if value < 0.4]
        )
        profile.strong_topics = sorted(
            [topic for topic, value in topic_mastery.items() if value > 0.75]
        )
        profile.hint_dependency_level = update_mastery(
            profile.hint_dependency_level,
            1.0 if signal.hint_used else 0.0,
            self.alpha,
        )
        profile.error_recurrence_rate = update_mastery(
            profile.error_recurrence_rate,
            1.0 if correctness < 0.5 else 0.0,
            self.alpha,
        )
        profile.misconception_patterns = self.misconception_detector.update_patterns(
            profile,
            signal.topics,
            correctness,
            repetition,
        )
        await session.commit()
        await session.refresh(profile)
        return profile

    async def _repetition_frequency(
        self,
        session: AsyncSession,
        user_id: UUID,
        topics: list[str],
    ) -> float:
        if not topics:
            return 0.0
        result = await session.execute(
            select(InteractionLog)
            .where(InteractionLog.user_id == user_id)
            .order_by(InteractionLog.created_at.desc())
            .limit(50)
        )
        logs = result.scalars().all()
        return float(sum(1 for log in logs if set(log.topics_detected or []).intersection(topics)))
