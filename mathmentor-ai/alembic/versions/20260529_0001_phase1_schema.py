"""phase 1 schema

Revision ID: 20260529_0001
Revises:
Create Date: 2026-05-29 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


class VectorType(sa.types.UserDefinedType):
    """Alembic-local pgvector column type."""

    cache_ok = True

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    def get_col_spec(self, **_: object) -> str:
        return f"VECTOR({self.dimensions})"


revision: str = "20260529_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create Phase 1 tables and PostgreSQL indexes."""
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("grade_level", sa.SmallInteger(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("grade_level BETWEEN 10 AND 12", name="ck_users_grade"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "user_profiles",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "topic_mastery",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "concept_dependency_map",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "misconception_patterns",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("learning_speed", sa.Float(), server_default="0.5", nullable=False),
        sa.Column("retention_strength", sa.Float(), server_default="0.5", nullable=False),
        sa.Column("error_recurrence_rate", sa.Float(), server_default="0.3", nullable=False),
        sa.Column("cognitive_load_tolerance", sa.Float(), server_default="0.5", nullable=False),
        sa.Column(
            "response_preference", sa.String(length=50), server_default="balanced", nullable=False
        ),
        sa.Column("hint_dependency_level", sa.Float(), server_default="0.5", nullable=False),
        sa.Column("step_by_step_preference", sa.Float(), server_default="0.5", nullable=False),
        sa.Column(
            "weak_topics",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column(
            "strong_topics",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("message_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "topics_covered",
            postgresql.ARRAY(sa.Text()),
            server_default=sa.text("'{}'::text[]"),
            nullable=False,
        ),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])

    op.create_table(
        "wiki_chunks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("article_id", sa.String(length=255), nullable=False),
        sa.Column("article_title", sa.String(length=500), nullable=False),
        sa.Column("section_header", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(length=50), nullable=True),
        sa.Column("subject", sa.String(length=50), server_default="Toán", nullable=False),
        sa.Column("grade_min", sa.SmallInteger(), nullable=True),
        sa.Column("grade_max", sa.SmallInteger(), nullable=True),
        sa.Column("difficulty", sa.Float(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("concepts", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("skills", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("prerequisites", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("source_refs", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("embedding", VectorType(1024), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=True),
        sa.Column(
            "parent_chunk_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("wiki_chunks.id"),
            nullable=True,
        ),
        sa.Column(
            "last_updated", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_wiki_chunks_article_id", "wiki_chunks", ["article_id"])
    op.create_index(
        "ix_wiki_chunks_embedding_ivfflat",
        "wiki_chunks",
        ["embedding"],
        postgresql_using="ivfflat",
        postgresql_ops={"embedding": "vector_cosine_ops"},
        postgresql_with={"lists": 100},
    )
    op.create_index("ix_wiki_chunks_tags_gin", "wiki_chunks", ["tags"], postgresql_using="gin")
    op.create_index(
        "ix_wiki_chunks_concepts_gin", "wiki_chunks", ["concepts"], postgresql_using="gin"
    )
    op.create_index(
        "ix_wiki_chunks_grade_difficulty",
        "wiki_chunks",
        ["grade_min", "grade_max", "difficulty"],
    )
    op.execute(
        "CREATE INDEX ix_wiki_chunks_content_fts "
        "ON wiki_chunks USING GIN (to_tsvector('english', content))"
    )

    op.create_table(
        "interaction_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id"),
            nullable=False,
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("response", sa.Text(), nullable=False),
        sa.Column("intent_detected", sa.String(length=100), nullable=True),
        sa.Column("topics_detected", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("teaching_strategy", sa.String(length=100), nullable=True),
        sa.Column("bloom_level", sa.String(length=50), nullable=True),
        sa.Column("learner_type_at_time", sa.String(length=50), nullable=True),
        sa.Column(
            "context_chunks_used", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True
        ),
        sa.Column("hint_used", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("response_latency_ms", sa.Integer(), nullable=True),
        sa.Column("user_feedback", sa.SmallInteger(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_interaction_logs_user_created",
        "interaction_logs",
        ["user_id", sa.text("created_at DESC")],
    )
    op.create_index("ix_interaction_logs_session_id", "interaction_logs", ["session_id"])

    op.create_table(
        "evaluation_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("run_type", sa.String(length=50), nullable=True),
        sa.Column("metrics", postgresql.JSONB(), nullable=True),
        sa.Column("sample_size", sa.Integer(), nullable=True),
        sa.Column("triggered_by", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    """Drop Phase 1 schema."""
    op.drop_table("evaluation_runs")
    op.drop_index("ix_interaction_logs_session_id", table_name="interaction_logs")
    op.drop_index("ix_interaction_logs_user_created", table_name="interaction_logs")
    op.drop_table("interaction_logs")
    op.execute("DROP INDEX IF EXISTS ix_wiki_chunks_content_fts")
    op.drop_index("ix_wiki_chunks_grade_difficulty", table_name="wiki_chunks")
    op.drop_index("ix_wiki_chunks_concepts_gin", table_name="wiki_chunks")
    op.drop_index("ix_wiki_chunks_tags_gin", table_name="wiki_chunks")
    op.drop_index("ix_wiki_chunks_embedding_ivfflat", table_name="wiki_chunks")
    op.drop_index("ix_wiki_chunks_article_id", table_name="wiki_chunks")
    op.drop_table("wiki_chunks")
    op.drop_index("ix_sessions_user_id", table_name="sessions")
    op.drop_table("sessions")
    op.drop_table("user_profiles")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
