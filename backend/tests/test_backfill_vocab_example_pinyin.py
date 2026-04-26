import json
import tempfile
import unittest
from pathlib import Path

from backend.content_builder.backfill_vocab_example_pinyin import backfill_file


class BackfillVocabularyExamplePinyinTests(unittest.TestCase):
    def test_backfill_file_recovers_missing_example_pinyin(self):
        sample_data = {
            "course_content": {
                "dialogues": [
                    {
                        "lines": [
                            {
                                "role": "A",
                                "translation": "Hello!",
                                "words": [
                                    {"cn": "你", "py": "nǐ"},
                                    {"cn": "好", "py": "hǎo"},
                                    {"cn": "！", "py": ""},
                                ],
                            }
                        ]
                    }
                ],
                "vocabulary": [
                    {
                        "word": "好",
                        "example_sentence": {
                            "cn": "你好！",
                            "py": "",
                            "en": "Hello!",
                        },
                    }
                ],
            }
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "lesson.json"
            with open(path, "w", encoding="utf-8") as file:
                json.dump(sample_data, file, ensure_ascii=False, indent=2)

            summary = backfill_file(path, apply=True)

            self.assertEqual(summary["updated"], 1)
            self.assertEqual(summary["unresolved"], 0)

            with open(path, "r", encoding="utf-8") as file:
                updated = json.load(file)

            example = updated["course_content"]["vocabulary"][0]["example_sentence"]
            self.assertEqual(example["py"], "Nǐ hǎo!")
            self.assertEqual(
                example["tokens"],
                [
                    {"cn": "你", "py": "nǐ"},
                    {"cn": "好", "py": "hǎo"},
                    {"cn": "！", "py": ""},
                ],
            )


if __name__ == "__main__":
    unittest.main()
