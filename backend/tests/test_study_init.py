import unittest
from unittest.mock import patch

from .test_helpers import FakeConnection, SmokeTestCaseMixin, study


class StudyInitSmokeTests(SmokeTestCaseMixin, unittest.TestCase):
    def test_study_init_returns_teaching_payload_for_next_lesson(self):
        def handler(query, params):
            if "ALTER TABLE user_progress_of_lessons" in query:
                return {}
            if "JOIN user_progress_of_language_items p" in query:
                return {"fetchall": []}
            if "SELECT last_completed_lesson_id, viewed_lesson_id, practice_question_index" in query:
                return {
                    "fetchone": {
                        "last_completed_lesson_id": 100,
                        "viewed_lesson_id": 0,
                        "practice_question_index": 1,
                    }
                }
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

        with patch.object(study, "get_connection", return_value=fake_db):
            response = self.client.get("/study/init", params={"user_id": "u-1", "course_id": 1})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["mode"], "teaching")
        self.assertFalse(body["data"]["skip_content"])
        self.assertEqual(body["data"]["practice_resume_index"], 1)
        self.assertEqual(body["data"]["lesson_content"]["lesson_metadata"]["lesson_id"], 101)
        self.assertEqual(len(body["data"]["pending_items"]), 2)


if __name__ == "__main__":
    unittest.main()
