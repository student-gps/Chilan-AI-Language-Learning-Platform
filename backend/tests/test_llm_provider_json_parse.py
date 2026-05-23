import json
import sys
from pathlib import Path
import unittest


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from content_builder.core.llm_providers import BaseLLMProvider


class DummyProvider(BaseLLMProvider):
    def generate_structured_json(self, prompt: str, file_path: str = None, file_obj=None) -> dict:
        return {}


class LLMProviderJsonParseTest(unittest.TestCase):
    def test_preserves_japanese_kana_payload_without_target_language_marker(self):
        provider = DummyProvider()
        payload = {
            "course_content": {
                "dialogue": {
                    "lines": [
                        {"text": "これからお世話になります。よろしくお願いします。"}
                    ]
                }
            }
        }

        parsed = provider._safe_parse_json(json.dumps(payload, ensure_ascii=False))
        text = parsed["course_content"]["dialogue"]["lines"][0]["text"]

        self.assertIn("お世話", text)
        self.assertIn("お願いします", text)
        self.assertNotIn("お世话", text)
        self.assertNotIn("お愿い", text)


if __name__ == "__main__":
    unittest.main()
