"""Prometheus metrics definitions."""

from prometheus_client import Counter, Gauge, Histogram

CHAT_LATENCY = Histogram(
    "chat_request_duration_seconds",
    "End-to-end chat request latency",
    buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 10.0],
)

RAG_RETRIEVAL_LATENCY = Histogram(
    "rag_retrieval_duration_seconds",
    "RAG pipeline latency",
    labelnames=["stage"],
)

STRATEGY_COUNTER = Counter(
    "teaching_strategy_selected_total",
    "Count of each teaching strategy selected",
    labelnames=["strategy", "learner_type"],
)

LLM_TOKEN_USAGE = Counter(
    "llm_tokens_used_total",
    "OpenAI API token consumption",
    labelnames=["model", "type"],
)

USER_MASTERY_GAUGE = Gauge(
    "user_average_mastery_score",
    "Average topic mastery across active users",
)
