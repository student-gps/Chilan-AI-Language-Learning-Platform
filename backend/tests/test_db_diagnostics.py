import argparse
import os
import unittest
from unittest.mock import patch

from scripts import db_diagnostics


class FakeCursor:
    def __init__(self, responses=None):
        self.responses = list(responses or [])
        self.executed = []
        self.closed = False

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        if not self.responses:
            return None
        response = self.responses.pop(0)
        return response.get("one") if isinstance(response, dict) else response

    def fetchall(self):
        if not self.responses:
            return []
        response = self.responses.pop(0)
        return response.get("all", []) if isinstance(response, dict) else response

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.autocommit = None
        self.rollback_calls = 0
        self.closed = False

    def cursor(self):
        return self._cursor

    def rollback(self):
        self.rollback_calls += 1

    def close(self):
        self.closed = True


class DbDiagnosticsTests(unittest.TestCase):
    def test_requires_production_and_readonly_confirmations(self):
        with self.assertRaises(db_diagnostics.DiagnosticsError):
            db_diagnostics.validate_confirmation(
                argparse.Namespace(environment="staging", confirm_readonly=True)
            )
        with self.assertRaises(db_diagnostics.DiagnosticsError):
            db_diagnostics.validate_confirmation(
                argparse.Namespace(environment="production", confirm_readonly=False)
            )

    def test_prefers_dedicated_diagnostics_database_url(self):
        with patch.dict(os.environ, {
            "DIAGNOSTICS_DATABASE_URL": "postgresql://diagnostics:secret@db.example/chilan",
            "APP_DATABASE_URL": "postgresql://application:secret@db.example/chilan",
        }, clear=False):
            url = db_diagnostics.resolve_database_url(allow_app_database_url=False)

        self.assertEqual(url, "postgresql://diagnostics:secret@db.example/chilan")

    def test_refuses_app_database_url_without_explicit_flag(self):
        with patch.dict(os.environ, {
            "DIAGNOSTICS_DATABASE_URL": "",
            "APP_DATABASE_URL": "postgresql://application:secret@db.example/chilan",
        }, clear=False):
            with self.assertRaises(db_diagnostics.DiagnosticsError):
                db_diagnostics.resolve_database_url(allow_app_database_url=False)

    def test_sanitize_value_redacts_query_text_urls_uuids_and_literals(self):
        sanitized = db_diagnostics.sanitize_value({
            "Query Text": "SELECT * FROM users WHERE user_id = '11111111-1111-1111-1111-111111111111'",
            "Plan": "Index Cond: (course_id = 303 AND email = 'learner@example.com')",
            "Endpoint": "postgresql://admin:secret@db.example/chilan",
            "Nested": [{"user_id": "11111111-1111-1111-1111-111111111111"}],
        })

        serialized = str(sanitized)
        self.assertEqual(sanitized["Query Text"], "<redacted>")
        self.assertNotIn("11111111-1111-1111-1111-111111111111", serialized)
        self.assertNotIn("learner@example.com", serialized)
        self.assertNotIn("admin:secret", serialized)

    def test_readonly_runner_sets_timeouts_and_rolls_back(self):
        cursor = FakeCursor()
        conn = FakeConnection(cursor)

        result = db_diagnostics._run_readonly(
            "postgresql://diagnostics:secret@db.example/chilan",
            lambda _cursor: "ok",
            connect=lambda _url: conn,
        )

        self.assertEqual(result, "ok")
        self.assertFalse(conn.autocommit)
        self.assertEqual(conn.rollback_calls, 1)
        self.assertTrue(conn.closed)
        statements = [query for query, _params in cursor.executed]
        self.assertEqual(statements[0], "BEGIN READ ONLY")
        self.assertIn("SET LOCAL transaction_read_only = on", statements)
        self.assertTrue(all("diagnostics:secret" not in statement for statement in statements))

    def test_run_explain_never_returns_query_parameters(self):
        plan = [{
            "Plan": {
                "Node Type": "Index Scan",
                "Index Name": "language_items_course_lesson_question_idx",
                "Index Cond": "(course_id = 303)",
                "Shared Read Blocks": 2,
            },
            "Planning Time": 1.25,
            "Execution Time": 2.5,
            "Settings": {"application_name": "chilan-db-diagnostics"},
        }]
        cursor = FakeCursor([{"one": (plan,)}])
        conn = FakeConnection(cursor)
        target = {
            "user_id": "11111111-1111-1111-1111-111111111111",
            "course_id": 303,
            "lesson_id": 1,
            "question_id": 1001,
        }

        result = db_diagnostics.run_explain(
            "postgresql://diagnostics:secret@db.example/chilan",
            "study-item",
            target,
            analyze=True,
            connect=lambda _url: conn,
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["mode"], "analyze")
        self.assertEqual(result["summary"]["index_scan_count"], 1)
        serialized = str(result)
        self.assertNotIn(target["user_id"], serialized)
        self.assertNotIn("diagnostics:secret", serialized)
        self.assertNotIn("Parameters", serialized)
        explain_sql, explain_params = cursor.executed[-1]
        self.assertIn("EXPLAIN (ANALYZE TRUE, BUFFERS TRUE", explain_sql)
        self.assertEqual(explain_params, (
            target["user_id"], target["course_id"], target["lesson_id"], target["question_id"],
        ))

    def test_rejects_unknown_query_ids(self):
        with self.assertRaises(db_diagnostics.DiagnosticsError):
            db_diagnostics.parse_query_ids("course-catalog,arbitrary-sql")


if __name__ == "__main__":
    unittest.main()
