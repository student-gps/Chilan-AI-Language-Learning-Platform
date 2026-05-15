"""Print a read-only PostgreSQL size report for the configured database."""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from database.connection import get_connection


def main() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
    print(f"database_size: {cur.fetchone()[0]}")

    cur.execute(
        """
        SELECT
            relname,
            pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
            pg_size_pretty(pg_relation_size(relid)) AS table_size,
            pg_size_pretty(pg_indexes_size(relid)) AS index_size,
            pg_total_relation_size(relid) AS bytes
        FROM pg_catalog.pg_statio_user_tables
        ORDER BY pg_total_relation_size(relid) DESC;
        """
    )
    print("\ntables:")
    for relname, total, table, index, _bytes in cur.fetchall():
        print(f"  {relname:36} total={total:>10} table={table:>10} index={index:>10}")

    cur.execute(
        """
        SELECT vector_dims(primary_embedding), COUNT(*)
        FROM answer_embeddings
        GROUP BY 1
        ORDER BY 1;
        """
    )
    print("\nanswer_embeddings dims:")
    for dims, count in cur.fetchall():
        print(f"  dims={dims} count={count}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
