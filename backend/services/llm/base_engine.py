import os
import time
import json
from typing import Dict, Any

from google import genai
from google.genai import types


class LLMEngine:
    def __init__(self, api_key: str, model_name: str = 'gemini-2.0-flash'):
        from config.env import get_env
        use_vertex = get_env("LLM_GEMINI_USE_VERTEX", default="false").lower() == "true"
        if use_vertex:
            project  = get_env("VERTEX_AI_PROJECT_ID")
            location = get_env("VERTEX_AI_LOCATION", default="us-central1")
            sa_key   = get_env("GOOGLE_APPLICATION_CREDENTIALS")
            if sa_key:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = sa_key
            self.client = genai.Client(vertexai=True, project=project, location=location)
        else:
            self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    async def generate_json(self, prompt: str, pm=None) -> Dict[str, Any]:
        start = time.perf_counter()
        full_text = ""
        try:
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

            if pm:
                pm.record("Tier 3 (LLM Inf)", time.perf_counter() - start)

            return json.loads(full_text)
        except Exception as e:
            print(f"LLM Error: {e}")
            return {"level": 2, "is_correct": True, "explanation": "Error occurred."}
