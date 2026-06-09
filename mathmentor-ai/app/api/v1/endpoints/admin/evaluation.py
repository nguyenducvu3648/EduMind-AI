"""Admin evaluation endpoints."""

from fastapi import APIRouter, Depends

from app.api.v1.schemas.evaluation import EvaluationRunRequest
from app.dependencies import verify_admin_api_key
from app.tasks.evaluation import EvaluationPipeline
from app.utils.logging import get_logger

router = APIRouter(dependencies=[Depends(verify_admin_api_key)])
logger = get_logger(__name__)


@router.post("/run")
async def run_evaluation(payload: EvaluationRunRequest) -> dict:
    """Run an evaluation pipeline and return computed metrics."""
    logger.info(
        "admin_evaluation_triggered",
        stage="evaluation",
        status="started",
        run_type=payload.run_type,
        sample_size=payload.sample_size,
    )
    pipeline = EvaluationPipeline()
    if payload.run_type == "rag_quality":
        metrics = await pipeline.run_rag_evaluation(payload.sample_size)
    elif payload.run_type == "response_quality":
        metrics = await pipeline.run_response_quality_evaluation(payload.sample_size)
    else:
        metrics = await pipeline.compute_personalization_metrics()

    logger.info(
        "admin_evaluation_completed",
        stage="evaluation",
        status="success",
        run_type=payload.run_type,
        metrics=metrics,
    )
    return metrics
