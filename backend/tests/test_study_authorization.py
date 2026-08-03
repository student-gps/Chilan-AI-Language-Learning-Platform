import unittest
from datetime import timedelta
from unittest.mock import patch

from .test_helpers import FakeConnection, SmokeTestCaseMixin, study
from database.utils import create_access_token


USER_A = "11111111-1111-1111-1111-111111111111"
USER_B = "22222222-2222-2222-2222-222222222222"


def auth_headers(user_id=USER_A):
    return {"Authorization": f"Bearer {create_access_token({'sub': user_id})}"}


class StudyAuthorizationTests(SmokeTestCaseMixin, unittest.TestCase):
    def test_study_private_endpoints_require_bearer_authentication(self):
        responses = [
            self.client.get("/study/init", params={"course_id": 1}),
            self.client.get("/study/practice_items", params={"course_id": 1, "lesson_id": 101}),
            self.client.post("/study/evaluate", json={"item_id": 1, "user_answer": "hello"}),
            self.client.post("/study/content_viewed", json={"course_id": 1, "lesson_id": 101}),
            self.client.post("/study/practice_progress", json={"course_id": 1, "lesson_id": 101, "current_index": 0}),
            self.client.post("/study/complete_lesson", json={"course_id": 1, "lesson_id": 101}),
            self.client.get("/study/knowledge", params={"item_id": 1}),
            self.client.post("/study/media/audio-url", json={"course_id": 1, "lesson_id": 101, "asset_ref": "full"}),
        ]

        for response in responses:
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.headers.get("www-authenticate"), "Bearer")

    def test_study_init_rejects_mismatched_legacy_user_id_before_database_access(self):
        fake_db = FakeConnection(lambda query, params: {})
        with patch.object(study, "get_connection", return_value=fake_db):
            response = self.client.get(
                "/study/init",
                params={"course_id": 1, "user_id": USER_B},
                headers=auth_headers(USER_A),
            )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(fake_db.executed_queries, [])

    def test_unenrolled_direct_browse_returns_teaching_only_capabilities(self):
        lesson_row = {
            "lesson_id": 101,
            "title": "Lesson 101",
            "lesson_metadata": {"title": "Lesson 101", "content_type": "dialogue"},
            "course_content": {"dialogues": []},
            "teaching_materials": {},
            "video_plan": {},
            "video_render_plan": {},
            "lesson_audio_assets": {},
            "explanation_video_urls": {},
            "llm_usage": {},
        }

        def handler(query, params):
            if "EXISTS (" in query and "is_course_enrolled" in query:
                return {"fetchone": {
                    "course_id": 1,
                    "name": "Course",
                    "category": "general",
                    "target_language": "Chinese",
                    "source_language": "English",
                    "is_course_enrolled": False,
                    "last_completed_lesson_id": 0,
                    "viewed_lesson_id": 0,
                    "practice_question_index": 0,
                }}
            if "SELECT 1" in query and "FROM lessons" in query:
                return {"fetchone": (1,)}
            if "SELECT lesson_id, title," in query:
                return {"fetchone": lesson_row}
            return {}

        fake_db = FakeConnection(handler)
        with patch.object(study, "get_connection", return_value=fake_db):
            response = self.client.get(
                "/study/init",
                params={"course_id": 1, "lesson_id": 101, "browse": 1},
                headers=auth_headers(),
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["mode"], "teaching")
        self.assertFalse(body["data"]["capabilities"]["can_practice"])
        self.assertFalse(body["data"]["capabilities"]["can_write_progress"])
        self.assertEqual(body["data"]["pending_items"], [])

    def test_practice_items_rejects_inactive_enrollment_before_item_query(self):
        def handler(query, params):
            if "SELECT 1" in query and "FROM lessons" in query:
                return {"fetchone": (1,)}
            if "FROM user_courses" in query:
                return {"fetchone": None}
            return {}

        fake_db = FakeConnection(handler)
        with patch.object(study, "get_connection", return_value=fake_db):
            response = self.client.get(
                "/study/practice_items",
                params={"course_id": 1, "lesson_id": 101},
                headers=auth_headers(),
            )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(any("FROM language_items item" in query for query, _ in fake_db.executed_queries))

    def test_audio_renewal_accepts_only_canonical_lesson_asset_reference(self):
        class Storage:
            def resolve_url(self, object_key):
                return f"https://media.example/{object_key}"

        def handler(query, params):
            if "FROM user_courses" in query:
                return {"fetchone": (1,)}
            if "SELECT lesson_audio_assets" in query:
                return {"fetchone": {
                    "lesson_audio_assets": {
                        "full_audio": {"object_key": "zh/audio/full.mp3"},
                        "items": [{"line_ref": 1, "object_key": "zh/audio/line-1.mp3"}],
                    }
                }}
            return {}

        fake_db = FakeConnection(handler)
        with patch.object(study, "get_connection", return_value=fake_db), \
             patch.object(study, "cos_media_storage", Storage()):
            accepted = self.client.post(
                "/study/media/audio-url",
                json={"course_id": 1, "lesson_id": 101, "asset_ref": "line:1"},
                headers=auth_headers(),
            )
            rejected = self.client.post(
                "/study/media/audio-url",
                json={"course_id": 1, "lesson_id": 101, "asset_ref": "../../secrets"},
                headers=auth_headers(),
            )

        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(accepted.json()["audio_url"], "https://media.example/zh/audio/line-1.mp3")
        self.assertEqual(rejected.status_code, 404)


if __name__ == "__main__":
    unittest.main()
