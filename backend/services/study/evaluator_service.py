import re
from typing import Any, Dict, List, Optional

from services.llm.tools import LanguageTools
from services.utils.monitor import PerformanceMonitor


class StudyEvaluator:
    SPEECH_DEFAULT_CONFIG = {
        "pass_threshold": 0.88,
        "review_threshold": 0.78,
        "min_asr_confidence": 0.60,
        "max_attempts": 3,
        "max_duration_sec": 15,
        "allow_paraphrase": True,
    }

    def __init__(self, tools: LanguageTools):
        self.tools = tools

    def _clean(self, text: str) -> str:
        if not text:
            return ""
        return re.sub(r"[^\w\u4e00-\u9fa5]", "", text).lower()

    @staticmethod
    def _to_optional_float(value: Any) -> Optional[float]:
        try:
            if value is None or value == "":
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _clamp(value: float, min_value: float, max_value: float) -> float:
        return max(min_value, min(max_value, value))

    def check_exact(self, user_ans: str, standards: List[str]) -> bool:
        cleaned_user = self._clean(user_ans)
        return any(cleaned_user == self._clean(s) for s in standards)

    def get_speech_eval_config(self, raw_config: Any = None) -> Dict[str, Any]:
        cfg = dict(self.SPEECH_DEFAULT_CONFIG)
        if not isinstance(raw_config, dict):
            return cfg

        pass_threshold = self._to_optional_float(raw_config.get("pass_threshold"))
        review_threshold = self._to_optional_float(raw_config.get("review_threshold"))
        min_asr_confidence = self._to_optional_float(raw_config.get("min_asr_confidence"))

        if pass_threshold is not None:
            cfg["pass_threshold"] = self._clamp(pass_threshold, 0.0, 1.0)
        if review_threshold is not None:
            cfg["review_threshold"] = self._clamp(review_threshold, 0.0, 1.0)
        if min_asr_confidence is not None:
            cfg["min_asr_confidence"] = self._clamp(min_asr_confidence, 0.0, 1.0)

        if cfg["review_threshold"] > cfg["pass_threshold"]:
            cfg["review_threshold"] = cfg["pass_threshold"]

        try:
            max_attempts = int(raw_config.get("max_attempts"))
            if max_attempts > 0:
                cfg["max_attempts"] = max_attempts
        except (TypeError, ValueError):
            pass

        try:
            max_duration_sec = int(raw_config.get("max_duration_sec"))
            if max_duration_sec > 0:
                cfg["max_duration_sec"] = max_duration_sec
        except (TypeError, ValueError):
            pass

        if "allow_paraphrase" in raw_config:
            cfg["allow_paraphrase"] = bool(raw_config.get("allow_paraphrase"))

        return cfg

    def check_speech_readiness(
        self,
        asr_text: str,
        asr_confidence: Optional[float],
        speech_eval_config: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        cfg = self.get_speech_eval_config(speech_eval_config)
        transcript = (asr_text or "").strip()
        if not transcript:
            return {
                "level": 1,
                "isCorrect": False,
                "message": "Speech transcript is empty. Please record again.",
                "judgedBy": "ASR Guard",
                "shouldRetry": True,
            }

        confidence = self._to_optional_float(asr_confidence)
        if confidence is None:
            return None
        if confidence < cfg["min_asr_confidence"]:
            return {
                "level": 1,
                "isCorrect": False,
                "message": (
                    f"ASR confidence is low ({confidence:.2f} < {cfg['min_asr_confidence']:.2f}). "
                    "Please record again."
                ),
                "judgedBy": "ASR Guard",
                "shouldRetry": True,
            }
        return None

    @staticmethod
    def _normalize_ai_result(raw_res: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(raw_res, dict):
            return {
                "level": 2,
                "isCorrect": False,
                "message": "Evaluation complete. Please improve and try again.",
                "judgedBy": "LLM Mentor",
            }

        try:
            level = int(raw_res.get("level", 2))
        except (TypeError, ValueError):
            level = 2
        level = max(1, min(4, level))

        is_correct_raw = raw_res.get("is_correct")
        if isinstance(is_correct_raw, bool):
            is_correct = is_correct_raw
        else:
            is_correct = level >= 3

        message = str(raw_res.get("explanation", "Evaluation complete."))

        if is_correct and level < 3:
            level = 3
        if not is_correct and level > 2:
            level = 2

        return {
            "level": level,
            "isCorrect": is_correct,
            "message": message,
            "judgedBy": "LLM Mentor",
        }

    async def process_judge(
        self,
        q_type: str,
        user_ans: str,
        origin: str,
        std_answers: List[str],
        vector_score: float,
        pm: Optional[PerformanceMonitor] = None,
        input_mode: str = "text",
        asr_confidence: Optional[float] = None,
        speech_eval_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if pm is None:
            pm = PerformanceMonitor()

        is_speech_mode = (input_mode or "").strip().lower() == "speech"
        if is_speech_mode:
            cfg = self.get_speech_eval_config(speech_eval_config)

            # Guardrail: low-confidence ASR should trigger re-record instead of grading.
            retry_res = self.check_speech_readiness(
                asr_text=user_ans,
                asr_confidence=asr_confidence,
                speech_eval_config=cfg,
            )
            if retry_res:
                pm.report(vector_score=vector_score if vector_score is not None else 0.0)
                return retry_res

            if vector_score >= cfg["pass_threshold"]:
                pm.record("Tier 3 (Skipped)", 0.0)
                pm.report(vector_score=vector_score)
                return {
                    "level": 4,
                    "isCorrect": True,
                    "message": "Great job! Semantic match passed.",
                    "judgedBy": "Vector Engine",
                }

            if vector_score < cfg["review_threshold"]:
                pm.record("Tier 3 (Skipped)", 0.0)
                pm.report(vector_score=vector_score)
                return {
                    "level": 1,
                    "isCorrect": False,
                    "message": "Semantic similarity is too low. Please try again.",
                    "judgedBy": "Vector Engine",
                }

            raw_res = await self.tools.judge_with_ai(q_type, origin, user_ans, std_answers, pm=pm)
            final_res = self._normalize_ai_result(raw_res)
            pm.report(vector_score=vector_score)
            return final_res

        if vector_score > 0.95:
            pm.record("Tier 3 (Skipped)", 0.0)
            pm.report(vector_score=vector_score)
            return {
                "level": 4,
                "isCorrect": True,
                "message": "Excellent semantic match!",
                "judgedBy": "Vector Engine",
            }

        raw_res = await self.tools.judge_with_ai(q_type, origin, user_ans, std_answers, pm=pm)
        final_res = self._normalize_ai_result(raw_res)
        pm.report(vector_score=vector_score)
        return final_res
