"""Tests for rule-based intent detection."""

from app.core.intent_detector import IntentDetector


async def test_intent_detector_identifies_quadratic_solving() -> None:
    intent = await IntentDetector().detect("Giải phương trình bậc hai $x^2 - 5x + 6 = 0$")

    assert intent.question_type == "problem_solving"
    assert "quadratic_equations" in intent.topic_tags
