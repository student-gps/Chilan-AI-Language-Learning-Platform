from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from content_builder.ja.minna_no_nihongo.tasks.practice_generator import MinnaNoNihongoPracticeGenerator
from content_builder.ja.minna_no_nihongo.tasks.vocab_memory import MinnaNoNihongoVocabMemory


class _SequenceProvider:
    def __init__(self, responses):
        self.responses = list(responses)
        self.prompts = []

    def generate_structured_json(self, prompt, file_path=None, file_obj=None):  # noqa: ARG002
        self.prompts.append(prompt)
        return self.responses.pop(0) if self.responses else {}


class MnnVocabExampleBackfillTests(unittest.TestCase):
    def _payload(self, vocabulary, *, dialogue=None):
        return {
            "lesson_metadata": {"lesson_id": 1, "lesson_slug": "lesson001", "course_id": 303},
            "course_content": {
                "sentence_patterns": [],
                "example_sentences": [],
                "dialogue": {"lines": dialogue or []},
                "vocabulary": vocabulary,
            },
        }

    def test_normalized_matching_handles_textbook_spacing_and_tracks_provenance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = MinnaNoNihongoVocabMemory(Path(tmpdir))
            payload = self._payload(
                [{"term": "おはようございます", "reading": "おはようございます", "translation": "早上好"}],
                dialogue=[{
                    "line_ref": 1,
                    "text": "おはよう　ございます。",
                    "reading": "おはようございます。",
                    "translation": "早上好。",
                }],
            )

            annotated = memory.annotate_lesson(payload)
            example = annotated["course_content"]["vocabulary"][0]["example_sentence"]

            self.assertEqual(example["text"], "おはよう　ございます。")
            self.assertEqual(example["source_section"], "dialogue")
            self.assertEqual(example["source_ref"], 1)
            self.assertEqual(example["match_method"], "normalized")

    def test_llm_backfill_can_only_select_and_rehydrate_real_source_candidate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = MinnaNoNihongoVocabMemory(Path(tmpdir))
            selector = _SequenceProvider([{
                "decisions": [{"vocab_index": 0, "candidate_id": "dialogue:3", "confidence": "high"}],
            }])
            reviewer = _SequenceProvider([{
                "reviews": [{"review_index": 0, "candidate_id": "dialogue:3", "approved": True}],
            }])
            payload = self._payload(
                [{
                    "term": "これからお世話になります",
                    "reading": "これからおせわになります",
                    "translation": "今后请您多关照",
                }],
                dialogue=[{
                    "line_ref": 3,
                    "text": "今後、ご指導をいただきます。",
                    "reading": "こんご、ごしどうをいただきます。",
                    "translation": "今后请您多关照。",
                }],
            )

            annotated = memory.annotate_lesson(payload, llm_provider=selector, reviewer_provider=reviewer)
            example = annotated["course_content"]["vocabulary"][0]["example_sentence"]

            self.assertEqual(example["text"], "今後、ご指導をいただきます。")
            self.assertEqual(example["source_section"], "dialogue")
            self.assertEqual(example["source_ref"], 3)
            self.assertEqual(example["match_method"], "llm_verified")
            self.assertEqual(len(selector.prompts), 1)
            self.assertEqual(len(reviewer.prompts), 1)

    def test_llm_reviewer_rejection_leaves_example_unfilled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = MinnaNoNihongoVocabMemory(Path(tmpdir))
            selector = _SequenceProvider([{
                "decisions": [{"vocab_index": 0, "candidate_id": "dialogue:1", "confidence": "high"}],
            }])
            reviewer = _SequenceProvider([{
                "reviews": [{"review_index": 0, "candidate_id": "dialogue:1", "approved": False}],
            }])
            payload = self._payload(
                [{"term": "お世話になります", "reading": "おせわになります", "translation": "承蒙关照"}],
                dialogue=[{"line_ref": 1, "text": "今後、ご指導をいただきます。", "translation": "今后请您多关照。"}],
            )

            annotated = memory.annotate_lesson(payload, llm_provider=selector, reviewer_provider=reviewer)
            vocab = annotated["course_content"]["vocabulary"][0]

            self.assertNotIn("example_sentence", vocab)
            summary = annotated["pipeline_diagnostics"]["vocab_memory"]["example_backfill"]
            self.assertEqual(summary["llm_matched"], 0)
            self.assertEqual(summary["llm_rejected"], 1)

    def test_llm_invalid_candidate_id_is_rejected_without_writing_an_example(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = MinnaNoNihongoVocabMemory(Path(tmpdir))
            selector = _SequenceProvider([{
                "decisions": [{"vocab_index": 0, "candidate_id": "dialogue:999", "confidence": "high"}],
            }])
            reviewer = _SequenceProvider([{}])
            payload = self._payload(
                [{"term": "対象語", "reading": "たいしょうご", "translation": "目标词"}],
                dialogue=[{"line_ref": 1, "text": "候補の文です。", "translation": "候选句。"}],
            )

            annotated = memory.annotate_lesson(payload, llm_provider=selector, reviewer_provider=reviewer)

            self.assertNotIn("example_sentence", annotated["course_content"]["vocabulary"][0])
            self.assertEqual(len(reviewer.prompts), 0)

        with tempfile.TemporaryDirectory() as tmpdir:
            memory = MinnaNoNihongoVocabMemory(Path(tmpdir))
            payload = self._payload([
                {"term": "補充語", "reading": "ほじゅうご", "translation": "补充词"},
            ])

            memory.save_lesson_vocabulary(payload)
            stored = json.loads(memory.memory_file.read_text(encoding="utf-8"))

            self.assertNotIn("example", stored["補充語"][0])

    def test_vocabulary_context_deduplicates_visible_current_and_historical_example(self):
        generator = MinnaNoNihongoPracticeGenerator()
        examples = generator._context_examples_for_vocab({
            "example_sentence": {
                "text": "どうも。",
                "reading": "どうも。",
                "translation": "谢谢。",
                "source_section": "dialogue",
                "source_ref": 2,
            },
            "historical_examples": [{
                "text": "どうも。",
                "reading": "どうも。",
                "translation": "谢谢。",
                "source_section": "sentence_patterns",
                "source_ref": 1,
            }],
        })

        self.assertEqual(len(examples), 1)
        self.assertEqual(examples[0]["source_section"], "dialogue")

    def test_vocabulary_context_keeps_distinct_history_after_current_example(self):
        generator = MinnaNoNihongoPracticeGenerator()
        examples = generator._context_examples_for_vocab({
            "example_sentence": {"text": "どうも。", "reading": "どうも。", "translation": "谢谢。"},
            "historical_examples": [
                {"text": "どうも すみません。", "reading": "どうも すみません。", "translation": "实在抱歉。"},
            ],
        })

        self.assertEqual([item["text"] for item in examples], ["どうも。", "どうも すみません。"])


if __name__ == "__main__":
    unittest.main()
