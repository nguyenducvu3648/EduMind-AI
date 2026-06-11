"""Embedding service using BAAI/bge-m3 (local, dim=1024) with API fallback.

Giữ nguyên logic cũ:
- Dùng embedding_api_key/embedding_base_url nếu có
- Fallback sang llm_api_key/llm_base_url nếu không
- Nếu không có key gì → disabled

Chỉ thay đổi: thử dùng local model BAAI/bge-m3 (1024-dim) trước khi gọi API.
Inference chạy sync trên main thread để tránh segfault.
"""

from collections.abc import Sequence

from openai import AsyncOpenAI

from app.config import Settings, get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class EmbeddingServiceError(RuntimeError):
    """Raised when embedding generation fails."""


class BGEEmbeddingService:
    """Generate embeddings — try local BAAI/bge-m3 first, then API."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client: AsyncOpenAI | None = None
        self._disabled = False
        self._local_model = None
        self._local_tokenizer = None

        # ── 1. Try loading local BAAI/bge-m3 (dim=1024, cached) ──
        try:
            from transformers import AutoModel, AutoTokenizer
            import torch
            self._local_tokenizer = AutoTokenizer.from_pretrained(
                "BAAI/bge-m3", local_files_only=True
            )
            self._local_model = AutoModel.from_pretrained(
                "BAAI/bge-m3", local_files_only=True
            )
            self._local_model.eval()
            logger.info("embedding_local_loaded", model="BAAI/bge-m3")
        except Exception as exc:
            logger.info("embedding_local_unavailable", error=str(exc))
            self._local_model = None

        # ── 2. API client (fallback) ──
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
            self._client = AsyncOpenAI(
                api_key=api_key, base_url=base_url,
                timeout=self.settings.llm_request_timeout,
            )
        else:
            self._disabled = True
            logger.info("embedding_service_disabled", reason="no_api_key")

    # ── Sync encode helper (runs on current thread) ──
    def _encode_local(self, texts: list[str]) -> list[list[float]]:
        import torch
        inputs = self._local_tokenizer(
            texts, padding=True, truncation=True, return_tensors="pt", max_length=512,
        )
        with torch.inference_mode():
            outputs = self._local_model(**inputs)
        mask = inputs["attention_mask"].unsqueeze(-1).expand(
            outputs.last_hidden_state.size()
        ).float()
        emb = (outputs.last_hidden_state * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
        emb = torch.nn.functional.normalize(emb, p=2, dim=1)
        return emb.tolist()

    async def embed_text(self, text: str) -> list[float]:
        vectors = await self.embed_texts([text])
        return vectors[0]

    async def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        cleaned = [t.strip() for t in texts if t and t.strip()]
        if not cleaned:
            return []

        # ── Local model ──
        if self._local_model is not None:
            return self._encode_local(cleaned)

        # ── API fallback ──
        if self._disabled or self._client is None:
            return []

        try:
            response = await self._client.embeddings.create(
                model=self.settings.embedding_model, input=cleaned
            )
            if not response.data:
                raise ValueError("No embedding data received")
            sorted_data = sorted(response.data, key=lambda x: x.index)
            return [item.embedding for item in sorted_data]
        except Exception as exc:
            logger.info(
                "embedding_generation_failed", stage="embedding",
                model=self.settings.embedding_model, status="error", error=str(exc),
            )
            raise EmbeddingServiceError("Embedding generation failed.") from exc
