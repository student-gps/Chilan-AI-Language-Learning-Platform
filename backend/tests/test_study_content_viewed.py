import unittest
from unittest.mock import patch

from .test_helpers import FakeConnection, SmokeTestCaseMixin, lesson_progress_service


class StudyContentViewedSmokeTests(SmokeTestCaseMixin, unittest.TestCase):
    def test_content_viewed_marks_lesson_as_viewed(self):
        def handler(query, params):
            if "ALTER TABLE user_progress_of_lessons" in query:
                return {}
            if "INSERT INTO user_progress_of_lessons (user_id, course_id, viewed_lesson_id)" in query:
                return {}
            return {}

        fake_db = FakeConnection(handler)
        payload = {
            "user_id": "44444444-4444-4444-4444-444444444444",
            "course_id": 1,
            "lesson_id": 101,
        }

        with patch.object(lesson_progress_service, "get_connection", return_value=fake_db):
            response = self.client.post("/study/content_viewed", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertGreaterEqual(fake_db.commit_calls, 1)

        insert_queries = [query for query, _params in fake_db.executed_queries if "viewed_lesson_id" in query]
        self.assertTrue(insert_queries)


if __name__ == "__main__":
    unittest.main()
