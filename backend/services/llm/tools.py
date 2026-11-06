from services.study.practice_item_schema import canonicalize_practice_item
from .base_engine import LLMEngine
from .prompts import get_eval_prompt


class LanguageTools:
    def __init__(self, engine: LLMEngine):
        self.engine = engine

    async def judge_with_ai(self, q_type: str, question: str, user_ans: str, standards: list, pm=None, metadata=None):
        canonical_type, normalized_metadata = canonicalize_practice_item(q_type, metadata)
        template = get_eval_prompt(canonical_type, metadata=normalized_metadata)
        prompt = template.format(question=question, user_answer=user_ans, standards=standards)
        return await self.engine.generate_json(prompt, pm=pm)
