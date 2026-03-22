import time
import google.generativeai as genai
from typing import List
from .base_engine import LLMEngine
from .prompts import EVALUATE_PROMPT_TEMPLATE_LEARN_CHINESE_BY_ENGLISH

class LanguageTools:
    def __init__(self, engine: LLMEngine):
        self.engine = engine

    async def get_embedding(self, text: str, pm=None) -> List[float]:
        start = time.perf_counter()
        try:
            result = genai.embed_content(model="models/gemini-embedding-001", content=text)
            # 🌟 记录向量化耗时
            if pm:
                pm.record("Tier 2 (Embedding)", time.perf_counter() - start)
            return result['embedding']
        except Exception as e:
            if pm: pm.record("Tier 2 (FAILED)", 0)
            return []

    async def judge_with_ai(self, q_type: str, question: str, user_ans: str, standards: list, pm=None):
        template = EVALUATE_PROMPT_TEMPLATE_LEARN_CHINESE_BY_ENGLISH.get(q_type, EVALUATE_PROMPT_TEMPLATE_LEARN_CHINESE_BY_ENGLISH["EN_TO_CN"])
        prompt = template.format(question=question, user_answer=user_ans, standards=standards)
        # 继续向下传递接力棒
        return await self.engine.generate_json(prompt, pm=pm)