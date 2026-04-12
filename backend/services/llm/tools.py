import time
from typing import List

from google import genai

from .base_engine import LLMEngine
from .prompts import EVALUATE_PROMPT_TEMPLATE_LEARN_CHINESE_BY_ENGLISH
from config.env import get_env


class LanguageTools:
    def __init__(self, engine: LLMEngine):
        self.engine = engine
        self.embed_provider = get_env("LLM_EMBED_PROVIDER", default="doubao").lower()
        self.gemini_model_id = get_env("LLM_EMBED_GEMINI_MODEL_ID", default="gemini-embedding-001")
        self.doubao_model_id = get_env("LLM_EMBED_DOUBAO_MODEL_ID")
        self._doubao_client = None
        self._gemini_client = None

    @staticmethod
    def _normalize_gemini_model_id(model_id: str) -> str:
        normalized = (model_id or "").strip()
        if normalized.startswith("models/"):
            return normalized.split("/", 1)[1]
        return normalized or "gemini-embedding-001"

    def _get_gemini_client(self):
        if self._gemini_client is None:
            api_key = get_env("LLM_EMBED_GEMINI_API_KEY", "LLM_GEMINI_API_KEY")
            self._gemini_client = genai.Client(api_key=api_key)
        return self._gemini_client

    def _get_doubao_client(self):
        if self._doubao_client is None:
            from volcenginesdkarkruntime import Ark

            api_key = get_env("LLM_EMBED_DOUBAO_API_KEY")
            self._doubao_client = Ark(api_key=api_key)
        return self._doubao_client

    async def get_embedding(self, text: str, pm=None) -> List[float]:
        start = time.perf_counter()
        try:
            if self.embed_provider == "gemini":
                client = self._get_gemini_client()
                result = client.models.embed_content(
                    model=self._normalize_gemini_model_id(self.gemini_model_id),
                    contents=text,
                )
                embedding = result.embeddings[0].values
            elif self.embed_provider == "doubao":
                client = self._get_doubao_client()
                result = client.embeddings.create(model=self.doubao_model_id, input=[text])
                embedding = result.data[0].embedding
            else:
                raise ValueError(f"Unsupported online judge embedding provider: {self.embed_provider}")

            if not embedding:
                raise ValueError("Embedding returned empty payload")

            if pm:
                pm.record("Tier 2 (Embedding)", time.perf_counter() - start)
            return embedding
        except Exception as e:
            print(f"Embedding Error: {e}")
            if pm:
                pm.record("Tier 2 (FAILED)", 0)
            raise

    async def judge_with_ai(self, q_type: str, question: str, user_ans: str, standards: list, pm=None):
        template = EVALUATE_PROMPT_TEMPLATE_LEARN_CHINESE_BY_ENGLISH.get(
            q_type,
            EVALUATE_PROMPT_TEMPLATE_LEARN_CHINESE_BY_ENGLISH["EN_TO_CN"],
        )
        prompt = template.format(question=question, user_answer=user_ans, standards=standards)
        return await self.engine.generate_json(prompt, pm=pm)
