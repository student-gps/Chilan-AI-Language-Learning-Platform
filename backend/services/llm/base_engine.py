import asyncio
import os
import time
import json
from typing import Dict, Any

from google import genai
from google.genai import types

from config.env import get_env


class LLMEngine:
    def __init__(self, api_key: str = None, model_name: str = None, use_vertex: bool = False):
        self.model_name = model_name or get_env("LLM_JUDGE_GEMINI_MODEL_ID", default="gemini-2.5-flash")
        self.use_vertex = use_vertex

        if use_vertex:
            project = get_env("LLM_JUDGE_VERTEX_AI_PROJECT_ID", "VERTEX_AI_PROJECT_ID")
            location = get_env("LLM_JUDGE_VERTEX_AI_LOCATION", "VERTEX_AI_LOCATION", default="us-central1")
            credentials = get_env("LLM_JUDGE_GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_APPLICATION_CREDENTIALS")
            if credentials:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials
            if not project:
                raise ValueError("LLM judge Vertex mode requires VERTEX_AI_PROJECT_ID.")
            self.client = genai.Client(vertexai=True, project=project, location=location)
            return

        resolved_api_key = api_key or get_env("LLM_JUDGE_GEMINI_API_KEY", "LLM_GEMINI_API_KEY")
        if not resolved_api_key:
            raise ValueError("LLM judge Gemini API key is missing. Set LLM_JUDGE_GEMINI_API_KEY or LLM_GEMINI_API_KEY.")
        self.client = genai.Client(api_key=resolved_api_key)

    @classmethod
    def from_env(cls) -> "LLMEngine":
        provider = get_env("LLM_JUDGE_PROVIDER", default="gemini").lower()
        if provider != "gemini":
            raise ValueError(f"Unsupported LLM judge provider: {provider}")

        use_vertex = get_env("LLM_JUDGE_GEMINI_USE_VERTEX", default="false").lower() in {"1", "true", "yes", "on"}
        return cls(use_vertex=use_vertex)

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
            return {"level": 1, "is_correct": False, "explanation": "Error occurred."}
