# ADR 0005: Use BAAI/bge-m3 Instead of OpenAI text-embedding-3-large

## Context
The knowledge base is Vietnamese math content with mixed natural language and symbolic notation. Embedding volume can grow substantially during ingestion and re-indexing.

## Decision
Use `BAAI/bge-m3` through sentence-transformers as the embedding model.

## Alternatives Considered
- OpenAI `text-embedding-3-large`: high-quality hosted embeddings, but API cost and data egress increase with ingestion volume.
- Smaller multilingual sentence-transformer models: cheaper to run, but lower retrieval quality for Vietnamese and technical math phrasing.
- Domain-trained custom embeddings: attractive long term, but not justified before collecting production retrieval feedback.

## Consequences
Self-hosted embeddings improve cost predictability and keep ingestion independent from external API availability. The cost is local model management and larger infrastructure footprint. The 1024-dimensional output aligns with the pgvector schema.
