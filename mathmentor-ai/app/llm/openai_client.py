"""OpenAI-compatible LLM client — works with OpenAI, DeepSeek, Groq, Together, etc."""

import asyncio
from collections.abc import AsyncIterator

from openai import AsyncOpenAI, OpenAIError

from app.config import Settings, get_settings
from app.utils.logging import get_logger
from app.utils.metrics import LLM_TOKEN_USAGE

logger = get_logger(__name__)


class OpenAIClient:
    """Thin async client for any OpenAI-compatible chat API."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client: AsyncOpenAI | None = None
        api_key = (
            self.settings.llm_api_key.get_secret_value() if self.settings.llm_api_key else ""
        )
        if api_key:
            self._client = AsyncOpenAI(
                api_key=api_key,
                base_url=self.settings.llm_base_url,
                timeout=self.settings.llm_request_timeout,
            )

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a complete tutor response."""
        if self._client is None:
            return self._offline_grounded_response(user_prompt)

        last_error: Exception | None = None
        for attempt in range(self.settings.llm_max_retries + 1):
            try:
                response = await self._client.chat.completions.create(
                    model=self.settings.llm_model,
                    temperature=self.settings.llm_temperature,
                    max_tokens=self.settings.llm_max_tokens,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                usage = response.usage
                if usage:
                    LLM_TOKEN_USAGE.labels(model=self.settings.llm_model, type="prompt").inc(
                        usage.prompt_tokens
                    )
                    LLM_TOKEN_USAGE.labels(model=self.settings.llm_model, type="completion").inc(
                        usage.completion_tokens
                    )
                return response.choices[0].message.content or ""
            except OpenAIError as exc:
                last_error = exc
                logger.info(
                    "llm_generation_retry",
                    stage="generation",
                    status="error",
                    attempt=attempt,
                    error=str(exc),
                )
                await asyncio.sleep(0.5 * (attempt + 1))
        raise RuntimeError("LLM generation failed.") from last_error

    async def stream(self, system_prompt: str, user_prompt: str) -> AsyncIterator[str]:
        """Stream tutor response chunks."""
        if self._client is None:
            yield self._offline_grounded_response(user_prompt)
            return

        stream = await self._client.chat.completions.create(
            model=self.settings.llm_model,
            temperature=self.settings.llm_temperature,
            max_tokens=self.settings.llm_max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=True,
        )
        async for event in stream:
            delta = event.choices[0].delta.content
            if delta:
                yield delta

    def _offline_grounded_response(self, user_prompt: str) -> str:
        """Graceful fallback when LLM API key is not configured."""
        context_marker = "## Retrieved Wiki Context"
        question_marker = "## Student Question"
        context = user_prompt.split(question_marker)[0].replace(context_marker, "").strip()
        question = user_prompt.split(question_marker)[-1].strip()
        if context:
            return (
                "LLM generation is disabled because `LLM_API_KEY` is not configured.\n\n"
                f"**Question:** {question}\n\n"
                f"**Relevant context:**\n{context[:1800]}"
            )
        return (
            "LLM generation is disabled because `LLM_API_KEY` is not configured, "
            "and no RAG context was retrieved for this question."
        )
