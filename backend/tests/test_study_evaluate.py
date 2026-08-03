import unittest
from unittest.mock import patch

from .test_helpers import FakeConnection, FakeEvaluatorService, FakeScheduler, SmokeTestCaseMixin, study
from database.utils import create_access_token


USER_ID = "33333333-3333-3333-3333-333333333333"


def auth_headers():
    return {"Authorization": f"Bearer {create_access_token({'sub': USER_ID})}"}


class StudyEvaluateSmokeTests(SmokeTestCaseMixin, unittest.TestCase):
    def test_study_evaluate_exact_match_returns_success_payload(self):
        def handler(query, params):
            if "FROM user_courses" in query:
                return {"fetchone": (1,)}
            if "SELECT q.item_id as item_pk" in query:
                return {
                    "fetchone": {
                        "item_pk": 77,
                        "question_id": 1001,
                        "course_id": 2,
                        "lesson_id": 101,
                        "question_type": "CN_TO_FR",
                        "original_text": "你好",
                        "standard_answers": ["bonjour"],
                        "item_metadata": {},
                        "stability": 0.6,
                        "difficulty": 4.0,
                        "recent_history": [],
                        "state": 0,
                    }
                }
            return {}

        fake_db = FakeConnection(handler)
        payload = {
            "item_id": 77,
            "user_answer": "bonjour",
            "input_mode": "text",
        }

        with patch.object(study, "get_connection", return_value=fake_db), \
             patch.object(study, "_get_evaluator_service", return_value=FakeEvaluatorService()), \
             patch.object(study.PerformanceMonitor, "report"), \
             patch.object(study, "scheduler", FakeScheduler()):
            response = self.client.post("/study/evaluate", json=payload, headers=auth_headers())

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertTrue(body["data"]["isCorrect"])
        self.assertEqual(body["data"]["judgedBy"], "Regex")
        self.assertEqual(body["data"]["vectorScore"], 1.0)
        self.assertEqual(body["data"]["inputMode"], "text")
        self.assertEqual(body["data"]["expected_answers"], ["bonjour"])
        self.assertGreaterEqual(fake_db.commit_calls, 1)
        self.assertTrue(any("WHERE q.item_id = %s" in query for query, _ in fake_db.executed_queries))
        self.assertTrue(any("ON CONFLICT (user_id, item_id)" in query for query, _ in fake_db.executed_queries))
        self.assertTrue(any("course_id, lesson_id" in query and "INSERT INTO review_logs" in query for query, _ in fake_db.executed_queries))


if __name__ == "__main__":
    unittest.main()
