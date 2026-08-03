"""Run fixed, read-only PostgreSQL diagnostics with sanitized reports.

This tool never accepts arbitrary SQL. It is intended for production performance
investigations with a dedicated diagnostics role and emits no query parameters or
record contents.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from contextlib import closing
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, Iterable

try:
    import psycopg2
except ImportError:  # pragma: no cover - exercised only on incomplete runtimes
    psycopg2 = None

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv is a backend runtime dependency
    load_dotenv = None


BACKEND_DIR = Path(__file__).resolve().parents[1]
if load_dotenv:
    load_dotenv(BACKEND_DIR / ".env")

APPLICATION_NAME = "chilan-db-diagnostics"
STATEMENT_TIMEOUT = "10s"
LOCK_TIMEOUT = "1s"
IDLE_TRANSACTION_TIMEOUT = "15s"
ACTIVE_COURSE_STATUS = "active"
VALID_QUERY_IDS = (
    "index-audit",
    "course-catalog",
    "course-detail",
    "my-courses",
    "classroom-stats",
    "due-review",
    "lesson-items",
    "study-item",
)
PRIVATE_QUERY_IDS = {"my-courses", "classroom-stats", "due-review", "study-item"}
COURSE_QUERY_IDS = {"course-detail", "due-review", "lesson-items", "study-item"}
LESSON_QUERY_IDS = {"lesson-items", "study-item"}
QUESTION_QUERY_IDS = {"study-item"}
SENSITIVE_KEY_NAMES = {
    "query text",
    "parameters",
    "params",
    "user_id",
    "user id",
    "email",
    "access_token",
    "authorization",
}
UUID_PATTERN = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
URL_PATTERN = re.compile(r"(?:postgres(?:ql)?|https?)://[^\s\"']+", re.IGNORECASE)
QUOTED_LITERAL_PATTERN = re.compile(r"'(?:[^']|'')*'")
NUMERIC_LITERAL_PATTERN = re.compile(r"(?<![A-Za-z_])\d+(?:\.\d+)?(?![A-Za-z_])")


COURSE_CATALOG_SQL = """
WITH lesson_counts AS (
    SELECT course_id, COUNT(DISTINCT lesson_id) AS lesson_total
    FROM lessons
    GROUP BY course_id
),
item_counts AS (
    SELECT course_id, COUNT(DISTINCT item_id) AS total_items
    FROM language_items
    GROUP BY course_id
)
SELECT
    c.course_id,
    c.name,
    c.category,
    c.target_language,
    c.source_language,
    COALESCE(lc.lesson_total, 0) AS lesson_total,
    COALESCE(ic.total_items, 0) AS total_items
FROM courses c
LEFT JOIN lesson_counts lc ON lc.course_id = c.course_id
LEFT JOIN item_counts ic ON ic.course_id = c.course_id
ORDER BY c.course_id
"""

COURSE_DETAIL_SQL = """
SELECT
    c.course_id,
    c.name,
    c.category,
    c.target_language,
    c.source_language,
    COALESCE(lc.lesson_total, 0) AS lesson_total,
    COALESCE(ic.total_items, 0) AS total_items
FROM courses c
LEFT JOIN LATERAL (
    SELECT COUNT(DISTINCT l.lesson_id) AS lesson_total
    FROM lessons l
    WHERE l.course_id = c.course_id
) lc ON TRUE
LEFT JOIN LATERAL (
    SELECT COUNT(DISTINCT li.item_id) AS total_items
    FROM language_items li
    WHERE li.course_id = c.course_id
) ic ON TRUE
WHERE c.course_id = %s
"""

MY_COURSES_SQL = """
WITH active_courses AS (
    SELECT DISTINCT uc.course_id
    FROM user_courses uc
    WHERE uc.user_id::text = %s
      AND uc.status = %s
),
item_progress AS (
    SELECT
        li.course_id,
        COUNT(DISTINCT li.item_id) AS total_item_count,
        COUNT(DISTINCT p.item_id) FILTER (WHERE p.is_mastered = TRUE) AS mastered_count
    FROM language_items li
    JOIN active_courses ac ON ac.course_id = li.course_id
    LEFT JOIN user_progress_of_language_items p
      ON p.item_id = li.item_id
     AND p.user_id::text = %s
    GROUP BY li.course_id
),
lesson_rollup AS (
    SELECT
        l.course_id,
        COUNT(DISTINCT l.lesson_id) AS lesson_total,
        COUNT(DISTINCT l.lesson_id) FILTER (
            WHERE l.lesson_id <= COALESCE(progress.last_completed_lesson_id, 0)
        ) AS completed_lesson_count
    FROM lessons l
    JOIN active_courses ac ON ac.course_id = l.course_id
    LEFT JOIN LATERAL (
        SELECT last_completed_lesson_id
        FROM user_progress_of_lessons lp
        WHERE lp.course_id = l.course_id
          AND lp.user_id::text = %s
        ORDER BY lp.last_completed_lesson_id DESC
        LIMIT 1
    ) progress ON TRUE
    GROUP BY l.course_id
)
SELECT c.course_id, c.name, c.category,
       c.target_language, c.source_language,
       COALESCE(ip.mastered_count, 0) AS mastered_count,
       COALESCE(ip.total_item_count, 0) AS total_item_count,
       COALESCE(lr.lesson_total, 0) AS lesson_total,
       COALESCE(lr.completed_lesson_count, 0) AS completed_lesson_count,
       COALESCE(lp.last_completed_lesson_id, 0) AS last_completed_lesson_id,
       COALESCE(lp.viewed_lesson_id, 0) AS viewed_lesson_id,
       COALESCE(lp.practice_question_index, 0) AS practice_question_index,
       next_lesson.lesson_id AS next_lesson_id,
       next_lesson.title AS next_lesson_title,
       next_lesson.title_localized AS next_lesson_title_localized
FROM active_courses ac
JOIN courses c ON c.course_id = ac.course_id
LEFT JOIN LATERAL (
    SELECT
        lp.last_completed_lesson_id,
        lp.viewed_lesson_id,
        lp.practice_question_index
    FROM user_progress_of_lessons lp
    WHERE lp.course_id = c.course_id
      AND lp.user_id::text = %s
    ORDER BY lp.last_completed_lesson_id DESC
    LIMIT 1
) lp ON TRUE
LEFT JOIN item_progress ip ON ip.course_id = c.course_id
LEFT JOIN lesson_rollup lr ON lr.course_id = c.course_id
LEFT JOIN LATERAL (
    SELECT
        l.lesson_id,
        l.title,
        l.lesson_metadata->>'title_localized' AS title_localized
    FROM lessons l
    WHERE l.course_id = c.course_id
      AND l.lesson_id > COALESCE(lp.last_completed_lesson_id, 0)
    ORDER BY l.lesson_id ASC
    LIMIT 1
) next_lesson ON TRUE
"""

CLASSROOM_STATS_SQL = """
SELECT
    due.total_remaining AS total_remaining,
    reviewed.total_reviewed AS total_reviewed,
    newly_learned.total_new_learned AS total_new_learned
FROM (VALUES (1)) AS one(dummy)
CROSS JOIN LATERAL (
    SELECT COUNT(*) AS total_remaining
    FROM user_progress_of_language_items p
    JOIN language_items q ON q.item_id = p.item_id
    JOIN user_courses uc
      ON uc.course_id = q.course_id
     AND uc.user_id::text = p.user_id::text
     AND uc.status = %s
    WHERE p.user_id::text = %s
      AND p.next_review <= CURRENT_TIMESTAMP
) due
CROSS JOIN LATERAL (
    SELECT COUNT(DISTINCT rl.item_id) AS total_reviewed
    FROM review_logs rl
    JOIN user_courses uc
      ON uc.course_id = rl.course_id
     AND uc.user_id::text = rl.user_id::text
     AND uc.status = %s
    WHERE rl.user_id::text = %s
      AND rl.review_time >= CURRENT_DATE
) reviewed
CROSS JOIN LATERAL (
    SELECT COUNT(*) AS total_new_learned
    FROM review_logs rl
    JOIN user_courses uc
      ON uc.course_id = rl.course_id
     AND uc.user_id::text = rl.user_id::text
     AND uc.status = %s
    WHERE rl.user_id::text = %s
      AND rl.state = 0
      AND rl.review_time >= CURRENT_DATE
) newly_learned
"""

DUE_REVIEW_SQL = """
SELECT
    q.item_id,
    q.course_id,
    q.lesson_id,
    q.question_id,
    q.question_type,
    q.original_text,
    q.original_pinyin,
    q.standard_answers,
    q.metadata
FROM language_items q
JOIN user_progress_of_language_items p ON q.item_id = p.item_id
WHERE p.user_id::text = %s
  AND q.course_id = %s
  AND p.next_review <= CURRENT_TIMESTAMP
ORDER BY p.next_review ASC, q.item_id ASC
LIMIT 20
"""

LESSON_ITEMS_SQL = """
SELECT
    item_id,
    course_id,
    question_id,
    question_type,
    original_text,
    original_pinyin,
    standard_answers,
    metadata,
    %s AS lesson_id
FROM language_items
WHERE course_id = %s
  AND lesson_id = %s
ORDER BY question_id ASC, item_id ASC
"""

STUDY_ITEM_SQL = """
SELECT q.item_id AS item_pk, q.question_id, q.course_id, q.lesson_id,
       q.question_type, q.original_text, q.standard_answers,
       q.metadata AS item_metadata, p.stability, p.difficulty,
       p.recent_history, p.state
FROM language_items q
LEFT JOIN user_progress_of_language_items p
       ON q.item_id = p.item_id
      AND p.user_id::text = %s
WHERE q.course_id = %s
  AND q.lesson_id = %s
  AND q.question_id = %s
"""


class DiagnosticsError(RuntimeError):
    """Raised when the diagnostics command cannot safely run."""


def parse_query_ids(raw_value: str) -> list[str]:
    requested = [item.strip() for item in (raw_value or "").split(",") if item.strip()]
    if not requested or requested == ["all"]:
        return list(VALID_QUERY_IDS)
    unsupported = [item for item in requested if item not in VALID_QUERY_IDS]
    if unsupported:
        raise DiagnosticsError(f"Unsupported query IDs: {', '.join(unsupported)}")
    return list(dict.fromkeys(requested))


def validate_confirmation(args: argparse.Namespace) -> None:
    if args.environment != "production":
        raise DiagnosticsError("Refusing to run without --environment production.")
    if not args.confirm_readonly:
        raise DiagnosticsError("Refusing to run without --confirm-readonly.")


def resolve_database_url(*, allow_app_database_url: bool) -> str:
    diagnostics_url = (os.getenv("DIAGNOSTICS_DATABASE_URL") or "").strip()
    if diagnostics_url:
        return diagnostics_url
    if allow_app_database_url:
        app_url = (os.getenv("APP_DATABASE_URL") or "").strip()
        if app_url:
            return app_url
    raise DiagnosticsError(
        "Set DIAGNOSTICS_DATABASE_URL, or explicitly pass --allow-app-database-url."
    )


def _sanitize_text(value: str) -> str:
    sanitized = URL_PATTERN.sub("<url>", value)
    sanitized = UUID_PATTERN.sub("<uuid>", sanitized)
    sanitized = QUOTED_LITERAL_PATTERN.sub("'<redacted>'", sanitized)
    return sanitized


def sanitize_value(value: Any, key: str = "") -> Any:
    if key.lower() in SENSITIVE_KEY_NAMES:
        return "<redacted>"
    if isinstance(value, dict):
        return {str(item_key): sanitize_value(item_value, str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    if isinstance(value, tuple):
        return [sanitize_value(item) for item in value]
    if isinstance(value, str):
        return _sanitize_text(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def _connect(database_url: str):
    if psycopg2 is None:
        raise DiagnosticsError("psycopg2 is required; install backend requirements first.")
    return psycopg2.connect(
        database_url,
        application_name=APPLICATION_NAME,
        connect_timeout=10,
    )


def _begin_readonly(cursor) -> None:
    cursor.execute("BEGIN READ ONLY")
    cursor.execute("SET LOCAL application_name = %s", (APPLICATION_NAME,))
    cursor.execute("SET LOCAL statement_timeout = %s", (STATEMENT_TIMEOUT,))
    cursor.execute("SET LOCAL lock_timeout = %s", (LOCK_TIMEOUT,))
    cursor.execute("SET LOCAL idle_in_transaction_session_timeout = %s", (IDLE_TRANSACTION_TIMEOUT,))
    cursor.execute("SET LOCAL transaction_read_only = on")


def _run_readonly(
    database_url: str,
    operation: Callable[[Any], Any],
    *,
    connect: Callable[[str], Any] = _connect,
) -> Any:
    conn = connect(database_url)
    try:
        conn.autocommit = False
        with closing(conn.cursor()) as cursor:
            _begin_readonly(cursor)
            result = operation(cursor)
        conn.rollback()
        return result
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        conn.close()


def select_target(database_url: str, *, connect: Callable[[str], Any] = _connect) -> dict[str, int | str | None]:
    """Choose opaque representative values without returning them in reports."""

    def operation(cursor):
        cursor.execute(
            """
            SELECT uc.user_id::text, uc.course_id
            FROM user_courses uc
            WHERE uc.status = %s
            ORDER BY (
                SELECT COUNT(*)
                FROM user_progress_of_language_items p
                JOIN language_items li ON li.item_id = p.item_id
                WHERE p.user_id = uc.user_id
                  AND li.course_id = uc.course_id
            ) DESC, uc.course_id ASC
            LIMIT 1
            """,
            (ACTIVE_COURSE_STATUS,),
        )
        active = cursor.fetchone()
        if active:
            user_id, course_id = active
        else:
            user_id = None
            cursor.execute("SELECT course_id FROM courses ORDER BY course_id ASC LIMIT 1")
            row = cursor.fetchone()
            course_id = row[0] if row else None

        lesson_id = None
        question_id = None
        if course_id is not None:
            cursor.execute(
                """
                SELECT l.lesson_id
                FROM lessons l
                WHERE l.course_id = %s
                ORDER BY l.lesson_id ASC
                LIMIT 1
                """,
                (course_id,),
            )
            lesson = cursor.fetchone()
            lesson_id = lesson[0] if lesson else None

        if course_id is not None and lesson_id is not None:
            cursor.execute(
                """
                SELECT li.question_id
                FROM language_items li
                WHERE li.course_id = %s
                  AND li.lesson_id = %s
                ORDER BY li.question_id ASC, li.item_id ASC
                LIMIT 1
                """,
                (course_id, lesson_id),
            )
            question = cursor.fetchone()
            question_id = question[0] if question else None

        return {
            "user_id": user_id,
            "course_id": course_id,
            "lesson_id": lesson_id,
            "question_id": question_id,
        }

    return _run_readonly(database_url, operation, connect=connect)


def _query_spec(query_id: str, target: dict[str, int | str | None]) -> tuple[str, tuple[Any, ...]] | None:
    user_id = target.get("user_id")
    course_id = target.get("course_id")
    lesson_id = target.get("lesson_id")
    question_id = target.get("question_id")

    if query_id == "course-catalog":
        return COURSE_CATALOG_SQL, ()
    if query_id == "course-detail" and course_id is not None:
        return COURSE_DETAIL_SQL, (course_id,)
    if query_id == "my-courses" and user_id is not None:
        return MY_COURSES_SQL, (user_id, ACTIVE_COURSE_STATUS, user_id, user_id, user_id)
    if query_id == "classroom-stats" and user_id is not None:
        return CLASSROOM_STATS_SQL, (
            ACTIVE_COURSE_STATUS,
            user_id,
            ACTIVE_COURSE_STATUS,
            user_id,
            ACTIVE_COURSE_STATUS,
            user_id,
        )
    if query_id == "due-review" and user_id is not None and course_id is not None:
        return DUE_REVIEW_SQL, (user_id, course_id)
    if query_id == "lesson-items" and course_id is not None and lesson_id is not None:
        return LESSON_ITEMS_SQL, (lesson_id, course_id, lesson_id)
    if (
        query_id == "study-item"
        and user_id is not None
        and course_id is not None
        and lesson_id is not None
        and question_id is not None
    ):
        return STUDY_ITEM_SQL, (user_id, course_id, lesson_id, question_id)
    return None


def _plan_summary(plan_document: list[dict[str, Any]]) -> dict[str, Any]:
    root = plan_document[0] if plan_document else {}
    plan = root.get("Plan", {}) if isinstance(root, dict) else {}
    nodes: list[dict[str, Any]] = []

    def visit(node: Any) -> None:
        if not isinstance(node, dict):
            return
        nodes.append(node)
        for child in node.get("Plans", []) or []:
            visit(child)

    visit(plan)
    node_types = [node.get("Node Type") for node in nodes if node.get("Node Type")]
    index_names = [node.get("Index Name") for node in nodes if node.get("Index Name")]
    return sanitize_value({
        "planning_time_ms": root.get("Planning Time"),
        "execution_time_ms": root.get("Execution Time"),
        "root_node_type": plan.get("Node Type"),
        "node_count": len(nodes),
        "sequential_scan_count": sum(node_type == "Seq Scan" for node_type in node_types),
        "index_scan_count": sum(node_type in {"Index Scan", "Index Only Scan", "Bitmap Index Scan"} for node_type in node_types),
        "index_names": index_names,
        "shared_hit_blocks": plan.get("Shared Hit Blocks"),
        "shared_read_blocks": plan.get("Shared Read Blocks"),
        "temp_read_blocks": plan.get("Temp Read Blocks"),
        "temp_written_blocks": plan.get("Temp Written Blocks"),
    })


def run_explain(
    database_url: str,
    query_id: str,
    target: dict[str, int | str | None],
    *,
    analyze: bool,
    connect: Callable[[str], Any] = _connect,
) -> dict[str, Any]:
    spec = _query_spec(query_id, target)
    if spec is None:
        return {"query_id": query_id, "status": "skipped", "reason": "representative target unavailable"}
    sql, params = spec
    explain_options = "ANALYZE TRUE, BUFFERS TRUE, SETTINGS TRUE, FORMAT JSON" if analyze else "SETTINGS TRUE, FORMAT JSON"

    def operation(cursor):
        cursor.execute(f"EXPLAIN ({explain_options}) {sql}", params)
        return cursor.fetchone()[0]

    try:
        plan_document = _run_readonly(database_url, operation, connect=connect)
        return {
            "query_id": query_id,
            "status": "ok",
            "mode": "analyze" if analyze else "plan",
            "summary": _plan_summary(plan_document),
            "plan": sanitize_value(plan_document),
        }
    except Exception as exc:
        return {
            "query_id": query_id,
            "status": "failed",
            "error_type": type(exc).__name__,
        }


def run_index_audit(
    database_url: str,
    *,
    connect: Callable[[str], Any] = _connect,
) -> dict[str, Any]:
    tables = (
        "user_courses",
        "lessons",
        "language_items",
        "user_progress_of_lessons",
        "user_progress_of_language_items",
        "review_logs",
    )

    def operation(cursor):
        cursor.execute(
            """
            SELECT
                t.relname AS table_name,
                i.relname AS index_name,
                pg_size_pretty(pg_relation_size(i.oid)) AS index_size,
                ix.indisunique AS is_unique,
                ix.indisvalid AS is_valid,
                pg_get_indexdef(i.oid) AS index_definition
            FROM pg_index ix
            JOIN pg_class t ON t.oid = ix.indrelid
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            WHERE n.nspname = 'public'
              AND t.relname = ANY(%s)
            ORDER BY t.relname, i.relname
            """,
            (list(tables),),
        )
        indexes = cursor.fetchall()
        cursor.execute(
            """
            SELECT
                relname AS table_name,
                indexrelname AS index_name,
                idx_scan,
                idx_tup_read,
                idx_tup_fetch,
                pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
            FROM pg_stat_user_indexes
            WHERE relname = ANY(%s)
            ORDER BY relname, indexrelname
            """,
            (list(tables),),
        )
        index_usage = cursor.fetchall()
        cursor.execute(
            """
            SELECT
                relname AS table_name,
                n_live_tup,
                n_dead_tup,
                seq_scan,
                seq_tup_read,
                idx_scan,
                n_mod_since_analyze,
                last_analyze,
                last_autoanalyze,
                last_vacuum,
                last_autovacuum
            FROM pg_stat_user_tables
            WHERE relname = ANY(%s)
            ORDER BY relname
            """,
            (list(tables),),
        )
        table_stats = cursor.fetchall()
        return {
            "indexes": indexes,
            "index_usage": index_usage,
            "table_stats": table_stats,
        }

    try:
        audit = _run_readonly(database_url, operation, connect=connect)
        return {"query_id": "index-audit", "status": "ok", "audit": sanitize_value(audit)}
    except Exception as exc:
        return {"query_id": "index-audit", "status": "failed", "error_type": type(exc).__name__}


def build_report(
    database_url: str,
    query_ids: Iterable[str],
    *,
    analyze: bool,
    connect: Callable[[str], Any] = _connect,
) -> dict[str, Any]:
    target = select_target(database_url, connect=connect)
    results = []
    for query_id in query_ids:
        if query_id == "index-audit":
            results.append(run_index_audit(database_url, connect=connect))
        else:
            results.append(run_explain(database_url, query_id, target, analyze=analyze, connect=connect))

    return {
        "report_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "application_name": APPLICATION_NAME,
        "mode": "analyze" if analyze else "plan",
        "target_availability": {
            "active_user": bool(target.get("user_id")),
            "course": target.get("course_id") is not None,
            "lesson": target.get("lesson_id") is not None,
            "question": target.get("question_id") is not None,
        },
        "results": results,
    }


def write_report(report: dict[str, Any]) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = Path(tempfile.gettempdir()) / f"chilan-db-diagnostics-{timestamp}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report_path


def print_summary(report: dict[str, Any], report_path: Path) -> None:
    successful = sum(result.get("status") == "ok" for result in report["results"])
    skipped = sum(result.get("status") == "skipped" for result in report["results"])
    failed = sum(result.get("status") == "failed" for result in report["results"])
    print(
        "Diagnostics complete: "
        f"{successful} completed, {skipped} skipped, {failed} failed.\n"
        f"Sanitized report: {report_path}"
    )
    for result in report["results"]:
        if result.get("status") != "ok" or "summary" not in result:
            continue
        summary = result["summary"]
        print(
            f"- {result['query_id']}: "
            f"planning={summary.get('planning_time_ms')}ms "
            f"execution={summary.get('execution_time_ms')}ms "
            f"seq_scans={summary.get('sequential_scan_count')} "
            f"index_scans={summary.get('index_scan_count')}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", required=True, choices=["production"])
    parser.add_argument("--confirm-readonly", action="store_true")
    parser.add_argument("--allow-app-database-url", action="store_true")
    parser.add_argument("--analyze", action="store_true", help="Execute each fixed read query once.")
    parser.add_argument("--queries", default="all", help="Comma-separated fixed query IDs, or 'all'.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        validate_confirmation(args)
        query_ids = parse_query_ids(args.queries)
        database_url = resolve_database_url(allow_app_database_url=args.allow_app_database_url)
        report = build_report(database_url, query_ids, analyze=args.analyze)
        report_path = write_report(report)
        print_summary(report, report_path)
        return 1 if any(result.get("status") == "failed" for result in report["results"]) else 0
    except DiagnosticsError as exc:
        print(f"Diagnostics refused: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # Avoid accidentally printing connection details from driver errors.
        print(f"Diagnostics failed: {type(exc).__name__}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
