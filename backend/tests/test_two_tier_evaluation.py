import ast
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from services.llm.base_engine import LLMEngine
from services.study.evaluator_service import StudyEvaluator
from services.utils.monitor import PerformanceMonitor

PerformanceMonitor.ENABLED = False


class TwoTierEvaluationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tools = SimpleNamespace(judge_with_ai=AsyncMock(return_value={
            "level": 3, "is_correct": True, "explanation": "Meaning preserved.",
        }))
        self.evaluator = StudyEvaluator(self.tools)

    async def test_text_and_speech_paraphrases_reach_llm_with_metadata(self):
        for mode in ("text", "speech"):
            with self.subTest(mode=mode):
                self.tools.judge_with_ai.reset_mock()
                result = await self.evaluator.process_judge(
                    "EN_TO_CN", "我喜欢学习汉语", "I like learning Chinese.", ["我喜欢学中文"],
                    input_mode=mode, asr_confidence=0.95,
                    item_metadata={"support_language": "en"},
                )
                self.assertTrue(result["isCorrect"])
                self.assertEqual(result["judgedBy"], "LLM Mentor")
                self.tools.judge_with_ai.assert_awaited_once()
                self.assertEqual(self.tools.judge_with_ai.call_args.kwargs["metadata"], {"support_language": "en"})

    async def test_legacy_similarity_thresholds_do_not_reject_speech(self):
        result = await self.evaluator.process_judge(
            "EN_TO_CN_SPEAK", "我喜欢学习汉语", "I like learning Chinese.", ["我喜欢学中文"],
            input_mode="speech", asr_confidence=0.95,
            speech_eval_config={"pass_threshold": 1.0, "review_threshold": 1.0, "allow_paraphrase": False},
        )
        self.assertTrue(result["isCorrect"])
        self.tools.judge_with_ai.assert_awaited_once()

    async def test_unreliable_or_empty_speech_requests_retry_without_llm(self):
        for text, confidence in (("你好", 0.2), ("", 0.95)):
            with self.subTest(text=text):
                result = await self.evaluator.process_judge(
                    "EN_TO_CN_SPEAK", text, "Hello", ["你好"],
                    input_mode="speech", asr_confidence=confidence,
                )
                self.assertTrue(result["shouldRetry"])
                self.assertEqual(result["judgedBy"], "ASR Guard")
        self.tools.judge_with_ai.assert_not_awaited()

    async def test_judge_failure_propagates_to_route_retry_handler(self):
        self.tools.judge_with_ai.side_effect = RuntimeError("unavailable")
        with self.assertRaises(RuntimeError):
            await self.evaluator.process_judge("EN_TO_CN", "你好呀", "Hello", ["你好"])

    async def test_engine_failure_is_not_a_review_grade(self):
        engine = LLMEngine.__new__(LLMEngine)
        engine.provider = "gemini"
        engine.model_name = "test"
        engine.fallback_engine = None
        with patch.object(engine, "_call_sync", side_effect=RuntimeError("unavailable")), patch("services.llm.base_engine.emit_judge_usage"):
            with self.assertRaises(RuntimeError):
                await engine.generate_json("test")

    def test_normalized_exact_matching_is_preserved(self):
        self.assertTrue(self.evaluator.check_exact("Bonjour !", ["bonjour"]))
        self.assertFalse(self.evaluator.check_exact("au revoir", ["bonjour"]))

    def test_changed_backend_sources_parse(self):
        root = Path(__file__).resolve().parents[1]
        for relative in (
            "routers/study.py", "services/study/evaluator_service.py", "services/llm/tools.py",
            "services/llm/__init__.py", "services/llm/base_engine.py", "database/sync_to_db.py",
            "database/init_cloud_schema.py",
        ):
            with self.subTest(path=relative):
                ast.parse((root / relative).read_text(encoding="utf-8-sig"), filename=relative)


if __name__ == "__main__":
    unittest.main()
