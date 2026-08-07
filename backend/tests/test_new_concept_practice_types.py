import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from services.llm.prompts import get_eval_prompt


class CanonicalPracticePromptTests(unittest.TestCase):
    def test_canonical_types_render_languages_from_metadata(self):
        cases = [
            (
                "TRANSLATE",
                {"prompt_language": "ja", "answer_language": "zh", "feedback_language": "zh"},
                ("translation from Japanese to Chinese", "explanation\" MUST be in Chinese"),
            ),
            (
                "SPEAK",
                {
                    "prompt_language": "zh",
                    "answer_language": "ja",
                    "feedback_language": "zh",
                    "answer_mode": "speech",
                    "speech_language": "ja",
                },
                ("spoken Japanese answer", "explanation\" MUST be in Chinese"),
            ),
            (
                "LISTEN_WRITE",
                {
                    "prompt_language": "fr",
                    "answer_language": "ja",
                    "feedback_language": "fr",
                    "audio_language": "ja",
                },
                ("Japanese dictation answer", "explanation\" MUST be in French"),
            ),
            (
                "PATTERN_DRILL",
                {"prompt_language": "zh", "answer_language": "en", "feedback_language": "zh"},
                ("English Pattern Coach", "explanation\" MUST be in Chinese"),
            ),
        ]

        for question_type, metadata, markers in cases:
            with self.subTest(question_type=question_type):
                prompt = get_eval_prompt(question_type, metadata)
                for marker in markers:
                    self.assertIn(marker, prompt)

    def test_course_support_language_controls_feedback_language(self):
        prompt = get_eval_prompt(
            "TRANSLATE",
            {
                "prompt_language": "zh",
                "answer_language": "en",
                "feedback_language": "english",
            },
        )

        self.assertIn('The "explanation" MUST be in English.', prompt)
        self.assertIn('Address the student with "you".', prompt)

    def test_incorrect_feedback_includes_expected_answer_instruction(self):
        cases = [
            (
                "TRANSLATE",
                {"prompt_language": "zh", "answer_language": "en", "feedback_language": "en"},
                "begin with “A correct answer is” and quote one or two appropriate answers",
            ),
            (
                "SPEAK",
                {
                    "prompt_language": "zh",
                    "answer_language": "en",
                    "feedback_language": "en",
                    "speech_language": "en",
                },
                "begin with “A correct answer is” and quote one or two appropriate answers",
            ),
            (
                "LISTEN_WRITE",
                {
                    "prompt_language": "zh",
                    "answer_language": "en",
                    "feedback_language": "en",
                    "audio_language": "en",
                },
                "begin with “The corrected sentence is” and quote the most appropriate",
            ),
            (
                "PATTERN_DRILL",
                {"prompt_language": "zh", "answer_language": "en", "feedback_language": "en"},
                "begin with “A correct answer is” and quote one or two appropriate answers",
            ),
        ]

        for question_type, metadata, correction_rule in cases:
            with self.subTest(question_type=question_type):
                prompt = get_eval_prompt(question_type, metadata)
                self.assertIn("Keep exactly 2 short sentences", prompt)
                self.assertIn(correction_rule, prompt)

    def test_request_values_are_only_in_final_evaluation_input(self):
        cases = [
            ("TRANSLATE", {"prompt_language": "en", "answer_language": "zh", "feedback_language": "zh"}),
            (
                "SPEAK",
                {
                    "prompt_language": "zh",
                    "answer_language": "ja",
                    "feedback_language": "zh",
                    "speech_language": "ja",
                },
            ),
            (
                "LISTEN_WRITE",
                {
                    "prompt_language": "zh",
                    "answer_language": "en",
                    "feedback_language": "zh",
                    "audio_language": "en",
                },
            ),
            ("PATTERN_DRILL", {"prompt_language": "zh", "answer_language": "en", "feedback_language": "zh"}),
        ]
        question = "__QUESTION_SENTINEL__"
        standards = ["__STANDARD_SENTINEL__"]
        user_answer = "__ANSWER_SENTINEL__"

        for question_type, metadata in cases:
            with self.subTest(question_type=question_type):
                prompt = get_eval_prompt(question_type, metadata).format(
                    question=question,
                    standards=standards,
                    user_answer=user_answer,
                )
                input_start = prompt.rindex("# Evaluation Input:")

                self.assertLess(prompt.index("# Output Format:"), input_start)
                self.assertLess(input_start, prompt.index(question))
                self.assertLess(prompt.index(question), prompt.index("__STANDARD_SENTINEL__"))
                self.assertLess(prompt.index("__STANDARD_SENTINEL__"), prompt.index(user_answer))
                self.assertTrue(prompt.rstrip().endswith(f'"{user_answer}"'))


if __name__ == "__main__":
    unittest.main()
