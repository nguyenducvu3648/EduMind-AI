# ADR 0001: Use pgvector Instead of a Dedicated Vector Database

## Context
MathMentor AI needs hybrid retrieval over structured wiki chunks with relational filters such as grade, difficulty, tags, concepts, and prerequisites. The v1.0 system is expected to scale to thousands of concurrent users, but the knowledge base is read-heavy, curated, and operationally simpler than a web-scale open corpus.

## Decision
Use PostgreSQL 16 with pgvector 0.7+ as the primary vector store and relational database.

## Alternatives Considered
- Pinecone: strong managed vector operations, but adds a vendor boundary, duplicated metadata, and higher recurring cost.
- Weaviate: mature vector-native features, but introduces another operational system and schema synchronization burden.
- Qdrant: excellent HNSW performance and filtering, but still requires running and observing a separate persistence layer.

## Consequences
This keeps transactional metadata, vector search, full-text search, and user state in one database. It reduces operational complexity and makes Phase 1 through Phase 3 easier to test locally. The trade-off is that very large corpora may require HNSW tuning, read replicas, or later migration to a dedicated vector database once vector workload exceeds PostgreSQL comfort zones.
