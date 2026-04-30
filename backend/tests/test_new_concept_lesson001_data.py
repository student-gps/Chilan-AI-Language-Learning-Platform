import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
CONTENT_BUILDER_DIR = BACKEND_DIR / "content_builder"

for path in (BACKEND_DIR, CONTENT_BUILDER_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.append(path_str)

from content_builder.pipelines.new_concept_english.tasks.content_extractor import build_lesson001_data


class NewConceptLesson001DataTests(unittest.TestCase):
    def test_lesson001_uses_clean_english_schema(self):
        lesson_data = build_lesson001_data(
            source_pdf=Path("book1.pdf"),
            lesson_pdf=Path("lesson001.pdf"),
        )

        self.assertEqual(lesson_data["schema_version"], "2.0")
        self.assertEqual(lesson_data["pipeline_id"], "new_concept_english")
        self.assertEqual(lesson_data["target_language"], "en")
        self.assertEqual(lesson_data["support_language"], "zh")
        self.assertEqual(lesson_data["lesson_metadata"]["course_id"], 101)
        self.assertEqual(lesson_data["lesson_metadata"]["course_slug"], "new_concept_english_1")
        self.assertEqual(lesson_data["lesson_metadata"]["lesson_id"], 1)
        self.assertEqual(lesson_data["lesson_metadata"]["lesson_slug"], "lesson001")

        anchor = lesson_data["course_content"]["anchor"]
        self.assertEqual(anchor["type"], "dialogue")
        self.assertEqual(len(anchor["lines"]), 7)
        self.assertEqual(anchor["lines"][0]["text"], "Excuse me!")
        self.assertIn("tokens", anchor["lines"][0])
        self.assertNotIn("cn", anchor["lines"][0]["tokens"][0])
        self.assertNotIn("py", anchor["lines"][0]["tokens"][0])

        vocabulary = lesson_data["course_content"]["vocabulary"]
        self.assertTrue(any(item["term"] == "handbag" for item in vocabulary))
        self.assertTrue(any(item["term"] == "pen" and item["role"] == "pattern_slot" for item in vocabulary))

        drills = lesson_data["course_content"]["pattern_drills"]
        self.assertEqual(drills[0]["pattern"], "Is this your {item}?")
        self.assertEqual(len(drills[0]["slots"]), 10)


if __name__ == "__main__":
    unittest.main()
