# MathMentor AI

Phase 1 foundation for a personalized Vietnamese high-school mathematics tutor.

## Included in Phase 1

- Architecture Decision Records in `docs/adr/`
- FastAPI app factory and health endpoint
- Async SQLAlchemy database setup
- Production-shaped PostgreSQL schema and Alembic migration
- JWT registration/login flow
- User profile read/update endpoints
- Basic wiki markdown schema validation and LaTeX-safe chunking without embeddings

## Local Development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
copy .env.example .env
uvicorn app.main:create_app --factory --reload
```

## Architecture

The implementation follows the required phased roadmap. Embeddings, hybrid retrieval, reranking, full orchestration, and GPT-4o generation are intentionally deferred to later phases.

