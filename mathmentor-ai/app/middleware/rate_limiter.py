"""Simple in-memory rate limiter for chat endpoints."""

import asyncio
import time
from dataclasses import dataclass
from uuid import UUID

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.config import Settings, get_settings
from app.core.security import AuthenticationError, decode_access_token
from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RateWindow:
    """Per-user fixed-window request counter."""

    count: int
    expires_at: float


class ChatRateLimitMiddleware(BaseHTTPMiddleware):
    """Limit authenticated chat requests per user in local process memory."""

    def __init__(self, app: ASGIApp, settings: Settings | None = None) -> None:
        super().__init__(app)
        self.settings = settings or get_settings()
        self._windows: dict[str, RateWindow] = {}
        self._concurrent_requests: dict[str, int] = {}
        self._lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next) -> Response:
        """Apply rate limits to `/api/v1/chat` routes only."""
        if not self._is_limited_path(request.url.path):
            return await call_next(request)

        user_id = self._extract_user_id(request)
        if user_id is None:
            return await call_next(request)

        decision = await self._try_acquire(user_id)
        if decision is not None:
            return decision

        try:
            return await call_next(request)
        finally:
            await self._release(user_id)

    def _is_limited_path(self, path: str) -> bool:
        return path == "/api/v1/chat" or path.startswith("/api/v1/chat/")

    def _extract_user_id(self, request: Request) -> str | None:
        authorization = request.headers.get("authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return None
        try:
            payload = decode_access_token(token, self.settings)
            return str(UUID(payload["sub"]))
        except (AuthenticationError, ValueError) as exc:
            logger.info(
                "rate_limit_token_rejected",
                stage="rate_limit",
                status="error",
                error=str(exc),
            )
            return None

    async def _try_acquire(self, user_id: str) -> JSONResponse | None:
        now = time.monotonic()
        async with self._lock:
            self._cleanup_expired(now)
            window = self._windows.get(user_id)
            if window is None:
                window = RateWindow(count=0, expires_at=now + 60)
                self._windows[user_id] = window

            if window.count >= self.settings.rate_limit_requests_per_minute:
                return self._too_many_requests(
                    "Rate limit exceeded.",
                    retry_after=max(1, int(window.expires_at - now)),
                )

            concurrent = self._concurrent_requests.get(user_id, 0)
            if concurrent >= self.settings.rate_limit_concurrent_sessions:
                return self._too_many_requests("Too many concurrent chat requests.")

            window.count += 1
            self._concurrent_requests[user_id] = concurrent + 1
        return None

    async def _release(self, user_id: str) -> None:
        async with self._lock:
            current = self._concurrent_requests.get(user_id, 0)
            if current <= 1:
                self._concurrent_requests.pop(user_id, None)
            else:
                self._concurrent_requests[user_id] = current - 1

    def _cleanup_expired(self, now: float) -> None:
        expired = [user_id for user_id, window in self._windows.items() if window.expires_at <= now]
        for user_id in expired:
            self._windows.pop(user_id, None)

    def _too_many_requests(self, detail: str, retry_after: int | None = None) -> JSONResponse:
        headers = {"Retry-After": str(retry_after)} if retry_after else None
        return JSONResponse(
            status_code=429,
            content={"detail": detail},
            headers=headers,
        )
