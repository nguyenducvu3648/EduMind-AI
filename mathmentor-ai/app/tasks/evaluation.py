"""Evaluation pipeline and scheduled tasks."""

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.db.models.evaluation import EvaluationRun
from app.db.models.interaction_log import InteractionLog
from app.db.models.session import Session
from app.db.session import AsyncSessionLocal
# Celery disabled — evaluation runs inline
# from app.tasks.celery_app import celery_app


@dataclass(frozen=True)
class RAGMetrics:
    """Basic RAG metrics snapshot."""

    sampled_interactions: int
    context_usage_rate: float


class EvaluationPipeline:
    """Compute lightweight offline evaluation metrics from persisted logs."""

    async def run_rag_evaluation(self, sample_size: int = 50) -> dict:
        """Compute RAG usage proxy metrics from recent interactions."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(InteractionLog).order_by(InteractionLog.created_at.desc()).limit(sample_size)
            )
            logs = list(result.scalars().all())
            context_used = sum(1 for log in logs if log.context_chunks_used)
            metrics = {
                "sample_size": len(logs),
                "context_usage_rate": context_used / len(logs) if logs else 1.0,
                "average_context_chunks": (
                    sum(len(log.context_chunks_used or []) for log in logs) / len(logs)
                    if logs
                    else 0.0
                ),
            }
            session.add(
                EvaluationRun(
                    run_type="rag_quality",
                    metrics=metrics,
                    sample_size=len(logs),
                    triggered_by="admin",
                )
            )
            await session.commit()
            return metrics

    async def run_response_quality_evaluation(self, sample_size: int = 50) -> dict:
        """Compute response quality proxy metrics."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(InteractionLog).order_by(InteractionLog.created_at.desc()).limit(sample_size)
            )
            logs = list(result.scalars().all())
            latex_valid = sum(
                1 for log in logs if "$" not in log.response or log.response.count("$") % 2 == 0
            )
            metrics = {
                "sample_size": len(logs),
                "latex_validity_rate": latex_valid / len(logs) if logs else 1.0,
                "average_latency_ms": (
                    sum(log.response_latency_ms or 0 for log in logs) / len(logs) if logs else 0
                ),
            }
            session.add(
                EvaluationRun(
                    run_type="response_quality",
                    metrics=metrics,
                    sample_size=len(logs),
                    triggered_by="celery",
                )
            )
            await session.commit()
            return metrics

    async def compute_personalization_metrics(self, days: int = 7) -> dict:
        """Compute recent personalization proxy metrics."""
        async with AsyncSessionLocal() as session:
            since = datetime.now(UTC) - timedelta(days=days)
            result = await session.execute(
                select(InteractionLog).where(InteractionLog.created_at >= since)
            )
            logs = list(result.scalars().all())
            strategy_count = len([log for log in logs if log.teaching_strategy])
            metrics = {
                "days": days,
                "interactions": len(logs),
                "strategy_assignment_rate": strategy_count / len(logs) if logs else 1.0,
            }
            session.add(
                EvaluationRun(
                    run_type="personalization",
                    metrics=metrics,
                    sample_size=len(logs),
                    triggered_by="celery",
                )
            )
            await session.commit()
            return metrics


async def run_scheduled_evaluation_task() -> dict:
    """Run scheduled response and personalization evaluations (inline)."""
    pipeline = EvaluationPipeline()
    quality = await pipeline.run_response_quality_evaluation()
    personalization = await pipeline.compute_personalization_metrics()
    return {"response_quality": quality, "personalization": personalization}


async def cleanup_expired_sessions_task() -> dict:
    """Mark inactive sessions as ended (inline)."""
    async with AsyncSessionLocal() as session:
        cutoff = datetime.now(UTC) - timedelta(hours=6)
        result = await session.execute(
            select(Session).where(Session.ended_at.is_(None), Session.started_at < cutoff)
        )
        sessions = list(result.scalars().all())
        for item in sessions:
            item.ended_at = datetime.now(UTC)
        await session.commit()
        return {"closed_sessions": len(sessions)}
