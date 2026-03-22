import re
import time
from typing import List, Dict, Any
from services.llm.tools import LanguageTools
from services.utils.monitor import PerformanceMonitor

class StudyEvaluator:
    def __init__(self, tools: LanguageTools):
        self.tools = tools

    def _clean(self, text: str) -> str:
        if not text: return ""
        return re.sub(r'[^\w\u4e00-\u9fa5]', '', text).lower()

    def check_exact(self, user_ans: str, standards: List[str]) -> bool:
        cleaned_user = self._clean(user_ans)
        return any(cleaned_user == self._clean(s) for s in standards)

    async def process_judge(self, q_type, user_ans, origin, std_answers, vector_score, pm=None):
        """
        核心判题流水线
        :param pm: 外部传入的性能监视器
        """
        # 🌟 1. 确保 pm 存在 (如果外部没传，则自己初始化)
        if pm is None:
            pm = PerformanceMonitor()
        
        # 🌟 2. Tier 1: 记录正则匹配检查的瞬间耗时
        t1_start = time.perf_counter()
        is_exact = self.check_exact(user_ans, std_answers)
        pm.record("Tier 1 (Regex)", time.perf_counter() - t1_start)

        if is_exact:
            pm.report(vector_score=1.0)
            return {
                "level": 1, "isCorrect": True, 
                "message": "Perfect! Exact match.", "judgedBy": "Regex"
            }

        # 🌟 3. Tier 3: 决策是否需要 LLM
        if vector_score > 0.95:
            # 记录跳过时间
            pm.record("Tier 3 (Skipped)", 0.0)
            final_res = {
                "level": 1, "isCorrect": True, 
                "message": "Excellent semantic match!", "judgedBy": "Vector Engine"
            }
        else:
            # 调用 AI，并将 pm 接力棒传给 tools -> engine
            raw_res = await self.tools.judge_with_ai(q_type, origin, user_ans, std_answers, pm=pm)
            
            try:
                level = int(raw_res.get("level", 2))
                is_correct = bool(raw_res.get("is_correct", level <= 2))
                msg = str(raw_res.get("explanation", "Evaluation complete."))
            except:
                level, is_correct, msg = 2, True, "Translation is acceptable."

            final_res = {
                "level": level, "isCorrect": is_correct, 
                "message": msg, "judgedBy": "LLM Mentor"
            }

        # 🌟 4. 输出最终体检报告
        pm.report(vector_score=vector_score)
        
        return final_res