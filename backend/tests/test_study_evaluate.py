import unittest
from unittest.mock import patch

from .test_helpers import FakeConnection, FakeEvaluatorService, FakeScheduler, SmokeTestCaseMixin, study


class StudyEvaluateSmokeTests(SmokeTestCaseMixin, unittest.TestCase):
    def test_study_evaluate_exact_match_returns_success_payload(self):
        def handler(query, params):
            if "SELECT q.item_id as item_pk" in query:
                return {
                    "fetchone": {
                        "item_pk": 77,
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
            "user_id": "33333333-3333-3333-3333-333333333333",
            "lesson_id": 101,
            "question_id": 1001,
            "question_type": "CN_TO_EN",
            "original_text": "你好",
            "standard_answers": ["hello"],
            "user_answer": "hello",
            "input_mode": "text",
        }

        with patch.object(study, "get_connection", return_value=fake_db), \
             patch.object(study, "evaluator_service", FakeEvaluatorService()), \
             patch.object(study, "scheduler", FakeScheduler()):
            response = self.client.post("/study/evaluate", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertTrue(body["data"]["isCorrect"])
        self.assertEqual(body["data"]["judgedBy"], "Regex")
        self.assertEqual(body["data"]["vectorScore"], 1.0)
        self.assertEqual(body["data"]["inputMode"], "text")
        self.assertGreaterEqual(fake_db.commit_calls, 1)


if __name__ == "__main__":
    unittest.main()
