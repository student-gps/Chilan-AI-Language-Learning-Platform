import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))
MIGRATION_PATH = BACKEND_DIR / "database" / "migrate_practice_item_schema.py"
SPEC = importlib.util.spec_from_file_location("practice_schema_migration", MIGRATION_PATH)
MIGRATION = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MIGRATION
SPEC.loader.exec_module(MIGRATION)


class PracticeItemSchemaMigrationTests(unittest.TestCase):
    def test_canonicalize_payload_converts_direction_types_and_retires_legacy_fields(self):
        source = {
            "target_language": "ja",
            "support_language": "zh",
            "lesson_metadata": {"course_id": 303, "lesson_id": 1},
            "database_items": [
                {
                    "question_id": 1,
                    "question_type": "CN_TO_JA",
                    "original_text": "我是学生。",
                    "standard_answers": ["わたしは学生です。"],
                    "metadata": {"custom": "preserve"},
                },
                {
                    "question_id": 2,
                    "question_type": "SPEAK",
                    "original_text": "我是学生。",
                    "standard_answers": ["わたしは学生です。"],
                    "metadata": {
                        "answer_mode": "speech",
                        "target_language": "ja",
                        "support_language": "zh",
                        "speech_language": "ja",
                    },
                },
            ],
        }

        migrated, report = MIGRATION.canonicalize_payload(source)
        translate, speak = migrated["database_items"]

        self.assertEqual(report.converted, 1)
        self.assertTrue(report.changed)
        self.assertEqual(translate["question_type"], "TRANSLATE")
        self.assertEqual(translate["metadata"]["prompt_language"], "zh")
        self.assertEqual(translate["metadata"]["answer_language"], "ja")
        self.assertEqual(translate["metadata"]["feedback_language"], "zh")
        self.assertEqual(translate["metadata"]["custom"], "preserve")
        self.assertNotIn("target_language", translate["metadata"])
        self.assertNotIn("support_language", translate["metadata"])
        self.assertEqual(speak["question_type"], "SPEAK")
        self.assertEqual(speak["metadata"]["speech_language"], "ja")
        self.assertNotIn("target_language", speak["metadata"])

    def test_migration_is_idempotent_and_creates_backup_only_on_apply(self):
        source = {
            "target_language": "en",
            "support_language": "zh",
            "lesson_metadata": {"course_id": 101, "lesson_id": 1},
            "database_items": [
                {
                    "question_id": 1,
                    "question_type": "TARGET_TO_SUPPORT",
                    "original_text": "Hello.",
                    "standard_answers": ["你好。"],
                    "metadata": {},
                }
            ],
        }

        first, first_report = MIGRATION.canonicalize_payload(source)
        second, second_report = MIGRATION.canonicalize_payload(first)
        self.assertTrue(first_report.changed)
        self.assertFalse(second_report.changed)
        self.assertEqual(first, second)

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "lesson001_data.json"
            path.write_text(json.dumps(source, ensure_ascii=False), encoding="utf-8")
            dry_run = MIGRATION.migrate_file(path)
            self.assertTrue(dry_run.changed)
            self.assertFalse(MIGRATION._backup_path(path).exists())

            applied = MIGRATION.migrate_file(path, apply_json=True)
            self.assertTrue(applied.changed)
            self.assertTrue(MIGRATION._backup_path(path).exists())
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved["database_items"][0]["question_type"], "TRANSLATE")


if __name__ == "__main__":
    unittest.main()
