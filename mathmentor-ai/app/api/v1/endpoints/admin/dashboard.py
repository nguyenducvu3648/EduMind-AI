"""Admin dashboard analytics endpoint."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.interaction_log import InteractionLog
from app.db.models.session import Session
from app.db.models.user import User, UserProfile
from app.db.models.wiki_chunk import WikiChunk
from app.db.session import get_db_session
from app.dependencies import verify_admin_api_key

router = APIRouter(dependencies=[Depends(verify_admin_api_key)])


@router.get("/stats")
async def get_dashboard_stats(
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Return aggregate learning analytics for the admin dashboard."""
    now = datetime.now(UTC)
    week_ago = now - timedelta(days=7)

    # --- User stats ---
    total_users = (
        await session.execute(select(func.count()).select_from(User))
    ).scalar() or 0
    new_users_7d = (
        await session.execute(
            select(func.count()).select_from(User).where(User.created_at >= week_ago)
        )
    ).scalar() or 0

    profiles = (await session.execute(select(UserProfile))).scalars().all()
    struggling = sum(
        1 for p in profiles if p.topic_mastery and any(v < 0.4 for v in p.topic_mastery.values())
    )
    active_learners = sum(
        1 for p in profiles if p.topic_mastery and len(p.topic_mastery) > 2
    )

    # --- Session stats ---
    total_sessions = (
        await session.execute(select(func.count()).select_from(Session))
    ).scalar() or 0
    active_sessions_7d = (
        await session.execute(
            select(func.count())
            .select_from(Session)
            .where(Session.started_at >= week_ago)
        )
    ).scalar() or 0

    # --- Interaction stats ---
    total_interactions = (
        await session.execute(select(func.count()).select_from(InteractionLog))
    ).scalar() or 0
    interactions_7d = (
        await session.execute(
            select(func.count())
            .select_from(InteractionLog)
            .where(InteractionLog.created_at >= week_ago)
        )
    ).scalar() or 0

    # --- Topic distribution (from InteractionLog topics_detected) ---
    topic_rows = await session.execute(
        select(InteractionLog.topics_detected)
        .where(InteractionLog.topics_detected.is_not(None))
    )
    topic_counts: dict[str, int] = {}
    for row in topic_rows:
        topics = row[0]
        if topics:
            for t in topics:
                topic_counts[t] = topic_counts.get(t, 0) + 1

    # Fallback: also count from UserProfile topic_mastery for additional topics
    for p in profiles:
        for topic in (p.topic_mastery or {}):
            # Only add if not already counted (wider coverage)
            if topic not in topic_counts:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

    # --- Strategy usage ---
    strategy_counts: dict[str, int] = {}
    strategies = await session.execute(
        select(InteractionLog.teaching_strategy)
        .where(InteractionLog.teaching_strategy.is_not(None))
    )
    for row in strategies:
        s = row[0]
        strategy_counts[s] = strategy_counts.get(s, 0) + 1

    # --- Daily interactions (last 7 days, zero-filled) ---
    seven_days_ago = now - timedelta(days=7)
    daily_rows = await session.execute(
        select(
            func.date_trunc("day", InteractionLog.created_at).label("day"),
            func.count().label("cnt"),
        )
        .where(InteractionLog.created_at >= seven_days_ago)
        .group_by(text("day"))
        .order_by(text("day"))
    )
    daily_map: dict[str, int] = {
        str(row.day.date()): row.cnt for row in daily_rows
    }
    # Zero-fill all 7 days
    daily_interactions = []
    for i in range(6, -1, -1):
        day = (now - timedelta(days=i)).date()
        date_str = str(day)
        daily_interactions.append({
            "date": date_str,
            "count": daily_map.get(date_str, 0),
        })

    # --- Weak topics (top 10) ---
    # Primary: from UserProfile.weak_topics (EMA-driven, mirrors real mastery < 0.4)
    weak_topic_counts: dict[str, int] = {}
    for p in profiles:
        for t in (p.weak_topics or []):
            weak_topic_counts[t] = weak_topic_counts.get(t, 0) + 1
    # Secondary: from interactions with low user_feedback (1-2)
    low_feedback_topics = await session.execute(
        select(InteractionLog.topics_detected)
        .where(
            InteractionLog.topics_detected.is_not(None),
            InteractionLog.user_feedback.is_not(None),
            InteractionLog.user_feedback <= 2,
        )
    )
    for row in low_feedback_topics:
        topics = row[0]
        if topics:
            for t in topics:
                weak_topic_counts[t] = weak_topic_counts.get(t, 0) + 1
    top_weak_topics = sorted(weak_topic_counts.items(), key=lambda x: -x[1])[:10]

    # --- Chunk stats ---
    total_chunks = (
        await session.execute(select(func.count()).select_from(WikiChunk))
    ).scalar() or 0
    with_emb = (
        await session.execute(
            select(func.count())
            .select_from(WikiChunk)
            .where(WikiChunk.embedding.is_not(None))
        )
    ).scalar() or 0

    return {
        "users": {
            "total": total_users,
            "new_7d": new_users_7d,
            "struggling": struggling,
            "active_learners": active_learners,
        },
        "sessions": {
            "total": total_sessions,
            "active_7d": active_sessions_7d,
        },
        "interactions": {
            "total": total_interactions,
            "last_7d": interactions_7d,
            "daily": daily_interactions,
        },
        "learning": {
            "topic_distribution": dict(
                sorted(topic_counts.items(), key=lambda x: -x[1])[:15]
            ),
            "strategy_usage": strategy_counts,
            "top_weak_topics": [
                {"topic": t, "count": c} for t, c in top_weak_topics
            ],
        },
        "knowledge_base": {
            "total_chunks": total_chunks,
            "with_embedding": with_emb,
        },
    }
