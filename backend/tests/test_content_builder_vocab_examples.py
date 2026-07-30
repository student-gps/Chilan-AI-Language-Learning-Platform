import sys
import types
import unittest
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
CONTENT_BUILDER_DIR = BACKEND_DIR / "content_builder"

for path in (BACKEND_DIR, CONTENT_BUILDER_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.append(path_str)

if "json_repair" not in sys.modules:
    json_repair_mod = types.ModuleType("json_repair")
    json_repair_mod.repair_json = lambda text, **kwargs: text  # noqa: ARG005
    sys.modules["json_repair"] = json_repair_mod

from content_builder.zh.integrated_chinese.agent import _normalize_dialogues
from content_builder.zh.integrated_chinese.tasks.quiz_generator import Task2QuizGenerator
from content_builder.zh.integrated_chinese.tasks.schema_validator import (
    IntegratedChineseStage1Validator,
    normalize_stage1_output,
)


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
                    "tokens": [
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

    def test_normalize_stage1_output_injects_stable_defaults(self):
        payload = {
            "lesson_metadata": {"title": "第101课"},
            "course_content": {
                "dialogues": [{"lines": [{"role": "A", "translation": "Hello!", "words": [{"cn": "你", "py": "nǐ"}]}]}],
            },
            "video_render_plan": {},
        }

        normalized = normalize_stage1_output(payload, lesson_id=101, course_id=1, support_language="en")

        self.assertEqual(normalized["schema_version"], "2.0")
        self.assertEqual(normalized["pipeline_id"], "integrated_chinese")
        self.assertEqual(normalized["target_language"], "zh")
        self.assertEqual(normalized["support_language"], "en")
        self.assertEqual(normalized["lesson_metadata"]["lesson_id"], 101)
        self.assertEqual(normalized["lesson_metadata"]["course_id"], 1)
        self.assertIsInstance(normalized["course_content"]["vocabulary"], list)
        self.assertIsInstance(normalized["database_items"], list)
        self.assertIsInstance(normalized["teaching_materials"], dict)
        self.assertIsInstance(normalized["lesson_audio_assets"]["items"], list)
        self.assertIsInstance(normalized["video_render_plan"]["explanation"]["segments"], list)
        self.assertEqual(normalized["video_render_plan"]["explanation"]["video_style"]["aspect_ratio"], "16:9")

    def test_stage1_validator_rejects_missing_metadata(self):
        validator = IntegratedChineseStage1Validator()
        with self.assertRaisesRegex(ValueError, "lesson_metadata.lesson_id missing"):
            validator.validate(
                normalize_stage1_output(
                    {"lesson_metadata": {"course_id": 1}, "course_content": {"dialogues": [], "vocabulary": []}, "teaching_materials": {}, "database_items": [], "video_render_plan": {"explanation": {"segments": [], "timeline": {}}}, "lesson_audio_assets": {"items": []}},
                    lesson_id=0,
                    course_id=1,
                    support_language="en",
                )
            )

    def test_profile_non_quiz_terms_and_sort_order_drive_behavior(self):
        self.assertFalse(
            self.generator._is_standalone_quizable_vocab(
                {
                    "word": "呢",
                    "part_of_speech": "particle",
                    "definition": "question particle",
                }
            )
        )

        items = [
            {"question_type": "SPEAK", "original_text": "Speak", "standard_answers": ["说"]},
            {"question_type": "LISTEN_WRITE", "original_text": "听写", "standard_answers": ["听写"]},
            {"question_type": "CN_TO_EN", "original_text": "你好", "standard_answers": ["hello"]},
            {"question_type": "EN_TO_CN", "original_text": "hello", "standard_answers": ["你好"]},
        ]
        sort_order = self.generator.exercise_sort_order
        sorted_items = sorted(items, key=lambda item: (sort_order.get(item["question_type"], 999), item["question_type"]))
        self.assertEqual([item["question_type"] for item in sorted_items], ["CN_TO_EN", "EN_TO_CN", "LISTEN_WRITE", "SPEAK"])


if __name__ == "__main__":
    unittest.main()
