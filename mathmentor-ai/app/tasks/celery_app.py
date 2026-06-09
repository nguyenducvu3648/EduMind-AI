"""Celery application configuration — disabled (no Redis)."""

# Celery is disabled because Redis is not configured.
# Background tasks (memory updates, evaluation) run inline instead.

celery_app: object | None = None
