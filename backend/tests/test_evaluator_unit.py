"""
Unit tests for StudyEvaluator — pure logic, no DB or network.
覆盖三层评估引擎的核心分支，改动阈值/逻辑时这里会先报警。
"""
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.study.evaluator_service import StudyEvaluator


def _make_evaluator(ai_result=None):
    """返回一个 tools.judge_with_ai 被 mock 的 evaluator。"""
    tools = MagicMock()
    tools.judge_with_ai = AsyncMock(return_value=ai_result or {
        "level": 3,
        "is_correct": True,
        "explanation": "Good answer.",
    })
    return StudyEvaluator(tools=tools)


def run(coro):
    return asyncio.run(coro)


# ─────────────────────────────────────────────
# check_exact
# ─────────────────────────────────────────────
class TestCheckExact(unittest.TestCase):
    def setUp(self):
        self.ev = _make_evaluator()

    def test_exact_match(self):
        self.assertTrue(self.ev.check_exact("hello", ["hello"]))

    def test_case_insensitive(self):
        self.assertTrue(self.ev.check_exact("Hello", ["hello"]))

    def test_punctuation_stripped(self):
        # 标点符号应被忽略
        self.assertTrue(self.ev.check_exact("hello!", ["hello"]))
        self.assertTrue(self.ev.check_exact("hello", ["hello!"]))

    def test_multiple_standards_any_match(self):
        self.assertTrue(self.ev.check_exact("hi", ["hello", "hi", "hey"]))

    def test_no_match(self):
        self.assertFalse(self.ev.check_exact("bye", ["hello", "hi"]))

    def test_empty_answer(self):
        self.assertFalse(self.ev.check_exact("", ["hello"]))

    def test_empty_standards(self):
        self.assertFalse(self.ev.check_exact("hello", []))

    def test_chinese_match(self):
        self.assertTrue(self.ev.check_exact("你好", ["你好"]))

    def test_chinese_punctuation_stripped(self):
        self.assertTrue(self.ev.check_exact("你好！", ["你好"]))


# ─────────────────────────────────────────────
# get_speech_eval_config
# ─────────────────────────────────────────────
class TestGetSpeechEvalConfig(unittest.TestCase):
    def setUp(self):
        self.ev = _make_evaluator()

    def test_defaults_when_none(self):
        cfg = self.ev.get_speech_eval_config(None)
        self.assertEqual(cfg["pass_threshold"], 0.88)
        self.assertEqual(cfg["review_threshold"], 0.78)
        self.assertEqual(cfg["min_asr_confidence"], 0.60)
        self.assertTrue(cfg["allow_paraphrase"])

    def test_custom_values_applied(self):
        cfg = self.ev.get_speech_eval_config({"pass_threshold": 0.9, "review_threshold": 0.8})
        self.assertAlmostEqual(cfg["pass_threshold"], 0.9)
        self.assertAlmostEqual(cfg["review_threshold"], 0.8)

    def test_review_threshold_clamped_to_pass_threshold(self):
        # review_threshold 不能超过 pass_threshold
        cfg = self.ev.get_speech_eval_config({"pass_threshold": 0.7, "review_threshold": 0.9})
        self.assertLessEqual(cfg["review_threshold"], cfg["pass_threshold"])

    def test_thresholds_clamped_to_01(self):
        cfg = self.ev.get_speech_eval_config({"pass_threshold": 1.5, "min_asr_confidence": -0.1})
        self.assertEqual(cfg["pass_threshold"], 1.0)
        self.assertEqual(cfg["min_asr_confidence"], 0.0)

    def test_allow_paraphrase_false(self):
        cfg = self.ev.get_speech_eval_config({"allow_paraphrase": False})
        self.assertFalse(cfg["allow_paraphrase"])

    def test_allow_paraphrase_string_false(self):
        cfg = self.ev.get_speech_eval_config({"allow_paraphrase": "false"})
        self.assertFalse(cfg["allow_paraphrase"])

    def test_non_dict_returns_defaults(self):
        cfg = self.ev.get_speech_eval_config("invalid")
        self.assertEqual(cfg["pass_threshold"], 0.88)


# ─────────────────────────────────────────────
# _normalize_ai_result
# ─────────────────────────────────────────────
class TestNormalizeAiResult(unittest.TestCase):
    def test_correct_answer_level3(self):
        res = StudyEvaluator._normalize_ai_result({"level": 3, "is_correct": True, "explanation": "Good"})
        self.assertTrue(res["isCorrect"])
        self.assertEqual(res["level"], 3)

    def test_correct_answer_level4(self):
        res = StudyEvaluator._normalize_ai_result({"level": 4, "is_correct": True, "explanation": "Excellent"})
        self.assertTrue(res["isCorrect"])
        self.assertEqual(res["level"], 4)

    def test_incorrect_answer_level1(self):
        res = StudyEvaluator._normalize_ai_result({"level": 1, "is_correct": False, "explanation": "Wrong"})
        self.assertFalse(res["isCorrect"])
        self.assertEqual(res["level"], 1)

    def test_is_correct_true_but_level_low_gets_bumped(self):
        # is_correct=True 但 level=2 → level 应提升到 3
        res = StudyEvaluator._normalize_ai_result({"level": 2, "is_correct": True, "explanation": "ok"})
        self.assertTrue(res["isCorrect"])
        self.assertGreaterEqual(res["level"], 3)

    def test_is_correct_false_but_level_high_gets_dropped(self):
        # is_correct=False 但 level=4 → level 应降到 ≤2
        res = StudyEvaluator._normalize_ai_result({"level": 4, "is_correct": False, "explanation": "wrong"})
        self.assertFalse(res["isCorrect"])
        self.assertLessEqual(res["level"], 2)

    def test_level_inferred_from_is_correct_when_missing(self):
        # 没有 is_correct 字段，从 level 推断
        res = StudyEvaluator._normalize_ai_result({"level": 3, "explanation": "ok"})
        self.assertTrue(res["isCorrect"])

    def test_non_dict_input_returns_safe_default(self):
        res = StudyEvaluator._normalize_ai_result("not a dict")
        self.assertFalse(res["isCorrect"])
        self.assertEqual(res["judgedBy"], "LLM Mentor")

    def test_level_clamped_to_1_4(self):
        res = StudyEvaluator._normalize_ai_result({"level": 99, "is_correct": True, "explanation": ""})
        self.assertLessEqual(res["level"], 4)
        res2 = StudyEvaluator._normalize_ai_result({"level": -5, "is_correct": False, "explanation": ""})
        self.assertGreaterEqual(res2["level"], 1)


# ─────────────────────────────────────────────
# process_judge — text mode
# ─────────────────────────────────────────────
class TestProcessJudgeTextMode(unittest.TestCase):
    def test_high_vector_score_skips_llm(self):
        ev = _make_evaluator()
        result = run(ev.process_judge(
            q_type="CN_TO_EN", user_ans="hello", origin="你好",
            std_answers=["hello"], vector_score=0.96, input_mode="text",
        ))
        self.assertTrue(result["isCorrect"])
        self.assertEqual(result["judgedBy"], "Vector Engine")
        ev.tools.judge_with_ai.assert_not_called()

    def test_vector_score_exactly_095_calls_llm(self):
        # 0.95 不超过阈值，应走 LLM
        ev = _make_evaluator({"level": 3, "is_correct": True, "explanation": "Good"})
        result = run(ev.process_judge(
            q_type="CN_TO_EN", user_ans="hello", origin="你好",
            std_answers=["hello"], vector_score=0.95, input_mode="text",
        ))
        ev.tools.judge_with_ai.assert_called_once()
        self.assertEqual(result["judgedBy"], "LLM Mentor")

    def test_low_vector_score_calls_llm(self):
        ev = _make_evaluator({"level": 2, "is_correct": False, "explanation": "Needs work"})
        result = run(ev.process_judge(
            q_type="CN_TO_EN", user_ans="bye", origin="你好",
            std_answers=["hello"], vector_score=0.5, input_mode="text",
        ))
        ev.tools.judge_with_ai.assert_called_once()
        self.assertFalse(result["isCorrect"])

    def test_llm_error_state_is_incorrect(self):
        # LLM 报错时（level=1, is_correct=False）不应标记为正确
        ev = _make_evaluator({"level": 1, "is_correct": False, "explanation": "Error occurred."})
        result = run(ev.process_judge(
            q_type="CN_TO_EN", user_ans="whatever", origin="你好",
            std_answers=["hello"], vector_score=0.5, input_mode="text",
        ))
        self.assertFalse(result["isCorrect"])


# ─────────────────────────────────────────────
# process_judge — speech mode
# ─────────────────────────────────────────────
class TestProcessJudgeSpeechMode(unittest.TestCase):
    def test_empty_transcript_triggers_retry(self):
        ev = _make_evaluator()
        result = run(ev.process_judge(
            q_type="CN_TO_EN", user_ans="", origin="你好",
            std_answers=["hello"], vector_score=0.5, input_mode="speech",
        ))
        self.assertTrue(result.get("shouldRetry"))
        self.assertFalse(result["isCorrect"])
        ev.tools.judge_with_ai.assert_not_called()

    def test_low_asr_confidence_triggers_retry(self):
        ev = _make_evaluator()
        result = run(ev.process_judge(
            q_type="CN_TO_EN", user_ans="hello", origin="你好",
            std_answers=["hello"], vector_score=0.85,
            input_mode="speech", asr_confidence=0.3,
        ))
        self.assertTrue(result.get("shouldRetry"))
        ev.tools.judge_with_ai.assert_not_called()

    def test_high_vector_score_passes_without_llm(self):
        ev = _make_evaluator()
        result = run(ev.process_judge(
            q_type="CN_TO_EN", user_ans="hello", origin="你好",
            std_answers=["hello"], vector_score=0.92,
            input_mode="speech", asr_confidence=0.9,
        ))
        self.assertTrue(result["isCorrect"])
        self.assertEqual(result["judgedBy"], "Vector Engine")
        ev.tools.judge_with_ai.assert_not_called()

    def test_low_vector_no_paraphrase_fails_immediately(self):
        ev = _make_evaluator()
        result = run(ev.process_judge(
            q_type="CN_TO_EN", user_ans="hi there", origin="你好",
            std_answers=["hello"], vector_score=0.5,
            input_mode="speech", asr_confidence=0.9,
            speech_eval_config={"allow_paraphrase": False, "review_threshold": 0.78},
        ))
        self.assertFalse(result["isCorrect"])
        self.assertEqual(result["judgedBy"], "Vector Engine")
        ev.tools.judge_with_ai.assert_not_called()

    def test_medium_vector_with_paraphrase_calls_llm(self):
        ev = _make_evaluator({"level": 3, "is_correct": True, "explanation": "Close enough"})
        result = run(ev.process_judge(
            q_type="CN_TO_EN", user_ans="hi there", origin="你好",
            std_answers=["hello"], vector_score=0.82,
            input_mode="speech", asr_confidence=0.9,
            speech_eval_config={"allow_paraphrase": True},
        ))
        ev.tools.judge_with_ai.assert_called_once()
        self.assertTrue(result["isCorrect"])


if __name__ == "__main__":
    unittest.main()
