import unittest
from unittest.mock import patch

from .test_helpers import FakeConnection, SmokeTestCaseMixin, lesson_progress_service


class StudyCompleteLessonSmokeTests(SmokeTestCaseMixin, unittest.TestCase):
    def test_complete_lesson_marks_lesson_complete_and_resets_progress(self):
        def handler(query, params):
            if "ALTER TABLE user_progress_of_lessons" in query:
                return {}
            if "INSERT INTO user_progress_of_lessons (user_id, course_id, last_completed_lesson_id)" in query:
                return {}
            return {}

        fake_db = FakeConnection(handler)
        payload = {
            "user_id": "55555555-5555-5555-5555-555555555555",
            "course_id": 1,
            "lesson_id": 101,
        }

        with patch.object(lesson_progress_service, "get_connection", return_value=fake_db):
            response = self.client.post("/study/complete_lesson", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertIn("Lesson 101 marked as completed.", body["message"])
        self.assertGreaterEqual(fake_db.commit_calls, 1)

        update_queries = [query for query, _params in fake_db.executed_queries if "last_completed_lesson_id" in query]
        self.assertTrue(update_queries)


if __name__ == "__main__":
    unittest.main()
