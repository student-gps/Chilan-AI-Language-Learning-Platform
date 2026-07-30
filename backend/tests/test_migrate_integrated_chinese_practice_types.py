import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
MIGRATION_PATH = BACKEND_DIR / "database" / "migrate_integrated_chinese_practice_types.py"
SPEC = importlib.util.spec_from_file_location("practice_type_migration", MIGRATION_PATH)
MIGRATION = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MIGRATION
SPEC.loader.exec_module(MIGRATION)


class IntegratedChinesePracticeTypeMigrationTests(unittest.TestCase):
    def test_english_legacy_items_become_canonical_with_metadata(self):
        source = {
            "database_items": [
                {
                    "question_id": 31,
                    "question_type": "CN_LISTEN_WRITE",
                    "original_text": "Hello.",
                    "original_pinyin": "nǐ hǎo",
                    "standard_answers": ["你好。"],
                    "metadata": {"line_ref": 7, "context": {"line_ref": 7}},
                },
                {
                    "question_id": 32,
                    "question_type": "EN_TO_CN_SPEAK",
                    "original_text": "Hello.",
                    "original_pinyin": "nǐ hǎo",
                    "standard_answers": ["你好。"],
                    "metadata": {"speech_eval_config": {"pass_threshold": 0.88}},
                },
            ]
        }

        migrated, report = MIGRATION.canonicalize_payload(source, "en")
        listen_write, speak = migrated["database_items"]

        self.assertEqual(listen_write["question_type"], "LISTEN_WRITE")
        self.assertEqual(listen_write["metadata"]["line_ref"], 7)
        self.assertEqual(listen_write["metadata"]["target_language"], "zh")
        self.assertEqual(listen_write["metadata"]["support_language"], "en")
        self.assertEqual(listen_write["metadata"]["audio_language"], "zh")

        self.assertEqual(speak["question_type"], "SPEAK")
        self.assertEqual(speak["metadata"]["answer_mode"], "speech")
        self.assertEqual(speak["metadata"]["target_language"], "zh")
        self.assertEqual(speak["metadata"]["support_language"], "en")
        self.assertEqual(speak["metadata"]["speech_language"], "zh")
        self.assertEqual(speak["metadata"]["audio_language"], "en")
        self.assertEqual(speak["metadata"]["speech_eval_config"], {"pass_threshold": 0.88})
        self.assertEqual(report.legacy_speak, 1)
        self.assertEqual(report.legacy_listen_write, 1)

    def test_localized_speaking_type_uses_source_language_from_type(self):
        source = {
            "localization": {"target_lang": "fr"},
            "database_items": [
                {
                    "question_id": 9,
                    "question_type": "FR_TO_CN_SPEAK",
                    "original_text": "Bonjour.",
                    "standard_answers": ["你好。"],
                    "metadata": {},
                }
            ],
        }

        migrated, report = MIGRATION.canonicalize_payload(source, "fr")
        item = migrated["database_items"][0]

        self.assertEqual(item["question_type"], "SPEAK")
        self.assertEqual(item["metadata"]["support_language"], "fr")
        self.assertEqual(item["metadata"]["audio_language"], "fr")
        self.assertEqual(report.legacy_speak, 1)

    def test_canonical_item_only_repairs_missing_metadata_and_is_idempotent(self):
        source = {
            "database_items": [
                {
                    "question_id": 7,
                    "question_type": "SPEAK",
                    "original_text": "Hello.",
                    "standard_answers": ["你好。"],
                    "metadata": {"support_language": "en", "custom": "preserve"},
                }
            ]
        }

        first, first_report = MIGRATION.canonicalize_payload(source, "en")
        second, second_report = MIGRATION.canonicalize_payload(first, "en")

        self.assertEqual(first["database_items"][0]["metadata"]["custom"], "preserve")
        self.assertEqual(first_report.metadata_repaired, 1)
        self.assertFalse(second_report.changed)
        self.assertEqual(first, second)

    def test_unresolvable_support_language_is_reported_without_mutation(self):
        source = {
            "database_items": [
                {
                    "question_id": 1,
                    "question_type": "SPEAK",
                    "original_text": "Prompt",
                    "standard_answers": ["答案"],
                    "metadata": {},
                }
            ]
        }

        migrated, report = MIGRATION.canonicalize_payload(source, "")

        self.assertEqual(migrated, source)
        self.assertFalse(report.changed)
        self.assertTrue(report.unresolved)

    def test_apply_creates_backup_and_preserves_question_identity(self):
        source = {
            "database_items": [
                {
                    "question_id": 12,
                    "question_type": "EN_TO_CN_SPEAK",
                    "original_text": "How are you?",
                    "original_pinyin": "nǐ hǎo ma",
                    "standard_answers": ["你好吗？"],
                    "metadata": {"speech_eval_config": {"max_attempts": 3}},
                }
            ]
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "lesson101_data.json"
            path.write_text(json.dumps(source, ensure_ascii=False), encoding="utf-8")

            report = MIGRATION.migrate_file(path, "en", apply_json=True, overwrite_backup=False)
            backup = MIGRATION._backup_path(path)
            migrated = json.loads(path.read_text(encoding="utf-8"))
            original = json.loads(backup.read_text(encoding="utf-8"))

        self.assertTrue(report.changed)
        self.assertTrue(backup.name.endswith(".speaking-migration-backup.json"))
        self.assertEqual(original["database_items"][0]["question_id"], 12)
        self.assertEqual(migrated["database_items"][0]["question_id"], 12)
        self.assertEqual(migrated["database_items"][0]["standard_answers"], ["你好吗？"])
        self.assertEqual(migrated["database_items"][0]["question_type"], "SPEAK")


if __name__ == "__main__":
    unittest.main()
