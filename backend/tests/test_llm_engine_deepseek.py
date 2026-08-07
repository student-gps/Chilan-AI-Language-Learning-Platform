import asyncio
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from services.llm.base_engine import LLMEngine


def run(coro):
    return asyncio.run(coro)


def content_chunk(text: str):
    return SimpleNamespace(
        choices=[SimpleNamespace(delta=SimpleNamespace(content=text))],
        usage=None,
    )


def usage_chunk(*, prompt=0, completion=0, total=0, hit=0, miss=0):
    return SimpleNamespace(
        choices=[],
        usage=SimpleNamespace(
            prompt_tokens=prompt,
            completion_tokens=completion,
            total_tokens=total,
            prompt_cache_hit_tokens=hit,
            prompt_cache_miss_tokens=miss,
        ),
    )


class DeepSeekJudgeEngineTests(unittest.TestCase):
    @patch("openai.OpenAI")
    def test_deepseek_stream_uses_json_non_thinking_and_cache_usage(self, mock_openai):
        client = MagicMock()
        client.chat.completions.create.return_value = iter([
            content_chunk('{"level": 2,'),
            content_chunk('"is_correct": false, "explanation": "Use English."}'),
            usage_chunk(prompt=420, completion=18, total=438, hit=360, miss=60),
        ])
        mock_openai.return_value = client
        engine = LLMEngine(
            provider="deepseek",
            api_key="deepseek-key",
            model_name="deepseek-v4-flash",
            timeout_seconds=30,
            max_retries=0,
            max_tokens=512,
            user_id="chilan-tier3",
        )

        with patch("services.llm.base_engine.emit_judge_usage") as emit_usage:
            result = run(engine.generate_json("Return valid JSON only."))

        self.assertEqual(result["level"], 2)
        self.assertFalse(result["is_correct"])
        mock_openai.assert_called_once_with(
            api_key="deepseek-key",
            base_url="https://api.deepseek.com",
            timeout=30.0,
            max_retries=0,
        )
        kwargs = client.chat.completions.create.call_args.kwargs
        self.assertEqual(kwargs["model"], "deepseek-v4-flash")
        self.assertEqual(kwargs["messages"], [{"role": "user", "content": "Return valid JSON only."}])
        self.assertEqual(kwargs["temperature"], 0.0)
        self.assertEqual(kwargs["max_tokens"], 512)
        self.assertEqual(kwargs["response_format"], {"type": "json_object"})
        self.assertTrue(kwargs["stream"])
        self.assertEqual(kwargs["stream_options"], {"include_usage": True})
        self.assertEqual(
            kwargs["extra_body"],
            {"thinking": {"type": "disabled"}, "user_id": "chilan-tier3"},
        )

        telemetry = emit_usage.call_args.kwargs
        self.assertEqual(telemetry["provider"], "deepseek")
        self.assertEqual(telemetry["model"], "deepseek-v4-flash")
        self.assertEqual(telemetry["prompt_cache_hit_tokens"], 360)
        self.assertEqual(telemetry["prompt_cache_miss_tokens"], 60)
        self.assertEqual(telemetry["prompt_tokens"], 420)
        self.assertEqual(telemetry["completion_tokens"], 18)
        self.assertGreaterEqual(telemetry["ttft_ms"], 0)
        self.assertNotIn("prompt", telemetry)

    @patch.dict(
        os.environ,
        {
            "LLM_JUDGE_PROVIDER": "deepseek",
            "LLM_JUDGE_DEEPSEEK_API_KEY": "deepseek-key",
            "LLM_JUDGE_DEEPSEEK_MODEL_ID": "deepseek-v4-flash",
            "LLM_JUDGE_DEEPSEEK_BASE_URL": "https://api.deepseek.com",
            "LLM_JUDGE_DEEPSEEK_TIMEOUT_SECONDS": "27",
            "LLM_JUDGE_DEEPSEEK_MAX_RETRIES": "2",
            "LLM_JUDGE_DEEPSEEK_MAX_TOKENS": "400",
            "LLM_JUDGE_DEEPSEEK_USER_ID": "chilan-tier3",
            "LLM_JUDGE_FALLBACK_PROVIDER": "",
        },
        clear=False,
    )
    @patch("openai.OpenAI")
    def test_from_env_selects_deepseek(self, mock_openai):
        engine = LLMEngine.from_env()

        self.assertEqual(engine.provider, "deepseek")
        self.assertEqual(engine.model_name, "deepseek-v4-flash")
        self.assertEqual(engine.timeout_seconds, 27)
        self.assertEqual(engine.max_retries, 2)
        self.assertEqual(engine.max_tokens, 400)
        self.assertEqual(engine.user_id, "chilan-tier3")
        self.assertIsNone(engine.fallback_engine)
        mock_openai.assert_called_once()

    @patch("openai.OpenAI")
    def test_retryable_deepseek_failure_uses_gemini_fallback_once(self, mock_openai):
        client = MagicMock()
        client.chat.completions.create.side_effect = Exception("503 Service Unavailable")
        mock_openai.return_value = client
        fallback = MagicMock(spec=LLMEngine)
        fallback.provider = "gemini"
        fallback.model_name = "gemini-2.5-flash"
        fallback._call_sync.return_value = {
            "text": '{"level": 1, "is_correct": false, "explanation": "Try again."}',
            "ttft_ms": 12.0,
            "total_latency_ms": 20.0,
            "prompt_tokens": 50,
            "completion_tokens": 10,
            "total_tokens": 60,
            "prompt_cache_hit_tokens": 0,
            "prompt_cache_miss_tokens": None,
        }
        fallback._emit_success = MagicMock()
        engine = LLMEngine(
            provider="deepseek",
            api_key="deepseek-key",
            max_retries=0,
            fallback_engine=fallback,
        )

        result = run(engine.generate_json("Return valid JSON only."))

        self.assertEqual(result["level"], 1)
        fallback._call_sync.assert_called_once_with("Return valid JSON only.")
        fallback._emit_success.assert_called_once()
        self.assertTrue(fallback._emit_success.call_args.kwargs["fallback_used"])
        self.assertEqual(fallback._emit_success.call_args.kwargs["fallback_provider"], "deepseek")

    @patch("openai.OpenAI")
    def test_non_retryable_deepseek_failure_does_not_use_fallback(self, mock_openai):
        client = MagicMock()
        client.chat.completions.create.side_effect = Exception("401 invalid_api_key")
        mock_openai.return_value = client
        fallback = MagicMock(spec=LLMEngine)
        fallback.provider = "gemini"
        engine = LLMEngine(
            provider="deepseek",
            api_key="deepseek-key",
            max_retries=0,
            fallback_engine=fallback,
        )

        result = run(engine.generate_json("Return valid JSON only."))

        self.assertEqual(result["level"], 1)
        self.assertFalse(result["is_correct"])
        fallback._call_sync.assert_not_called()
    @patch("openai.OpenAI")
    def test_status_coded_non_retryable_deepseek_failure_does_not_use_fallback(self, mock_openai):
        client = MagicMock()
        api_error = Exception("gateway timeout")
        api_error.status_code = 401
        client.chat.completions.create.side_effect = api_error
        mock_openai.return_value = client
        fallback = MagicMock(spec=LLMEngine)
        fallback.provider = "gemini"
        engine = LLMEngine(
            provider="deepseek",
            api_key="deepseek-key",
            max_retries=0,
            fallback_engine=fallback,
        )

        result = run(engine.generate_json("Return valid JSON only."))

        self.assertEqual(result["level"], 1)
        fallback._call_sync.assert_not_called()


if __name__ == "__main__":
    unittest.main()
