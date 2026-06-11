"""FastAPI dependency providers."""

from functools import lru_cache
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.core.orchestrator import MathTutorOrchestrator
from app.core.security import AuthenticationError, decode_access_token
from app.db.models.user import User
from app.db.session import get_db_session
from app.llm.openai_client import OpenAIClient
from app.rag.context_compressor import LaTeXSafeCompressor
from app.rag.reranker import CrossEncoderReranker
from app.rag.retriever import HybridRetriever
from app.wiki.embedding_service import BGEEmbeddingService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@lru_cache
def get_embedding_service() -> BGEEmbeddingService:
    """Return a process-local embedding service with lazy model loading."""
    return BGEEmbeddingService()


async def get_hybrid_retriever(
    session: AsyncSession = Depends(get_db_session),
    embedding_service: BGEEmbeddingService = Depends(get_embedding_service),
) -> HybridRetriever:
    """Return a request-scoped hybrid retriever."""
    return HybridRetriever(session, embedding_service)


@lru_cache
def get_reranker() -> CrossEncoderReranker:
    """Return a process-local cross-encoder reranker with lazy loading."""
    return CrossEncoderReranker()


@lru_cache
def get_context_compressor() -> LaTeXSafeCompressor:
    """Return a reusable context compressor."""
    return LaTeXSafeCompressor()


@lru_cache
def get_openai_client() -> OpenAIClient:
    """Return a process-local OpenAI client."""
    return OpenAIClient()


async def get_orchestrator(
    session: AsyncSession = Depends(get_db_session),
    retriever: HybridRetriever = Depends(get_hybrid_retriever),
    reranker: CrossEncoderReranker = Depends(get_reranker),
    compressor: LaTeXSafeCompressor = Depends(get_context_compressor),
    llm_client: OpenAIClient = Depends(get_openai_client),
) -> MathTutorOrchestrator:
    """Return the request-scoped tutor orchestrator."""
    return MathTutorOrchestrator(session, retriever, reranker, compressor, llm_client)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    token_override: str | None = None,
) -> User:
    """Resolve the authenticated user from a bearer token or override."""
    raw_token = token_override or token
    try:
        payload = decode_access_token(raw_token, settings)
        user_id = UUID(payload["sub"])
    except (AuthenticationError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
        ) from exc

    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    return user


async def verify_admin_api_key(
    request: Request,
    x_admin_api_key: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> None:
    """Validate admin access via API Key header or Bearer JWT with role='admin'."""
    # Method 1: API Key (for scripts / automation)
    expected = settings.admin_api_key.get_secret_value()
    if x_admin_api_key and x_admin_api_key == expected:
        return

    # Method 2: Bearer JWT with role='admin' (for the admin UI)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            payload = decode_access_token(token, settings)
            user_id = UUID(payload["sub"])
        except (AuthenticationError, ValueError):
            pass  # fall through to raise
        else:
            user = await session.get(User, user_id)
            if user is not None and user.role == "admin":
                return

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")


async def ensure_user_exists(user_id: UUID, session: AsyncSession) -> User:
    """Load a user by ID or raise a 404 error."""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user
