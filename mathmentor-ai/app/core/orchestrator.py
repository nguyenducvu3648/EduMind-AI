"""Main tutoring pipeline coordinator — Orchestration Layer."""

import asyncio
import json
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.core.intent_detector import IntentDetector, QueryIntent
from app.core.pedagogy_selector import PedagogySelector
from app.core.prompt_builder import DynamicPromptBuilder
from app.core.query_rewriter import QueryRewriter
from app.core.response_postprocessor import ResponsePostprocessor
from app.db.models.interaction_log import InteractionLog
from app.db.models.session import Session
from app.db.models.user import User, UserProfile
from app.db.models.wiki_article import WikiArticle
from app.llm.openai_client import OpenAIClient
from app.memory.ema_updater import EMAUpdater, InteractionSignal
from app.memory.user_state_interpreter import (
    SessionSummary,
    UserStateInterpreter,
    UserStateSnapshot,
)
from app.rag.context_compressor import LaTeXSafeCompressor
from app.rag.reranker import CrossEncoderReranker
from app.rag.retriever import HybridRetriever
from app.rag.types import RetrievedChunk
from app.utils.latex_utils import validate_safe_latex
from app.utils.logging import get_logger
from app.utils.metrics import CHAT_LATENCY, STRATEGY_COUNTER

logger = get_logger(__name__)


@dataclass(frozen=True)
class ChatPipelineResult:
    """Final result returned by the tutor pipeline."""

    session_id: UUID
    message_id: UUID
    response: str
    teaching_strategy_used: str
    bloom_level: str
    topics_covered: list[str]
    sources: list[RetrievedChunk]
    follow_up_suggestions: list[str]


@dataclass
class PipelinePrepared:
    """Prepared pipeline state before LLM generation."""

    session: Session
    intent: QueryIntent
    user_state: UserStateSnapshot
    strategy: str
    bloom_level: str
    prompt_system: str
    prompt_user: str
    context_chunks: list[RetrievedChunk]
    wiki_article: dict | None
    started: float


class MathTutorOrchestrator:
    """Orchestration Layer — coordinate RAG, LLM-Wiki, User Memory, and LLM."""

    def __init__(
        self,
        db_session: AsyncSession,
        retriever: HybridRetriever,
        reranker: CrossEncoderReranker,
        compressor: LaTeXSafeCompressor,
        llm_client: OpenAIClient,
        settings: Settings | None = None,
    ) -> None:
        self.db_session = db_session
        self.retriever = retriever
        self.reranker = reranker
        self.compressor = compressor
        self.llm_client = llm_client
        self.settings = settings or get_settings()
        self.intent_detector = IntentDetector()
        self.query_rewriter = QueryRewriter()
        self.user_state_interpreter = UserStateInterpreter()
        self.pedagogy_selector = PedagogySelector()
        self.prompt_builder = DynamicPromptBuilder()
        self.postprocessor = ResponsePostprocessor()
        self.ema_updater = EMAUpdater(alpha=self.settings.ema_alpha)

    async def answer(self, user: User, message: str, session_id: UUID | None) -> ChatPipelineResult:
        """Run the full non-streaming tutoring pipeline."""
        prepared = await self._prepare(user, message, session_id)
        raw_response = await self.llm_client.generate(prepared.prompt_system, prepared.prompt_user)
        response = self.postprocessor.process(raw_response)
        log = await self._persist_interaction(prepared, user, message, response)
        await self._schedule_memory_update(
            user.id,
            prepared.intent.topic_tags,
            log.id,
            hint_used=prepared.strategy == "hint_first",
        )
        return self._result(prepared, log.id, response)

    async def stream_answer(
        self,
        user: User,
        message: str,
        session_id: UUID | None,
    ) -> AsyncIterator[str]:
        """Stream the tutoring response and persist the completed interaction."""
        prepared = await self._prepare(user, message, session_id)
        chunks: list[str] = []
        async for chunk in self.llm_client.stream(prepared.prompt_system, prepared.prompt_user):
            chunks.append(chunk)
            yield f"event: token\ndata: {json.dumps({'token': chunk})}\n\n"
        response = self.postprocessor.process("".join(chunks))
        log = await self._persist_interaction(prepared, user, message, response)
        await self._schedule_memory_update(
            user.id,
            prepared.intent.topic_tags,
            log.id,
            hint_used=prepared.strategy == "hint_first",
        )
        follow_up_suggestions = self._followups(prepared.intent.topic_tags)
        metadata = {
            "session_id": str(prepared.session.id),
            "message_id": str(log.id),
            "teaching_strategy_used": prepared.strategy,
            "bloom_level": prepared.bloom_level,
            "topics_covered": prepared.intent.topic_tags,
            "sources": [str(chunk.id) for chunk in prepared.context_chunks],
            "follow_up_suggestions": follow_up_suggestions,
        }
        yield f"event: metadata\ndata: {json.dumps(metadata)}\n\n"

    async def _prepare(
        self,
        user: User,
        message: str,
        session_id: UUID | None,
    ) -> PipelinePrepared:
        started = time.perf_counter()
        validate_safe_latex(message)
        session = await self._load_or_create_session(user, session_id)
        profile = await self._load_profile(user)
        intent = await self.intent_detector.detect(message)
        recent_sessions = await self._recent_session_summaries(user.id)
        user_state = await self.user_state_interpreter.interpret(
            profile,
            recent_sessions,
            message,
            intent.topic_tags,
        )
        strategy = self.pedagogy_selector.select(user_state, intent)
        bloom = self.pedagogy_selector.get_bloom_target(user_state)
        scaffolding = self.pedagogy_selector.get_scaffolding_depth(user_state)
        STRATEGY_COUNTER.labels(strategy=strategy.value, learner_type=user_state.learner_type).inc()

        queries = await self.query_rewriter.rewrite(message, intent)
        metadata_filter = self._metadata_filter(user, intent)
        context_chunks: list[RetrievedChunk] = []
        wiki_article_data: dict | None = None

        # ─── Step 1: Fetch RAG context ───
        try:
            retrieved = await self.retriever.retrieve(
                queries,
                metadata_filter,
                profile,
                top_k_semantic=self.settings.rag_top_k_semantic,
                top_k_bm25=self.settings.rag_top_k_bm25,
                final_top_k=max(10, self.settings.rag_final_top_k),
            )
            context_chunks = await self.reranker.rerank(
                message,
                retrieved,
                top_k=self.settings.rag_final_top_k,
            )
        except Exception as exc:
            logger.info("rag_pipeline_fallback", stage="rag", status="fallback", error=str(exc))

        # ─── Step 2: Check LLM-Wiki for relevant articles ───
        try:
            wiki_article_data = await self._find_wiki_article(
                intent.topic_tags, user.grade_level
            )
            if wiki_article_data:
                logger.info(
                    "wiki_article_found",
                    stage="llm_wiki",
                    slug=wiki_article_data.get("slug"),
                    title=wiki_article_data.get("title"),
                )
        except Exception as exc:
            logger.info("wiki_article_lookup_failed", stage="llm_wiki", error=str(exc))

        # ─── Step 3: Build prompt with both RAG + LLM-Wiki ───
        context_bundle = self.compressor.compress(
            context_chunks,
            max_tokens=self.settings.max_context_tokens,
            query=message,
        )

        try:
            recent_history = await self._recent_history(user.id)
        except Exception:
            recent_history = []

        prompt_system = self.prompt_builder.build_system_prompt(
            user_state,
            strategy,
            bloom,
            scaffolding,
        )

        # Enhanced user prompt with optional LLM-Wiki article
        prompt_user = self.prompt_builder.build_user_prompt(
            message,
            context_bundle,
            recent_history,
            wiki_article=wiki_article_data,
        )

        return PipelinePrepared(
            session=session,
            intent=intent,
            user_state=user_state,
            strategy=strategy.value,
            bloom_level=bloom.value,
            prompt_system=prompt_system,
            prompt_user=prompt_user,
            context_chunks=context_chunks,
            wiki_article=wiki_article_data,
            started=started,
        )

    async def _find_wiki_article(
        self, topics: list[str], grade: int | None
    ) -> dict | None:
        """Search LLM-Wiki for a relevant article matching topics + grade."""
        if not topics:
            return None

        # Try exact grade match first
        for topic in topics:
            result = await self.db_session.execute(
                select(WikiArticle).where(
                    WikiArticle.is_published == True,
                    WikiArticle.grade == grade if grade else True,
                    WikiArticle.tags.any(topic),
                )
            )
            article = result.scalar_one_or_none()
            if article:
                return {
                    "slug": article.slug,
                    "title": article.title,
                    "summary": article.summary,
                    "content": article.content,
                }

        # Fallback: any grade
        for topic in topics:
            result = await self.db_session.execute(
                select(WikiArticle).where(
                    WikiArticle.is_published == True,
                    WikiArticle.tags.any(topic),
                )
            )
            article = result.scalar_one_or_none()
            if article:
                return {
                    "slug": article.slug,
                    "title": article.title,
                    "summary": article.summary,
                    "content": article.content,
                }

        return None

    async def _load_or_create_session(self, user: User, session_id: UUID | None) -> Session:
        if session_id:
            session = await self.db_session.get(Session, session_id)
            if session and session.user_id == user.id:
                return session
        session = Session(user_id=user.id)
        self.db_session.add(session)
        await self.db_session.flush()
        return session

    async def _load_profile(self, user: User) -> UserProfile:
        profile = await self.db_session.get(UserProfile, user.id)
        if profile is None:
            profile = UserProfile(user_id=user.id)
            self.db_session.add(profile)
            await self.db_session.flush()
        return profile

    async def _recent_session_summaries(self, user_id: UUID) -> list[SessionSummary]:
        result = await self.db_session.execute(
            select(Session)
            .where(Session.user_id == user_id)
            .order_by(Session.started_at.desc())
            .limit(5)
        )
        return [SessionSummary.from_model(session) for session in result.scalars().all()]

    async def _recent_history(self, user_id: UUID) -> list[str]:
        result = await self.db_session.execute(
            select(InteractionLog)
            .where(InteractionLog.user_id == user_id)
            .order_by(InteractionLog.created_at.desc())
            .limit(6)
        )
        history = []
        for log in reversed(result.scalars().all()):
            history.append(f"Student: {log.query}\nTutor: {log.response[:600]}")
        return history

    def _metadata_filter(self, user: User, intent: QueryIntent) -> dict:
        return {
            "grade": user.grade_level,
            "difficulty_max": min(1.0, intent.difficulty_estimate + 0.25),
            "concepts": intent.topic_tags,
            "tags": intent.topic_tags,
        }

    async def _persist_interaction(
        self,
        prepared: PipelinePrepared,
        user: User,
        query: str,
        response: str,
    ) -> InteractionLog:
        duration_ms = int((time.perf_counter() - prepared.started) * 1000)
        log = InteractionLog(
            session_id=prepared.session.id,
            user_id=user.id,
            query=query,
            response=response,
            intent_detected=prepared.intent.question_type,
            topics_detected=prepared.intent.topic_tags,
            teaching_strategy=prepared.strategy,
            bloom_level=prepared.bloom_level,
            learner_type_at_time=prepared.user_state.learner_type,
            context_chunks_used=[],  # wiki_chunks use int IDs, interaction_log expects UUID — skip for now
            hint_used=prepared.strategy == "hint_first",
            response_latency_ms=duration_ms,
        )
        prepared.session.message_count += 1
        prepared.session.topics_covered = sorted(
            set(prepared.session.topics_covered or []).union(prepared.intent.topic_tags)
        )
        self.db_session.add(log)
        await self.db_session.commit()
        await self.db_session.refresh(log)
        CHAT_LATENCY.observe(duration_ms / 1000)
        logger.info(
            "chat_pipeline_completed",
            stage="orchestration",
            status="success",
            user_id=str(user.id),
            session_id=str(prepared.session.id),
            message_id=str(log.id),
            duration_ms=duration_ms,
            strategy=prepared.strategy,
        )
        return log

    async def _schedule_memory_update(
        self,
        user_id: UUID,
        topics: list[str],
        message_id: UUID,
        hint_used: bool,
    ) -> None:
        signal = InteractionSignal(user_id=user_id, topics=topics, hint_used=hint_used)
        try:
            await self.ema_updater.apply(self.db_session, signal)
        except Exception as exc:
            logger.info("memory_update_failed", stage="memory_update", status="error", error=str(exc))

    def _result(
        self,
        prepared: PipelinePrepared,
        message_id: UUID,
        response: str,
    ) -> ChatPipelineResult:
        return ChatPipelineResult(
            session_id=prepared.session.id,
            message_id=message_id,
            response=response,
            teaching_strategy_used=prepared.strategy,
            bloom_level=prepared.bloom_level,
            topics_covered=prepared.intent.topic_tags,
            sources=prepared.context_chunks,
            follow_up_suggestions=self._followups(prepared.intent.topic_tags),
        )

    def _followups(self, topics: list[str]) -> list[str]:
        if not topics:
            return [
                "Can you show me one similar example?",
                "What is the key formula I should remember?",
            ]
        topic = topics[0].replace("_", " ")
        return [
            f"Can we solve another {topic} problem?",
            f"What common mistake should I avoid in {topic}?",
            f"How does {topic} connect to earlier lessons?",
        ]
