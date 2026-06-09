"""User-memory update tasks — inline (no Celery)."""

from uuid import UUID

from app.config import get_settings
from app.db.session import AsyncSessionLocal
from app.memory.ema_updater import EMAUpdater, InteractionSignal


async def update_user_memory_task(user_id: str, interaction_signal: dict) -> dict:
    """Apply EMA memory updates for one interaction."""
    async with AsyncSessionLocal() as session:
        updater = EMAUpdater(alpha=get_settings().ema_alpha)
        profile = await updater.apply(
            session,
            InteractionSignal(
                user_id=UUID(user_id),
                topics=list(interaction_signal.get("topics") or []),
                user_feedback=interaction_signal.get("user_feedback"),
                hint_used=bool(interaction_signal.get("hint_used", False)),
                viewed_over_30s=bool(interaction_signal.get("viewed_over_30s", True)),
                clarification_followup=bool(
                    interaction_signal.get("clarification_followup", False)
                ),
            ),
        )
        return {"updated": profile is not None, "user_id": user_id}
