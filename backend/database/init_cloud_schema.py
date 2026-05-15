"""
Initialize the cloud database schema after restoring the legacy Neon schema.

This keeps the old application tables from the dump, then applies the newer
embedding-deduplication schema used by sync_to_db.py.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from database.connection import get_connection
from database.sync_to_db import (
    ensure_answer_embeddings_table,
    ensure_language_items_answer_embedding_id,
    ensure_vocabulary_knowledge_table,
)
from services.course_enrollment_service import ensure_user_courses_status


def main() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    ensure_vocabulary_knowledge_table(cur)
    ensure_answer_embeddings_table(cur)
    ensure_language_items_answer_embedding_id(cur)
    ensure_user_courses_status(cur)

    conn.commit()
    cur.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
        ORDER BY table_name;
        """
    )
    tables = [row[0] for row in cur.fetchall()]
    cur.execute(
        """
        SELECT extname, extversion
        FROM pg_extension
        WHERE extname IN ('vector', 'uuid-ossp')
        ORDER BY extname;
        """
    )
    extensions = cur.fetchall()
    cur.close()
    conn.close()

    print("Tables:")
    for table in tables:
        print(f"  - {table}")
    print("Extensions:")
    for name, version in extensions:
        print(f"  - {name} {version}")


if __name__ == "__main__":
    main()
