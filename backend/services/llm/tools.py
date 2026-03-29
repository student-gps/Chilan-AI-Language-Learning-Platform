import time
import os
from typing import List
from .base_engine import LLMEngine
from .prompts import EVALUATE_PROMPT_TEMPLATE_LEARN_CHINESE_BY_ENGLISH

class LanguageTools:
    def __init__(self, engine: LLMEngine):
        self.engine = engine
        self.embed_provider = os.getenv("EMBED_ACTIVE_PROVIDER", "doubao").lower()
        self.gemini_model_id = os.getenv("EMBED_GEMINI_MODEL_ID", "gemini-embedding-001")
        self.doubao_model_id = os.getenv("EMBED_DOUBAO_MODEL_ID")
        self._gemini_client = None
        self._doubao_client = None

    def _get_gemini_client(self):
        if self._gemini_client is None:
            from google import genai
            api_key = os.getenv("EMBED_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
            self._gemini_client = genai.Client(api_key=api_key)
        return self._gemini_client

    def _get_doubao_client(self):
        if self._doubao_client is None:
            from volcenginesdkarkruntime import Ark
            api_key = os.getenv("EMBED_DOUBAO_API_KEY")
            self._doubao_client = Ark(api_key=api_key)
        return self._doubao_client

    async def get_embedding(self, text: str, pm=None) -> List[float]:
        start = time.perf_counter()
        try:
            if self.embed_provider == "gemini":
                client = self._get_gemini_client()
                result = client.models.embed_content(
                    model=self.gemini_model_id,
                    contents=text,
                )
                embedding = result.embeddings[0].values
            elif self.embed_provider == "doubao":
                client = self._get_doubao_client()
                result = client.embeddings.create(
                    model=self.doubao_model_id,
                    input=[text]
                )
                embedding = result.data[0].embedding
            else:
                raise ValueError(f"❌ 不支持的在线判题向量 Provider: {self.embed_provider}")

            if not embedding:
                raise ValueError("❌ Embedding 返回为空")

            # 🌟 记录向量化耗时
            if pm:
                pm.record("Tier 2 (Embedding)", time.perf_counter() - start)
            return embedding
        except Exception as e:
            print(f"❌ Embedding Error: {e}")
            if pm:
                pm.record("Tier 2 (FAILED)", 0)
            raise

    async def judge_with_ai(self, q_type: str, question: str, user_ans: str, standards: list, pm=None):
        template = EVALUATE_PROMPT_TEMPLATE_LEARN_CHINESE_BY_ENGLISH.get(q_type, EVALUATE_PROMPT_TEMPLATE_LEARN_CHINESE_BY_ENGLISH["EN_TO_CN"])
        prompt = template.format(question=question, user_answer=user_ans, standards=standards)
        # 继续向下传递接力棒
        return await self.engine.generate_json(prompt, pm=pm)
