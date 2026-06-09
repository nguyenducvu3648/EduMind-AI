"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.api.v1.router import router as api_v1_router
from app.config import get_settings
from app.middleware.rate_limiter import ChatRateLimitMiddleware
from app.utils.logging import configure_logging


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Application lifespan hook."""
    configure_logging()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Admin-Api-Key"],
    )
    app.add_middleware(ChatRateLimitMiddleware, settings=settings)
    app.include_router(api_v1_router)
    app.mount("/metrics", make_asgi_app())

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        """Return a lightweight service health response."""
        return {"status": "ok", "service": settings.app_name}

    return app


app = create_app()


def start() -> None:
    """Entry point for `python -m app.main` or `start` CLI."""
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start()
