import json
import logging
from typing import Any


LOGGER = logging.getLogger("chilan.llm_judge")


def emit_judge_usage(
    *,
    provider: str,
    model: str,
    status: str,
    total_latency_ms: float,
    ttft_ms: float | None = None,
    prompt_tokens: int | None = None,
    completion_tokens: int | None = None,
    total_tokens: int | None = None,
    prompt_cache_hit_tokens: int | None = None,
    prompt_cache_miss_tokens: int | None = None,
    fallback_used: bool = False,
    fallback_provider: str | None = None,
    error_type: str | None = None,
) -> None:
    """Emit privacy-safe, low-cardinality judge telemetry as one JSON log line."""
    event: dict[str, Any] = {
        "event": "llm_judge_usage",
        "provider": provider,
        "model": model,
        "status": status,
        "fallback_used": fallback_used,
        "total_latency_ms": round(total_latency_ms, 2),
    }
    optional_values = {
        "ttft_ms": ttft_ms,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "prompt_cache_hit_tokens": prompt_cache_hit_tokens,
        "prompt_cache_miss_tokens": prompt_cache_miss_tokens,
        "fallback_provider": fallback_provider,
        "error_type": error_type,
    }
    event.update({key: value for key, value in optional_values.items() if value is not None})
    LOGGER.info(json.dumps(event, ensure_ascii=False, separators=(",", ":")))
