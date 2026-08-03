import unittest
from unittest.mock import patch

from .test_helpers import FakeConnection, SmokeTestCaseMixin, init_flow_service
from database.utils import create_access_token


USER_ID = "11111111-1111-1111-1111-111111111111"


def auth_headers():
    return {"Authorization": f"Bearer {create_access_token({'sub': USER_ID})}"}


class StudyInitSmokeTests(SmokeTestCaseMixin, unittest.TestCase):
    def test_study_init_returns_teaching_payload_for_next_lesson(self):
        def handler(query, params):
            if "EXISTS (" in query and "is_course_enrolled" in query:
                return {
                    "fetchone": {
                        "course_id": 1,
                        "name": "Course 1",
                        "category": "general",
                        "target_language": "Chinese",
                        "source_language": "English",
                        "is_course_enrolled": True,
                        "last_completed_lesson_id": 100,
                        "viewed_lesson_id": 0,
                        "practice_question_index": 1,
                    }
                }
            if "JOIN user_progress_of_language_items p" in query:
                return {"fetchall": []}
            if "SELECT lesson_id, title," in query and "FROM lessons" in query:
                return {
                    "fetchone": {
                        "lesson_id": 101,
                        "title": "Lesson 1.01",
                        "lesson_metadata": {"title": "Lesson 1.01", "content_type": "dialogue"},
                        "course_content": {
                            "dialogues": [{"lines": [{"line_ref": 1, "speaker": "A", "text": "你好"}]}],
                            "vocabulary": [{"word": "你好", "translation": "hello"}],
                        },
                        "teaching_materials": {},
                        "video_plan": {"dramatization": {}},
                        "video_render_plan": {"explanation": {}},
                        "lesson_audio_assets": {},
                        "explanation_video_urls": {},
                        "llm_usage": {},
                    }
                }
            if "SELECT lesson_id" in query and "FROM lessons" in query:
                return {"fetchone": {"lesson_id": 101}}
            if "FROM language_items" in query and "ORDER BY question_id ASC" in query:
                return {
                    "fetchall": [
                        {
                            "item_id": 1,
                            "question_id": 1001,
                            "question_type": "CN_TO_EN",
                            "original_text": "你好",
                            "original_pinyin": "ni hao",
                            "standard_answers": ["hello"],
                            "metadata": {},
                            "lesson_id": 101,
                        },
                        {
                            "item_id": 2,
                            "question_id": 1002,
                            "question_type": "EN_TO_CN",
                            "original_text": "hello",
                            "original_pinyin": "",
                            "standard_answers": ["你好"],
                            "metadata": {},
                            "lesson_id": 101,
                        },
                    ]
                }
            return {}

        fake_db = FakeConnection(handler)

        with patch.object(init_flow_service, "get_connection", return_value=fake_db):
            response = self.client.get(
                "/study/init",
                params={"user_id": USER_ID, "course_id": 1},
                headers=auth_headers(),
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["mode"], "teaching")
        self.assertFalse(body["data"]["skip_content"])
        self.assertEqual(body["data"]["practice_resume_index"], 1)
        self.assertEqual(body["data"]["lesson_content"]["lesson_metadata"]["lesson_id"], 101)
        self.assertNotIn("teaching_slide_deck", body["data"]["lesson_content"])
        self.assertEqual(len(body["data"]["pending_items"]), 2)

    def test_practice_items_use_one_query_and_keep_resume_index(self):
        def handler(query, params):
            if "FROM user_courses" in query:
                return {"fetchone": (1,)}
            if "SELECT 1" in query and "FROM lessons" in query:
                return {"fetchone": (1,)}
            if "WITH progress AS" in query:
                return {
                    "fetchall": [
                        {
                            "practice_question_index": 1,
                            "item_id": 1,
                            "course_id": 1,
                            "lesson_id": 101,
                            "question_id": 1001,
                            "question_type": "CN_TO_EN",
                            "original_text": "你好",
                            "original_pinyin": "ni hao",
                            "standard_answers": ["hello"],
                            "metadata": {},
                        },
                        {
                            "practice_question_index": 1,
                            "item_id": 2,
                            "course_id": 1,
                            "lesson_id": 101,
                            "question_id": 1002,
                            "question_type": "EN_TO_CN",
                            "original_text": "hello",
                            "original_pinyin": "",
                            "standard_answers": ["你好"],
                            "metadata": {},
                        },
                    ]
                }
            return {}

        fake_db = FakeConnection(handler)

        with patch.object(init_flow_service, "get_connection", return_value=fake_db):
            result = init_flow_service.load_lesson_practice_items("u-1", 1, 101)

        self.assertEqual(len(fake_db.executed_queries), 3)
        query, params = fake_db.executed_queries[-1]
        self.assertIn("WITH progress AS", query)
        self.assertIn("ORDER BY item.question_id ASC, item.item_id ASC", query)
        self.assertEqual(params, ("u-1", 1, 101, 1, 101))
        self.assertEqual(result["practice_resume_index"], 1)
        self.assertEqual([item["item_id"] for item in result["pending_items"]], [1, 2])
        self.assertTrue(all("practice_question_index" not in item for item in result["pending_items"]))

    def test_lesson_cache_returns_deep_copies(self):
        init_flow_service.clear_lesson_row_cache()
        source = {
            "lesson_id": 101,
            "lesson_audio_assets": {"items": [{"object_key": "audio.mp3"}]},
        }
        init_flow_service._put_cached_lesson_row(1, 101, source)

        first = init_flow_service._get_cached_lesson_row(1, 101)
        first["lesson_audio_assets"]["items"][0]["audio_url"] = "signed-url"
        second = init_flow_service._get_cached_lesson_row(1, 101)

        self.assertNotIn("audio_url", second["lesson_audio_assets"]["items"][0])
        init_flow_service.clear_lesson_row_cache()


if __name__ == "__main__":
    unittest.main()
