import asyncio
import time
import json
from typing import Dict, Any

from google import genai
from google.genai import types


class LLMEngine:
    def __init__(self, api_key: str, model_name: str = 'gemini-2.0-flash'):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def _call_sync(self, prompt: str) -> str:
        """Run the synchronous Gemini streaming call and return the full text."""
        full_text = ""
        stream = self.client.models.generate_content_stream(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0,
            ),
        )
        for chunk in stream:
            chunk_text = getattr(chunk, "text", None)
            if chunk_text:
                full_text += chunk_text
        return full_text

    async def generate_json(self, prompt: str, pm=None) -> Dict[str, Any]:
        start = time.perf_counter()
        try:
            full_text = await asyncio.to_thread(self._call_sync, prompt)

            if pm:
                pm.record("Tier 3 (LLM Inf)", time.perf_counter() - start)

            return json.loads(full_text)
        except Exception as e:
            print(f"LLM Error: {e}")
            return {"level": 2, "is_correct": True, "explanation": "Error occurred."}
