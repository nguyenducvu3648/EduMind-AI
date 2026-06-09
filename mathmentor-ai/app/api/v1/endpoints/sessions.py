"""Session history endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.session import MessageRead, SessionDetailRead, SessionRead
from app.db.models.interaction_log import InteractionLog
from app.db.models.session import Session
from app.db.models.user import User
from app.db.session import get_db_session
from app.dependencies import get_current_user

router = APIRouter()


@router.get("", response_model=list[SessionRead])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[SessionRead]:
    """List recent chat sessions with a preview of the last message."""
    result = await session.execute(
        select(Session)
        .where(Session.user_id == current_user.id)
        .order_by(Session.started_at.desc())
        .limit(50)
    )
    sessions = list(result.scalars().all())

    results: list[SessionRead] = []
    for s in sessions:
        # Lấy message cuối cùng để làm preview
        msg_result = await session.execute(
            select(InteractionLog)
            .where(InteractionLog.session_id == s.id)
            .order_by(InteractionLog.created_at.desc())
            .limit(1)
        )
        last_msg = msg_result.scalar_one_or_none()
        last_text = last_msg.query[:120] if last_msg else None
        results.append(
            SessionRead(
                id=s.id,
                user_id=s.user_id,
                started_at=s.started_at,
                ended_at=s.ended_at,
                message_count=s.message_count,
                topics_covered=s.topics_covered or [],
                last_message=last_text,
            )
        )
    return results


@router.get("/{session_id}", response_model=SessionRead)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> Session:
    """Return one chat session metadata."""
    session = await db_session.get(Session, session_id)
    if session is None or session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    return session


@router.get("/{session_id}/messages", response_model=SessionDetailRead)
async def get_session_messages(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db_session: AsyncSession = Depends(get_db_session),
) -> SessionDetailRead:
    """Return full message history for a session (like ChatGPT sidebar)."""
    session = await db_session.get(Session, session_id)
    if session is None or session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    result = await db_session.execute(
        select(InteractionLog)
        .where(InteractionLog.session_id == session_id)
        .order_by(InteractionLog.created_at.asc())
    )
    messages = [
        MessageRead(
            id=msg.id,
            query=msg.query,
            response=msg.response,
            created_at=msg.created_at,
        )
        for msg in result.scalars().all()
    ]

    return SessionDetailRead(
        id=session.id,
        user_id=session.user_id,
        started_at=session.started_at,
        ended_at=session.ended_at,
        message_count=session.message_count,
        topics_covered=session.topics_covered or [],
        messages=messages,
    )
