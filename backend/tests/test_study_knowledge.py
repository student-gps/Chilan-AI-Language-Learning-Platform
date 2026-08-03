import unittest
from unittest.mock import patch

from .test_helpers import FakeConnection, SmokeTestCaseMixin, study
from database.utils import create_access_token


USER_ID = "11111111-1111-1111-1111-111111111111"


def auth_headers():
    return {"Authorization": f"Bearer {create_access_token({'sub': USER_ID})}"}


class StudyKnowledgeSmokeTests(SmokeTestCaseMixin, unittest.TestCase):
    def test_study_knowledge_scopes_vocabulary_history_to_current_course(self):
        same_course_rows = [
            {
                "course_id": 99,
                "lesson_id": 101,
                "word": "我",
                "pinyin": "wǒ",
                "part_of_speech": "pronoun",
                "definition": "I, me",
                "example": {"cn": "我找李。", "translation": "I'm looking for Li."},
            },
            {
                "course_id": 99,
                "lesson_id": 102,
                "word": "我",
                "pinyin": "wǒ",
                "part_of_speech": "pronoun",
                "definition": "me (object)",
                "example": {"cn": "他看见我。", "translation": "They saw me."},
            },
        ]
        leaked_cross_course_rows = same_course_rows + [
            {
                "course_id": 7,
                "lesson_id": 101,
                "word": "我",
                "pinyin": "tôi",
                "part_of_speech": "đại từ",
                "definition": "tôi",
                "example": {"cn": "我在这儿。", "translation": "Tôi ở đây."},
            },
            {
                "course_id": 8,
                "lesson_id": 101,
                "word": "我",
                "pinyin": "yo",
                "part_of_speech": "pronombre",
                "definition": "yo, me",
                "example": {"cn": "我来了。", "translation": "Yo ya vine."},
            },
        ]

        def handler(query, params):
            if "CREATE TABLE IF NOT EXISTS vocabulary_knowledge" in query:
                return {}
            if "FROM language_items" in query and "WHERE item_id = %s" in query:
                return {
                    "fetchone": {
                        "item_id": 1,
                        "course_id": 99,
                        "lesson_id": 101,
                        "question_type": "CN_TO_EN",
                        "original_text": "我",
                        "standard_answers": ["me"],
                        "metadata": {
                            "knowledge": {
                                "word": "我",
                                "pinyin": "wǒ",
                                "part_of_speech": "pronoun",
                                "definition": "I, me",
                                "example_sentence": {
                                    "cn": "我找李。",
                                    "translation": "I'm looking for Li.",
                                },
                            }
                        },
                    }
                }
            if "FROM user_courses" in query:
                return {"fetchone": (1,)}
            if "FROM vocabulary_knowledge" in query:
                if params == (99, "我", 101):
                    return {"fetchall": same_course_rows}
                if params == ("我", 101):
                    return {"fetchall": leaked_cross_course_rows}
                return {"fetchall": leaked_cross_course_rows}
            return {}

        fake_db = FakeConnection(handler)

        with patch.object(study, "get_connection", return_value=fake_db):
            response = self.client.get("/study/knowledge", params={"item_id": 1}, headers=auth_headers())

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["data"]["current_sense"]["definition"], "I, me")
        self.assertEqual(
            [entry["definition"] for entry in body["data"]["other_senses"]],
            ["me (object)"],
        )
        self.assertTrue(
            any(
                "WHERE course_id = %s AND word = %s" in query
                for query, _ in fake_db.executed_queries
            )
        )


if __name__ == "__main__":
    unittest.main()
