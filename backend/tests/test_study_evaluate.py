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
                        "course_support_language": "french",
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
        self.assertTrue(any("JOIN courses c ON c.course_id = q.course_id" in query for query, _ in fake_db.executed_queries))
        self.assertTrue(any("WHERE q.item_id = %s" in query for query, _ in fake_db.executed_queries))
        self.assertTrue(any("ON CONFLICT (user_id, item_id)" in query for query, _ in fake_db.executed_queries))
        self.assertTrue(any("course_id, lesson_id" in query and "INSERT INTO review_logs" in query for query, _ in fake_db.executed_queries))
        review_log_query, review_log_params = next(
            (query, params)
            for query, params in fake_db.executed_queries
            if "INSERT INTO review_logs" in query
        )
        self.assertIn("forfeited", review_log_query)
        self.assertFalse(review_log_params[10])

    def test_study_evaluate_forfeit_records_text_mode_and_forfeited_flag(self):
        def handler(query, params):
            if "FROM user_courses" in query:
                return {"fetchone": (1,)}
            if "SELECT q.item_id as item_pk" in query:
                return {
                    "fetchone": {
                        "item_pk": 79,
                        "question_id": 1003,
                        "course_id": 2,
                        "lesson_id": 101,
                        "question_type": "CN_TO_EN",
                        "original_text": "王朋",
                        "standard_answers": ["Wang Peng"],
                        "item_metadata": {},
                        "course_support_language": "english",
                        "stability": 0.6,
                        "difficulty": 4.0,
                        "recent_history": [],
                        "state": 0,
                    }
                }
            return {}

        fake_db = FakeConnection(handler)

        with patch.object(study, "get_connection", return_value=fake_db), \
             patch.object(study, "_get_evaluator_service", return_value=FakeEvaluatorService()), \
             patch.object(study, "scheduler", FakeScheduler()):
            response = self.client.post(
                "/study/evaluate",
                json={"item_id": 79, "user_answer": "", "input_mode": "text", "forfeit": True},
                headers=auth_headers(),
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["data"]["forfeited"])
        self.assertEqual(body["data"]["expected_answers"], ["Wang Peng"])
        self.assertEqual(body["data"]["inputMode"], "text")
        review_log_query, review_log_params = next(
            (query, params)
            for query, params in fake_db.executed_queries
            if "INSERT INTO review_logs" in query
        )
        self.assertIn("forfeited", review_log_query)
        self.assertEqual(review_log_params[9], "text")
        self.assertTrue(review_log_params[10])

    def test_study_evaluate_uses_course_support_language_for_llm_feedback(self):
        class CapturingEvaluator(FakeEvaluatorService):
            async def process_judge(self, **kwargs):
                self.received_metadata = kwargs["item_metadata"]
                return {
                    "level": 2,
                    "isCorrect": False,
                    "message": "Try again.",
                    "judgedBy": "LLM Mentor",
                }

        evaluator = CapturingEvaluator()

        def handler(query, params):
            if "FROM user_courses" in query:
                return {"fetchone": (1,)}
            if "SELECT q.item_id as item_pk" in query:
                return {
                    "fetchone": {
                        "item_pk": 78,
                        "question_id": 1002,
                        "course_id": 2,
                        "lesson_id": 101,
                        "question_type": "TRANSLATE",
                        "original_text": "好",
                        "standard_answers": ["fine", "good"],
                        "item_metadata": {
                            "prompt_language": "zh",
                            "answer_language": "en",
                            "feedback_language": "zh",
                        },
                        "course_support_language": "english",
                        "stability": 0.6,
                        "difficulty": 4.0,
                        "recent_history": [],
                        "state": 0,
                    }
                }
            if "SELECT 1 - (ae.primary_embedding" in query:
                return {"fetchone": {"sim_score": 0.5}}
            return {}

        fake_db = FakeConnection(handler)
        fake_tools = type("FakeTools", (), {"get_embedding": self._get_embedding})()

        with patch.object(study, "get_connection", return_value=fake_db), \
             patch.object(study, "_get_evaluator_service", return_value=evaluator), \
             patch.object(study, "_get_llm_tools", return_value=fake_tools), \
             patch.object(study.PerformanceMonitor, "report"), \
             patch.object(study, "scheduler", FakeScheduler()):
            response = self.client.post(
                "/study/evaluate",
                json={"item_id": 78, "user_answer": "bien", "input_mode": "text"},
                headers=auth_headers(),
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(evaluator.received_metadata["feedback_language"], "english")
        self.assertEqual(evaluator.received_metadata["prompt_language"], "zh")
        self.assertEqual(evaluator.received_metadata["answer_language"], "en")

    @staticmethod
    async def _get_embedding(*args, **kwargs):  # noqa: ARG004
        return [0.0]


if __name__ == "__main__":
    unittest.main()
