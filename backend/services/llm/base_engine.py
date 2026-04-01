import json
import time
from typing import Any, Dict

from google import genai


class LLMEngine:
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    @staticmethod
    def _parse_json_text(raw_text: str) -> Dict[str, Any]:
        text = (raw_text or "").strip()
        if text.startswith("```"):
            lines = [line for line in text.splitlines() if not line.strip().startswith("```")]
            text = "\n".join(lines).strip()
        return json.loads(text)

    async def generate_json(self, prompt: str, pm=None) -> Dict[str, Any]:
        start = time.perf_counter()
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={"response_mime_type": "application/json"},
            )
            raw_text = response.text or ""

            if pm:
                pm.record("Tier 3 (LLM Inf)", time.perf_counter() - start)

            return self._parse_json_text(raw_text)
        except Exception as e:
            print(f"LLM Error: {e}")
            return {
                "level": 2,
                "is_correct": False,
                "explanation": "Evaluation is temporarily unavailable. Please retry.",
            }
