# ADR 0002: Use Cross-Encoder Reranking After Hybrid Retrieval

## Context
Initial retrieval uses semantic similarity and full-text search, which are fast but can rank superficially similar chunks above pedagogically necessary context. Math questions often hinge on exact constraints, formula variants, and misconception-specific wording.

## Decision
Use `cross-encoder/ms-marco-MiniLM-L-6-v2` to rerank the fused top candidates before context compression.

## Alternatives Considered
- Bi-encoder-only ranking: lower latency, but weaker pairwise relevance judgment.
- LLM-based reranking: potentially higher quality, but too slow and expensive for the request-critical path.
- No reranking: simplest implementation, but lower RAG precision and more irrelevant prompt context.

## Consequences
Cross-encoder reranking improves Precision@5 and reduces hallucination risk by selecting tighter context. It adds CPU/GPU latency, so reranking is constrained to small candidate sets, batched at 32 pairs or fewer, and can be degraded gracefully if the model is unavailable.
