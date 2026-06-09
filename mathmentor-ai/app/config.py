"""Environment-driven application settings."""

from functools import lru_cache
from typing import Annotated

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "MathMentor AI"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://mathmentor:mathmentor@localhost:5432/mathmentor"
    db_pool_size: int = 20
    db_max_overflow: int = 40
    redis_url: str = ""
    celery_broker_url: str = ""
    celery_result_backend: str = ""

    secret_key: SecretStr = SecretStr("dev-secret-change-me")
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"
    rate_limit_requests_per_minute: int = 60
    rate_limit_concurrent_sessions: int = 10
    cors_allow_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )
    admin_api_key: SecretStr = SecretStr("dev-admin-key")

    # OpenAI-compatible LLM provider (OpenAI, DeepSeek, Groq, Together, v.v.)
    llm_api_key: SecretStr | None = None
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-chat"
    llm_max_tokens: int = 2000
    llm_temperature: float = 0.3
    llm_request_timeout: float = 30.0
    llm_max_retries: int = 2

    # Embedding via OpenAI-compatible API (same provider or different)
    embedding_api_key: SecretStr | None = Field(default=None)
    embedding_base_url: str = ""
    embedding_model: str = "text-embedding-3-small"

    # Reranker via chat model (same LLM provider)
    reranker_model: str = Field(default="BAAI/bge-reranker-base")
    rag_top_k_semantic: int = 8
    rag_top_k_bm25: int = 8
    rag_final_top_k: int = 3
    max_context_tokens: int = 2000
    ema_alpha: Annotated[float, Field(ge=0.0, le=1.0)] = 0.35

    # Docker / runtime defaults for local development
    docker_bind_host: str = "0.0.0.0"
    docker_api_port: int = 8000

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: str | list[str]) -> list[str]:
        """Parse comma-delimited CORS origins from environment values."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    """Return cached settings for dependency injection."""
    return Settings()
