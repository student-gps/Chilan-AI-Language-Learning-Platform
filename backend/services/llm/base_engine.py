import asyncio
import json
import os
import time
from typing import Any, Dict

from config.env import get_env, get_env_bool, get_env_int
from services.llm.judge_metrics import emit_judge_usage


class LLMEngine:
    def __init__(
        self,
        provider: str = "gemini",
        api_key: str | None = None,
        model_name: str | None = None,
        use_vertex: bool = False,
        base_url: str | None = None,
        timeout_seconds: int | None = None,
        max_retries: int | None = None,
        max_tokens: int | None = None,
        user_id: str | None = None,
        fallback_engine: "LLMEngine | None" = None,
    ):
        self.provider = (provider or "gemini").strip().lower()
        self.model_name = model_name
        self.use_vertex = use_vertex
        self.base_url = (base_url or "").strip()
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.max_tokens = max_tokens
        self.user_id = (user_id or "").strip()
        self.fallback_engine = fallback_engine
        self.client = None

        if self.provider == "gemini":
            self._configure_gemini(api_key=api_key)
        elif self.provider == "deepseek":
            self._configure_deepseek(api_key=api_key)
        else:
            raise ValueError(f"Unsupported LLM judge provider: {self.provider}")

    def _configure_gemini(self, api_key: str | None) -> None:
        from google import genai

        self.model_name = self.model_name or get_env("LLM_JUDGE_GEMINI_MODEL_ID", default="gemini-2.5-flash")
        if self.use_vertex:
            project = get_env("LLM_JUDGE_VERTEX_AI_PROJECT_ID", "VERTEX_AI_PROJECT_ID")
            location = get_env("LLM_JUDGE_VERTEX_AI_LOCATION", "VERTEX_AI_LOCATION", default="us-central1")
            credentials = get_env("LLM_JUDGE_GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_APPLICATION_CREDENTIALS")
            if credentials:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials
            if not project:
                raise ValueError("LLM judge Vertex mode requires VERTEX_AI_PROJECT_ID.")
            self.client = genai.Client(vertexai=True, project=project, location=location)
            return

        resolved_api_key = api_key or get_env("LLM_JUDGE_GEMINI_API_KEY", "LLM_GEMINI_API_KEY")
        if not resolved_api_key:
            raise ValueError("LLM judge Gemini API key is missing. Set LLM_JUDGE_GEMINI_API_KEY or LLM_GEMINI_API_KEY.")
        self.client = genai.Client(api_key=resolved_api_key)

    def _configure_deepseek(self, api_key: str | None) -> None:
        from openai import OpenAI

        self.model_name = self.model_name or get_env("LLM_JUDGE_DEEPSEEK_MODEL_ID", default="deepseek-v4-flash")
        self.base_url = self.base_url or get_env("LLM_JUDGE_DEEPSEEK_BASE_URL", default="https://api.deepseek.com")
        self.timeout_seconds = self.timeout_seconds or get_env_int("LLM_JUDGE_DEEPSEEK_TIMEOUT_SECONDS", default=30)
        self.max_retries = self.max_retries if self.max_retries is not None else get_env_int("LLM_JUDGE_DEEPSEEK_MAX_RETRIES", default=1)
        self.max_tokens = self.max_tokens or get_env_int("LLM_JUDGE_DEEPSEEK_MAX_TOKENS", default=512)
        self.user_id = self.user_id or get_env("LLM_JUDGE_DEEPSEEK_USER_ID", default="chilan-tier3")
        resolved_api_key = api_key or get_env("LLM_JUDGE_DEEPSEEK_API_KEY")
        if not resolved_api_key:
            raise ValueError("LLM judge DeepSeek API key is missing. Set LLM_JUDGE_DEEPSEEK_API_KEY.")
        self.client = OpenAI(
            api_key=resolved_api_key,
            base_url=self.base_url,
            timeout=float(self.timeout_seconds),
            max_retries=0,
        )

    @classmethod
    def from_env(cls) -> "LLMEngine":
        provider = get_env("LLM_JUDGE_PROVIDER", default="gemini").lower()
        if provider == "gemini":
            use_vertex = get_env_bool("LLM_JUDGE_GEMINI_USE_VERTEX", default=False)
            return cls(provider="gemini", use_vertex=use_vertex)
        if provider == "deepseek":
            engine = cls(provider="deepseek")
            fallback_provider = get_env("LLM_JUDGE_FALLBACK_PROVIDER", default="").lower()
            if fallback_provider:
                engine.fallback_engine = cls._fallback_from_env(fallback_provider)
            return engine
        raise ValueError(f"Unsupported LLM judge provider: {provider}")

    @classmethod
    def _fallback_from_env(cls, provider: str) -> "LLMEngine":
        if provider != "gemini":
            raise ValueError(f"Unsupported LLM judge fallback provider: {provider}")
        use_vertex = get_env_bool("LLM_JUDGE_GEMINI_USE_VERTEX", default=False)
        return cls(provider="gemini", use_vertex=use_vertex)

    @staticmethod
    def _is_retryable_deepseek_error(exc: Exception) -> bool:
        status_code = getattr(exc, "status_code", None)
        if status_code in {429, 500, 502, 503, 504}:
            return True
        if status_code is not None:
            return False

        message = str(exc).lower()
        retryable_markers = (
            "429",
            "rate limit",
            "500",
            "502",
            "503",
            "504",
            "unavailable",
            "bad gateway",
            "gateway timeout",
            "connection",
            "timeout",
            "timed out",
            "readtimeout",
            "connecttimeout",
            "api connection",
        )
        return any(marker in message for marker in retryable_markers)

    @staticmethod
    def _usage_value(usage: Any, name: str, default: int = 0) -> int:
        if usage is None:
            return default
        value = getattr(usage, name, default)
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return default

    def _call_gemini_sync(self, prompt: str) -> Dict[str, Any]:
        """Run the synchronous Gemini stream and return text plus opaque telemetry."""
        from google.genai import types

        started_at = time.perf_counter()
        first_content_at = None
        full_text = ""
        usage = None
        stream = self.client.models.generate_content_stream(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0,
            ),
        )
        for chunk in stream:
            usage = getattr(chunk, "usage_metadata", None) or usage
            chunk_text = getattr(chunk, "text", None)
            if chunk_text:
                if first_content_at is None:
                    first_content_at = time.perf_counter()
                full_text += chunk_text

        return {
            "text": full_text,
            "ttft_ms": (first_content_at - started_at) * 1000 if first_content_at else None,
            "total_latency_ms": (time.perf_counter() - started_at) * 1000,
            "prompt_tokens": self._usage_value(usage, "prompt_token_count"),
            "completion_tokens": self._usage_value(usage, "candidates_token_count"),
            "total_tokens": self._usage_value(usage, "total_token_count"),
            "prompt_cache_hit_tokens": self._usage_value(usage, "cached_content_token_count"),
            "prompt_cache_miss_tokens": None,
        }

    def _call_deepseek_sync(self, prompt: str) -> Dict[str, Any]:
        """Run a non-thinking DeepSeek JSON stream and capture its terminal usage chunk."""
        started_at = time.perf_counter()
        first_content_at = None
        full_text = ""
        usage = None
        waits = [0.25, 0.75, 1.5]

        for attempt in range(self.max_retries + 1):
            try:
                stream = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=self.max_tokens,
                    response_format={"type": "json_object"},
                    stream=True,
                    stream_options={"include_usage": True},
                    extra_body={
                        "thinking": {"type": "disabled"},
                        "user_id": self.user_id,
                    },
                )
                for chunk in stream:
                    usage = getattr(chunk, "usage", None) or usage
                    choices = getattr(chunk, "choices", None) or []
                    if not choices:
                        continue
                    delta = getattr(choices[0], "delta", None)
                    chunk_text = getattr(delta, "content", None) if delta else None
                    if chunk_text:
                        if first_content_at is None:
                            first_content_at = time.perf_counter()
                        full_text += chunk_text
                break
            except Exception as exc:
                if not self._is_retryable_deepseek_error(exc) or attempt >= self.max_retries:
                    raise
                time.sleep(waits[min(attempt, len(waits) - 1)])

        return {
            "text": full_text,
            "ttft_ms": (first_content_at - started_at) * 1000 if first_content_at else None,
            "total_latency_ms": (time.perf_counter() - started_at) * 1000,
            "prompt_tokens": self._usage_value(usage, "prompt_tokens"),
            "completion_tokens": self._usage_value(usage, "completion_tokens"),
            "total_tokens": self._usage_value(usage, "total_tokens"),
            "prompt_cache_hit_tokens": self._usage_value(usage, "prompt_cache_hit_tokens"),
            "prompt_cache_miss_tokens": self._usage_value(usage, "prompt_cache_miss_tokens"),
        }

    def _call_sync(self, prompt: str) -> Dict[str, Any]:
        if self.provider == "deepseek":
            return self._call_deepseek_sync(prompt)
        return self._call_gemini_sync(prompt)

    def _emit_success(self, result: Dict[str, Any], *, fallback_used: bool = False, fallback_provider: str | None = None) -> None:
        emit_judge_usage(
            provider=self.provider,
            model=self.model_name,
            status="success",
            fallback_used=fallback_used,
            fallback_provider=fallback_provider,
            ttft_ms=result.get("ttft_ms"),
            total_latency_ms=result["total_latency_ms"],
            prompt_tokens=result.get("prompt_tokens"),
            completion_tokens=result.get("completion_tokens"),
            total_tokens=result.get("total_tokens"),
            prompt_cache_hit_tokens=result.get("prompt_cache_hit_tokens"),
            prompt_cache_miss_tokens=result.get("prompt_cache_miss_tokens"),
        )

    async def generate_json(self, prompt: str, pm=None) -> Dict[str, Any]:
        started_at = time.perf_counter()
        try:
            result = await asyncio.to_thread(self._call_sync, prompt)
            parsed = json.loads(result["text"])
            self._emit_success(result)
            if pm:
                pm.record("Tier 3 (LLM Inf)", time.perf_counter() - started_at)
            return parsed
        except Exception as exc:
            retryable = self.provider == "deepseek" and self._is_retryable_deepseek_error(exc)
            if retryable and self.fallback_engine:
                try:
                    fallback_result = await asyncio.to_thread(self.fallback_engine._call_sync, prompt)
                    parsed = json.loads(fallback_result["text"])
                    self.fallback_engine._emit_success(
                        fallback_result,
                        fallback_used=True,
                        fallback_provider=self.provider,
                    )
                    if pm:
                        pm.record("Tier 3 (LLM Inf)", time.perf_counter() - started_at)
                    return parsed
                except Exception as fallback_exc:
                    emit_judge_usage(
                        provider=self.provider,
                        model=self.model_name,
                        status="error",
                        total_latency_ms=(time.perf_counter() - started_at) * 1000,
                        fallback_used=True,
                        fallback_provider=self.fallback_engine.provider,
                        error_type=type(fallback_exc).__name__,
                    )
                    print(f"LLM fallback error: {fallback_exc}")
            else:
                emit_judge_usage(
                    provider=self.provider,
                    model=self.model_name,
                    status="error",
                    total_latency_ms=(time.perf_counter() - started_at) * 1000,
                    error_type=type(exc).__name__,
                )
            print(f"LLM Error: {exc}")
            return {"level": 1, "is_correct": False, "explanation": "Error occurred."}
