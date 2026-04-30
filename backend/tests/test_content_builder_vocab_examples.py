import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
CONTENT_BUILDER_DIR = BACKEND_DIR / "content_builder"

for path in (BACKEND_DIR, CONTENT_BUILDER_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.append(path_str)

from content_builder.content_agent import _normalize_dialogues
from content_builder.tasks.quiz_generator import Task2QuizGenerator


class DummyLLMProvider:
    pass


class ContentBuilderVocabularyExampleTests(unittest.TestCase):
    def setUp(self):
        self.generator = Task2QuizGenerator(DummyLLMProvider(), BACKEND_DIR / "content_builder")

    def test_normalize_dialogues_preserves_line_pinyin(self):
        dialogues = [
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
        ]

        normalized = _normalize_dialogues(dialogues)

        self.assertEqual(
            normalized,
            [
                {
                    "role": "A",
                    "chinese": "你好！",
                    "pinyin": "nǐ hǎo",
                    "translation": "Hello!",
                    "words": [
                        {"cn": "你", "py": "nǐ"},
                        {"cn": "好", "py": "hǎo"},
                        {"cn": "！", "py": ""},
                    ],
                }
            ],
        )

    def test_attach_examples_backfills_missing_pinyin_from_dialogues(self):
        vocab_batch = [
            {
                "word": "好",
                "pinyin": "Hǎo",
                "part_of_speech": "Adjective",
                "definition": "fine, good, nice, OK, it's settled",
            }
        ]
        example_batch = [
            {
                "cn": "你好！",
                "py": "",
                "en": "Hello!",
            }
        ]
        source_dialogues = [
            {
                "role": "A",
                "chinese": "你好！",
                "pinyin": "nǐ hǎo",
                "translation": "Hello!",
                "words": [
                    {"cn": "你", "py": "nǐ"},
                    {"cn": "好", "py": "hǎo"},
                    {"cn": "！", "py": ""},
                ],
            }
        ]

        merged = self.generator._attach_examples_with_fallback(
            vocab_batch,
            example_batch,
            source_dialogues,
        )

        self.assertEqual(merged[0]["example_sentence"]["cn"], "你好！")
        self.assertEqual(merged[0]["example_sentence"]["py"], "nǐ hǎo")
        self.assertEqual(merged[0]["example_sentence"]["translation"], "Hello!")
        self.assertEqual(
            merged[0]["example_sentence"]["tokens"],
            [
                {"cn": "你", "py": "nǐ"},
                {"cn": "好", "py": "hǎo"},
                {"cn": "！", "py": ""},
            ],
        )

    def test_attach_examples_backfills_tokens_from_dialogue_substring(self):
        vocab_batch = [
            {
                "word": "姓",
                "pinyin": "Xìng",
                "part_of_speech": "Verb/Noun",
                "definition": "family name",
            }
        ]
        example_batch = [
            {
                "cn": "我姓李。",
                "py": "Wǒ xìng Lǐ.",
                "en": "My surname is Li.",
            }
        ]
        source_dialogues = [
            {
                "role": "B",
                "chinese": "我姓李。你呢？",
                "pinyin": "wǒ xìng lǐ. nǐ ne?",
                "translation": "My surname is Li. And you?",
                "words": [
                    {"cn": "我", "py": "wǒ"},
                    {"cn": "姓", "py": "xìng"},
                    {"cn": "李", "py": "lǐ"},
                    {"cn": "。", "py": ""},
                    {"cn": "你", "py": "nǐ"},
                    {"cn": "呢", "py": "ne"},
                    {"cn": "？", "py": ""},
                ],
            }
        ]

        merged = self.generator._attach_examples_with_fallback(
            vocab_batch,
            example_batch,
            source_dialogues,
        )

        self.assertEqual(merged[0]["example_sentence"]["translation"], "My surname is Li.")
        self.assertEqual(
            merged[0]["example_sentence"]["tokens"],
            [
                {"cn": "我", "py": "wǒ"},
                {"cn": "姓", "py": "xìng"},
                {"cn": "李", "py": "lǐ"},
                {"cn": "。", "py": ""},
            ],
        )


if __name__ == "__main__":
    unittest.main()
