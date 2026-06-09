"""Chat endpoints wired to the full tutor orchestrator."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.chat import ChatRequest, ChatResponse, ChunkReference, FeedbackRequest
from app.core.orchestrator import MathTutorOrchestrator
from app.db.models.interaction_log import InteractionLog
from app.db.models.user import User
from app.db.session import get_db_session
from app.dependencies import get_current_user, get_orchestrator
from app.memory.ema_updater import EMAUpdater, InteractionSignal

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    orchestrator: MathTutorOrchestrator = Depends(get_orchestrator),
) -> ChatResponse:
    """Run the full MathMentor AI tutoring pipeline."""
    result = await orchestrator.answer(current_user, payload.message, payload.session_id)
    return ChatResponse(
        session_id=result.session_id,
        message_id=result.message_id,
        response=result.response,
        teaching_strategy_used=result.teaching_strategy_used,
        topics_covered=result.topics_covered,
        sources=[
            ChunkReference(
                chunk_id=chunk.id,
                article_title=chunk.title,
                section_header=chunk.section,
            )
            for chunk in result.sources
        ],
        follow_up_suggestions=result.follow_up_suggestions,
    )


@router.get("/stream")
async def chat_stream(
    message: str = Query(min_length=1, max_length=8000),
    session_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    orchestrator: MathTutorOrchestrator = Depends(get_orchestrator),
) -> StreamingResponse:
    """Stream a MathMentor response with Server-Sent Events."""
    return StreamingResponse(
        orchestrator.stream_answer(current_user, message, session_id),
        media_type="text/event-stream",
    )


@router.post("/feedback", status_code=status.HTTP_204_NO_CONTENT)
async def submit_feedback(
    payload: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    """Persist message feedback and update user memory."""
    log = await session.get(InteractionLog, payload.message_id)
    if log is None or log.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")
    log.user_feedback = payload.rating
    await session.commit()
    updater = EMAUpdater()
    await updater.apply(
        session,
        InteractionSignal(
            user_id=current_user.id,
            topics=log.topics_detected or [],
            user_feedback=payload.rating,
            hint_used=log.hint_used,
            viewed_over_30s=payload.helpful,
            clarification_followup=payload.confusion_flag,
        ),
    )
