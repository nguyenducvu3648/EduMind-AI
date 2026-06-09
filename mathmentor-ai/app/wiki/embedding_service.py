"""Async embedding via OpenAI-compatible API (DeepSeek, OpenAI, etc.)."""

from collections.abc import Sequence

from openai import AsyncOpenAI

from app.config import Settings, get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class EmbeddingServiceError(RuntimeError):
    """Raised when embedding generation fails."""


class BGEEmbeddingService:
    """Generate embeddings via any OpenAI-compatible API.

    Uses embedding_api_key / embedding_base_url from settings if set,
    otherwise falls back to llm_api_key / llm_base_url.
    If no key at all, embedding is skipped silently.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client: AsyncOpenAI | None = None
        self._disabled = False

        # Try embedding-specific key, then fall back to LLM key
        api_key = (
            self.settings.embedding_api_key.get_secret_value()
            if self.settings.embedding_api_key
            else (
                self.settings.llm_api_key.get_secret_value()
                if self.settings.llm_api_key
                else ""
            )
        )
        base_url = self.settings.embedding_base_url or self.settings.llm_base_url

        if api_key:
            self._client = AsyncOpenAI(api_key=api_key, base_url=base_url,
                                       timeout=self.settings.llm_request_timeout)
        else:
            self._disabled = True
            logger.info("embedding_service_disabled", stage="embedding", reason="no_api_key")

    async def embed_text(self, text: str) -> list[float]:
        vectors = await self.embed_texts([text])
        return vectors[0]

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if self._disabled or self._client is None:
            return []
        cleaned = [text.strip() for text in texts if text and text.strip()]
        if not cleaned:
            return []
        try:
            response = await self._client.embeddings.create(
                model=self.settings.embedding_model, input=cleaned
            )
            sorted_data = sorted(response.data, key=lambda x: x.index)
            return [item.embedding for item in sorted_data]
        except Exception as exc:
            logger.info(
                "embedding_generation_failed", stage="embedding",
                model=self.settings.embedding_model, status="error", error=str(exc),
            )
            raise EmbeddingServiceError("Embedding generation failed.") from exc
