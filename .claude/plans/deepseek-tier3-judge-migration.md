# DeepSeek Tier-3 Judge Migration

## Objective
Make DeepSeek V4 Flash the configurable production Tier-3 judge while retaining Gemini as an explicitly configured fallback, preserving the existing `LanguageTools → LLMEngine.generate_json()` contract and adding per-request cache/TTFT telemetry.

## Provider and request design

### `backend/services/llm/base_engine.py`
Refactor `LLMEngine` into a small provider-dispatched façade without changing callers:

- Keep `generate_json(prompt, pm=None)` returning the same parsed dictionary/error fallback shape.
- Retain the Gemini branch and its Vertex option for fallback/support.
- Add a DeepSeek branch using the existing `openai` dependency and the OpenAI-compatible endpoint:
  ```text
  https://api.deepseek.com
  ```
- Read DeepSeek configuration:
  ```env
  LLM_JUDGE_PROVIDER=deepseek
  LLM_JUDGE_DEEPSEEK_API_KEY=
  LLM_JUDGE_DEEPSEEK_MODEL_ID=deepseek-v4-flash
  LLM_JUDGE_DEEPSEEK_BASE_URL=https://api.deepseek.com
  LLM_JUDGE_DEEPSEEK_TIMEOUT_SECONDS=30
  LLM_JUDGE_DEEPSEEK_MAX_RETRIES=1
  LLM_JUDGE_DEEPSEEK_MAX_TOKENS=512
  LLM_JUDGE_DEEPSEEK_USER_ID=chilan-tier3
  ```
- Use non-thinking mode deliberately—DeepSeek enables thinking by default:
  ```python
  messages=[{"role": "user", "content": prompt}],
  temperature=0.0,
  max_tokens=512,
  response_format={"type": "json_object"},
  stream=True,
  stream_options={"include_usage": True},
  extra_body={
      "thinking": {"type": "disabled"},
      "user_id": "chilan-tier3",
  },
  ```
  The system-wide opaque `user_id` is intentional. DeepSeek documents that `user_id` isolates KVCaches, so it must be shared by requests that should share the generic judge-prompt cache; do **not** send raw learner IDs or personally identifying data.
- Consume stream chunks safely:
  - first content-bearing chunk records `ttft_ms`;
  - concatenate `choices[0].delta.content` for normal chunks;
  - accept the final usage-only chunk where `choices=[]` and extract `usage`;
  - parse the complete JSON only after the stream ends.
- Extract and log DeepSeek cache telemetry from the final usage object:
  - `prompt_cache_hit_tokens`
  - `prompt_cache_miss_tokens`
  - standard prompt/completion/total Token fields
  - `ttft_ms` and complete request latency.
- Do not add cache values to `PerformanceMonitor.stages`, which only represents seconds. Continue recording `Tier 3 (LLM Inf)` with total request duration.

### Retry / fallback behavior
- DeepSeek retries only transient API failures (`429`, `500`, `502`, `503`, `504`, connection and timeout errors), using short bounded exponential waits. Do not retry invalid JSON/API validation responses blindly.
- Add optional configured fallback:
  ```env
  LLM_JUDGE_FALLBACK_PROVIDER=gemini
  ```
  When DeepSeek exhausts a retryable failure, invoke a separately configured Gemini engine once. Mark every fallback in telemetry. Never fallback on a valid DeepSeek judgment merely because it is marked incorrect.
- The first release does **not** automatically fall back on a JSON parse failure; report it as a provider failure in telemetry so JSON-mode behavior is visible. A later reliability decision can enable fallback based on observed parse failures.

## Observability

### New module: `backend/services/llm/judge_metrics.py`
Introduce a lightweight structured logger/adapter that emits one JSON event per Tier-3 model call. It should carry only low-cardinality or numeric fields:

```json
{
  "event": "llm_judge_usage",
  "provider": "deepseek",
  "model": "deepseek-v4-flash",
  "status": "success",
  "fallback_used": false,
  "prompt_cache_hit_tokens": 0,
  "prompt_cache_miss_tokens": 0,
  "prompt_tokens": 0,
  "completion_tokens": 0,
  "ttft_ms": 0,
  "total_latency_ms": 0
}
```

Include `question_type`, `prompt_language`, `answer_language`, `feedback_language`, and a static prompt schema/version only if they are controlled finite values. Do **not** log prompt text, student answers, reference answers, course/item/user IDs, cache IDs, or raw provider errors containing request content.

This enables dashboards for:

```text
cache coverage = hit / (hit + miss)
TTFT p50/p95 by cache hit versus miss
JSON/provider error rate
fallback rate
estimated input cost and actual output volume
```

## Configuration and documentation

### `backend/.env.example`
- Add the DeepSeek judge variables above with blank API key and `deepseek-v4-flash` default model.
- Keep Gemini settings, but annotate that Gemini is optional when `LLM_JUDGE_PROVIDER=deepseek` and serves as the recommended emergency fallback.
- Add a comment: thinking must remain disabled for the short structured judge workload.

### `CLAUDE.md`
- Update the LLM-judge provider description to state Tier 3 supports Gemini and DeepSeek V4 Flash.
- Document the environment selector and the cache telemetry fields, including the fact that prompt caching is best-effort and is monitored through usage—not presumed.

## Test coverage

### New: `backend/tests/test_llm_engine_deepseek.py`
Mock `openai.OpenAI` and test:

1. `LLMEngine.from_env()` selects DeepSeek and validates its API key/model configuration.
2. DeepSeek uses the exact base URL, JSON response format, `thinking.disabled`, stream usage inclusion, temperature `0.0`, token cap, and opaque `user_id`.
3. A normal content chunk plus a terminal `choices=[]` usage chunk returns parsed judge JSON.
4. The usage event contains cache hit/miss tokens, TTFT, latency, provider, and model—but not prompt/answer text.
5. A valid no-cache response (`hit=0`) is successful, not an error.
6. Retryable 429/5xx failures retry to the configured limit; non-retryable 4xx does not.
7. Optional Gemini fallback runs once only after DeepSeek has exhausted a retryable failure and telemetry marks it.
8. JSON parsing/provider errors keep the current safe `{"level": 1, "is_correct": false, ...}` behavior.

### Existing tests
- Keep [test_evaluator_unit.py](backend/tests/test_evaluator_unit.py) as the provider-independent behavior contract.
- Add a `LanguageTools` test verifying the generic schema-v2 prompt still reaches `generate_json()` unchanged under either provider.
- Run existing study-route tests to verify the recently added course-native feedback language remains provider-independent.

## Rollout

1. Deploy code with Gemini still configured as primary; enable telemetry first.
2. Add the DeepSeek key and set:
   ```env
   LLM_JUDGE_PROVIDER=deepseek
   LLM_JUDGE_FALLBACK_PROVIDER=gemini
   ```
3. Run a controlled test set covering `TRANSLATE`, `SPEAK`, `LISTEN_WRITE`, and strict pattern/conjugation items in English, Chinese, Japanese, and another supported course language.
4. Monitor cache coverage, TTFT p50/p95, malformed-JSON rate, fallback rate, and qualitative judgment agreement with Gemini for at least several hundred Tier-3 calls.
5. Keep the DeepSeek shared `user_id` stable. Changing it partitions the provider cache and resets cache warmness.

## Verification commands

```bash
cd backend
../.venv/Scripts/python.exe tests/test_llm_engine_deepseek.py
../.venv/Scripts/python.exe tests/test_evaluator_unit.py
../.venv/Scripts/python.exe tests/test_new_concept_practice_types.py
# Run the study evaluate test module through its package loader.

cd frontend
npm run build
```

## Important DeepSeek contract points
- JSON mode: `response_format={"type": "json_object"}` plus a prompt that explicitly requests JSON.
- Thinking is enabled by default; disable it with `extra_body={"thinking": {"type": "disabled"}}` for this latency-sensitive, deterministic workload.
- The stream's usage chunk may have empty `choices`; handle it before accessing `choices[0]`.
- Caching is automatic and best-effort. A cache hit requires a persisted, fully matching prefix unit, and unused cache entries are typically cleared after hours to days.
