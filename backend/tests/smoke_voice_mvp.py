import asyncio
import os
import sys
import types
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

try:
    import google.generativeai as _unused_google_genai  # noqa: F401
except Exception:
    google_pkg = types.ModuleType("google")
    google_genai_mod = types.ModuleType("google.generativeai")

    def _embed_content(*args, **kwargs):  # noqa: ARG001, ARG002
        return {"embedding": [0.0]}

    google_genai_mod.configure = lambda *args, **kwargs: None  # noqa: E731
    google_genai_mod.embed_content = _embed_content
    google_pkg.generativeai = google_genai_mod
    sys.modules["google"] = google_pkg
    sys.modules["google.generativeai"] = google_genai_mod

from services.speech.asr_service import ASRService  # noqa: E402
from services.study.evaluator_service import StudyEvaluator  # noqa: E402
from services.utils.monitor import PerformanceMonitor  # noqa: E402


PerformanceMonitor.ENABLED = False


class FakeTools:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    async def judge_with_ai(self, q_type, question, user_ans, standards, pm=None):  # noqa: ARG002
        self.calls += 1
        return self.response


class DummyASRService(ASRService):
    def _transcribe_with_openai(self, audio_bytes, filename, language, prompt):  # noqa: ARG002
        return {
            "transcript": "你好",
            "confidence": 0.91,
            "provider": "openai",
            "model": self.openai_model,
        }


def test_asr_service():
    os.environ["ASR_ACTIVE_PROVIDER"] = "openai"
    os.environ["ASR_MAX_AUDIO_BYTES"] = "1024"

    service = DummyASRService()
    result = service.transcribe(
        audio_bytes=b"1234",
        filename="sample.webm",
        content_type="audio/webm",
        language="zh",
        prompt=None,
    )
    assert result["transcript"] == "你好"
    assert result["confidence"] == 0.91
    assert result["provider"] == "openai"

    try:
        service.transcribe(audio_bytes=b"x" * 2048)
        raise AssertionError("Expected oversize audio to fail")
    except ValueError as exc:
        assert "too large" in str(exc)

    os.environ["ASR_ACTIVE_PROVIDER"] = "mock_provider"
    bad_provider = ASRService()
    try:
        bad_provider.transcribe(audio_bytes=b"123")
        raise AssertionError("Expected unsupported provider to fail")
    except RuntimeError as exc:
        assert "Unsupported ASR provider" in str(exc)


async def test_evaluator_service():
    tools = FakeTools({"level": 4, "is_correct": True, "explanation": "unused"})
    evaluator = StudyEvaluator(tools=tools)
    speech_cfg = {"pass_threshold": 0.88, "review_threshold": 0.78, "min_asr_confidence": 0.60}

    high_res = await evaluator.process_judge(
        q_type="EN_TO_CN_SPEAK",
        user_ans="我喜欢学习中文",
        origin="I like learning Chinese",
        std_answers=["我喜欢学习中文"],
        vector_score=0.93,
        input_mode="speech",
        asr_confidence=0.95,
        speech_eval_config=speech_cfg,
    )
    assert high_res["isCorrect"] is True
    assert high_res["judgedBy"] == "Vector Engine"
    assert tools.calls == 0

    retry_res = evaluator.check_speech_readiness(
        asr_text="我喜欢学习中文",
        asr_confidence=0.45,
        speech_eval_config=speech_cfg,
    )
    assert retry_res is not None
    assert retry_res["shouldRetry"] is True

    llm_tools = FakeTools({"level": 4, "is_correct": True, "explanation": "语义准确"})
    evaluator_llm = StudyEvaluator(tools=llm_tools)
    mid_res = await evaluator_llm.process_judge(
        q_type="EN_TO_CN_SPEAK",
        user_ans="我平时会看书",
        origin="I usually read books.",
        std_answers=["我平时看书"],
        vector_score=0.82,
        input_mode="speech",
        asr_confidence=0.90,
        speech_eval_config=speech_cfg,
    )
    assert llm_tools.calls == 1
    assert mid_res["judgedBy"] == "LLM Mentor"
    assert mid_res["isCorrect"] is True

    strict_tools = FakeTools({"level": 4, "is_correct": True, "explanation": "unused"})
    evaluator_strict = StudyEvaluator(tools=strict_tools)
    strict_res = await evaluator_strict.process_judge(
        q_type="EN_TO_CN_SPEAK",
        user_ans="noise",
        origin="I usually read books.",
        std_answers=["correct answer"],
        vector_score=0.50,
        input_mode="speech",
        asr_confidence=0.90,
        speech_eval_config={**speech_cfg, "allow_paraphrase": False},
    )
    assert strict_res["isCorrect"] is False
    assert strict_res["judgedBy"] == "Vector Engine"
    assert strict_tools.calls == 0


def main():
    test_asr_service()
    asyncio.run(test_evaluator_service())
    print("SMOKE TEST PASS: voice MVP core logic is working.")


if __name__ == "__main__":
    main()
