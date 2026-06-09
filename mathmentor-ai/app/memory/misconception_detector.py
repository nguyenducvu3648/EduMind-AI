"""Misconception detection from interaction signals."""

from datetime import UTC, datetime

from app.db.models.user import UserProfile


class MisconceptionDetector:
    """Detect recurring low-correctness patterns per topic."""

    def update_patterns(
        self,
        profile: UserProfile,
        topics: list[str],
        correctness: float,
        repetition_frequency: float,
    ) -> list[dict]:
        """Return updated misconception patterns for a profile."""
        patterns = list(profile.misconception_patterns or [])
        if correctness >= 0.5 or repetition_frequency < 3:
            return patterns

        now = datetime.now(UTC).isoformat()
        for topic in topics:
            existing = next((item for item in patterns if item.get("topic") == topic), None)
            if existing:
                existing["frequency"] = int(existing.get("frequency", 1)) + 1
                existing["last_seen"] = now
            else:
                patterns.append(
                    {
                        "topic": topic,
                        "label": f"recurring_confusion:{topic}",
                        "frequency": 1,
                        "last_seen": now,
                    }
                )
        return patterns
