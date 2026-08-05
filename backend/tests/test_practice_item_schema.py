import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from services.study.practice_item_schema import (
    PracticeItemSchemaError,
    canonicalize_practice_item,
)


class PracticeItemSchemaTests(unittest.TestCase):
    def test_canonical_translate_requires_explicit_languages(self):
        question_type, metadata = canonicalize_practice_item(
            "TRANSLATE",
            {
                "prompt_language": "ja",
                "answer_language": "zh",
                "feedback_language": "zh",
            },
        )

        self.assertEqual(question_type, "TRANSLATE")
        self.assertEqual(metadata["practice_schema_version"], 2)
        self.assertEqual(metadata["prompt_language"], "ja")
        self.assertEqual(metadata["answer_language"], "zh")
        self.assertEqual(metadata["feedback_language"], "zh")
        self.assertEqual(metadata["answer_mode"], "text")

    def test_canonical_speak_requires_matching_speech_language(self):
        with self.assertRaisesRegex(PracticeItemSchemaError, "speech_language"):
            canonicalize_practice_item(
                "SPEAK",
                {
                    "prompt_language": "zh",
                    "answer_language": "ja",
                    "feedback_language": "zh",
                    "speech_language": "zh",
                },
            )

    def test_legacy_direction_becomes_translate_with_retired_fields_removed(self):
        question_type, metadata = canonicalize_practice_item(
            "JA_TO_CN",
            {"target_language": "ja", "support_language": "zh"},
            defaults={"feedback_language": "zh"},
            retire_legacy_fields=True,
        )

        self.assertEqual(question_type, "TRANSLATE")
        self.assertEqual(metadata["prompt_language"], "ja")
        self.assertEqual(metadata["answer_language"], "zh")
        self.assertEqual(metadata["feedback_language"], "zh")
        self.assertNotIn("target_language", metadata)
        self.assertNotIn("support_language", metadata)

    def test_legacy_pattern_drill_uses_course_language_defaults(self):
        question_type, metadata = canonicalize_practice_item(
            "SUPPORT_TO_TARGET",
            {},
            defaults={
                "course_target_language": "en",
                "course_support_language": "zh",
                "feedback_language": "zh",
            },
        )

        self.assertEqual(question_type, "PATTERN_DRILL")
        self.assertEqual(metadata["prompt_language"], "zh")
        self.assertEqual(metadata["answer_language"], "en")
        self.assertEqual(metadata["feedback_language"], "zh")

    def test_legacy_type_without_language_context_fails(self):
        with self.assertRaisesRegex(PracticeItemSchemaError, "Cannot canonicalize"):
            canonicalize_practice_item("TARGET_TO_SUPPORT", {})

    def test_existing_skill_type_keeps_its_activity_identity(self):
        question_type, metadata = canonicalize_practice_item(
            "TONE_MARKING",
            {
                "prompt_language": "en",
                "answer_language": "zh",
                "feedback_language": "en",
            },
        )

        self.assertEqual(question_type, "TONE_MARKING")
        self.assertEqual(metadata["answer_mode"], "text")


if __name__ == "__main__":
    unittest.main()
