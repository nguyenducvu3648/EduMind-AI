# ADR 0003: Use Celery Instead of FastAPI BackgroundTasks for Memory Updates

## Context
The memory system updates mastery scores, behavioral signals, and misconception patterns after each interaction. These updates must not block student responses and must survive API process restarts.

## Decision
Use Celery 5+ for EMA updates, wiki ingestion jobs, and scheduled evaluation tasks.

## Alternatives Considered
- FastAPI `BackgroundTasks`: simple, but tied to the API worker lifecycle with weak retry semantics.
- In-process asyncio tasks: low overhead, but unreliable under restarts and difficult to observe across replicas.
- External workflow engines: durable, but too heavyweight for v1.0.

## Consequences
Celery provides queue isolation, retries, routing, and operational visibility. It adds Redis or another broker to the stack, but the reliability gain is justified because memory updates affect personalization quality over time.
