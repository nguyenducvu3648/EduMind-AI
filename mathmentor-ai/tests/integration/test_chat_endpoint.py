"""Chat endpoint wiring tests."""

from types import SimpleNamespace
from uuid import uuid4

from httpx import ASGITransport, AsyncClient

from app.db.models.user import User
from app.dependencies import get_current_user, get_orchestrator
from app.main import create_app
from app.rag.types import RetrievedChunk


class FakeOrchestrator:
    """Small orchestrator double for route wiring."""

    async def answer(self, user: User, message: str, session_id):
        _ = (user, message, session_id)
        chunk_id = uuid4()
        return SimpleNamespace(
            session_id=uuid4(),
            message_id=uuid4(),
            response="Use $\\Delta = b^2 - 4ac$.",
            teaching_strategy_used="step_by_step",
            topics_covered=["quadratic_equations"],
            sources=[
                RetrievedChunk(
                    id=chunk_id,
                    article_id="quadratic",
                    article_title="Quadratic Equations",
                    section_header="Formula",
                    content="content",
                    content_type="definition",
                    subject="Math",
                    grade_min=10,
                    grade_max=12,
                    difficulty=0.4,
                )
            ],
            follow_up_suggestions=["Can we solve another quadratic problem?"],
        )


async def test_chat_endpoint_uses_orchestrator_dependency() -> None:
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: User(
        id=uuid4(),
        email="student@example.com",
        hashed_password="hash",
        grade_level=10,
    )
    app.dependency_overrides[get_orchestrator] = lambda: FakeOrchestrator()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            json={"message": "Giải phương trình bậc hai"},
            headers={"Authorization": "Bearer test"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["teaching_strategy_used"] == "step_by_step"
    assert payload["sources"][0]["article_title"] == "Quadratic Equations"
