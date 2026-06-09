"""Create all app tables (users, sessions, etc.) without migrating wiki_chunks.

Usage: python -m scripts.create_tables
"""

import asyncio

from sqlalchemy import inspect, text

from app.db.base import Base
from app.db.session import create_engine
from app.db.models.user import User, UserProfile
from app.db.models.session import Session
from app.db.models.interaction_log import InteractionLog
from app.db.models.evaluation import EvaluationRun
from app.db.models.wiki_chunk import WikiChunk


async def main():
    engine = create_engine()

    async with engine.connect() as conn:
        # Check existing tables
        result = await conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        )
        existing = {row[0] for row in result}
        print(f"Existing tables: {existing}")

        # Tables we want (without wiki_chunks)
        target_tables = {"users", "user_profiles", "sessions", "interaction_logs", "evaluation_runs"}

        # Check which are missing
        missing = target_tables - existing
        if not missing:
            print("All tables already exist. Nothing to do.")
            return

        print(f"Creating missing tables: {missing}")

        # Create only the missing tables using Base metadata
        # We prevent wiki_chunks from being created by temporarily removing it
        tables_to_create = [t for t in Base.metadata.sorted_tables if t.name in missing]

        for table in tables_to_create:
            print(f"  Creating: {table.name}")
            await conn.run_sync(lambda sync_conn: table.create(sync_conn))

        await conn.commit()
        print("\nDone! Created tables:", missing)


if __name__ == "__main__":
    asyncio.run(main())
