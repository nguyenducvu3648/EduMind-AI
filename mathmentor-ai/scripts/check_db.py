"""View DB schema & data using raw SQL."""

import asyncio
from app.db.session import AsyncSessionLocal


async def main():
    async with AsyncSessionLocal() as sess:
        # 1. Schema columns
        print("=== TABLE: wiki_chunks (columns) ===")
        rows = await sess.execute(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'wiki_chunks'
            ORDER BY ordinal_position
            """
        )
        for col in rows.all():
            print(f"  {col.column_name:30s} {col.data_type:20s} {col.is_nullable}")

        # 2. Count + first 3 rows
        print("\n=== FIRST 3 ROWS ===")
        rows = await sess.execute("SELECT * FROM wiki_chunks LIMIT 3")
        col_names = list(rows.keys())
        print(f"  Columns: {col_names}")
        for i, row in enumerate(rows, 1):
            print(f"\n  --- Row {i} ---")
            for name, val in row._mapping.items():
                if name == "embedding" and val is not None:
                    print(f"    {name}: <vector len={len(val)}>")
                elif isinstance(val, str) and len(val) > 200:
                    print(f"    {name}: {val[:150]}...")
                else:
                    print(f"    {name}: {val}")


if __name__ == "__main__":
    asyncio.run(main())
