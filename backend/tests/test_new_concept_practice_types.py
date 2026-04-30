import unittest
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from services.llm.prompts import get_eval_prompt


class NewConceptPracticeTypePromptTests(unittest.TestCase):
    def test_new_concept_question_types_have_targeted_prompts(self):
        expected_markers = {
            "PATTERN_DRILL": "correct English pattern sentence",
            "TARGET_TO_SUPPORT": "translation from English to Chinese",
            "TARGET_LISTEN_WRITE": "English dictation",
            "TARGET_SPEAK": "spoken English answer",
        }

        for question_type, marker in expected_markers.items():
            with self.subTest(question_type=question_type):
                prompt = get_eval_prompt(question_type)
                self.assertIn(marker, prompt)
                self.assertIn("Chinese Native Speakers", prompt)

    def test_legacy_support_to_target_uses_pattern_drill_prompt(self):
        prompt = get_eval_prompt("SUPPORT_TO_TARGET")

        self.assertIn("correct English pattern sentence", prompt)
        self.assertIn("Chinese Native Speakers", prompt)


if __name__ == "__main__":
    unittest.main()
