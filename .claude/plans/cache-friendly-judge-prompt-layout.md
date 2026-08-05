# Cache-Friendly Judge Prompt Layout

## Goal
Move the per-request values in every online Tier 3 judge prompt—the question, reference answers, and student/ASR answer—to one final `# Evaluation Input` section. This preserves the existing grading instructions and response contract while making each prompt's reusable policy prefix stable for Gemini implicit/explicit context caching.

## Scope

### `backend/services/llm/prompts.py`
- Update all 10 exact judge templates in `_EXACT_PROMPTS`:
  - `CN_TO_EN`, `EN_TO_CN`, `PATTERN_DRILL`, `TARGET_TO_SUPPORT`, `TARGET_LISTEN_WRITE`, `TARGET_SPEAK`, `CN_TO_JA`, `JA_TO_CN`, `JA_LISTEN_WRITE`, and `JA_SPEAK`.
- Update all five language-rendered template families:
  - `_CN_TO_X_TPL`, `_X_TO_CN_TPL`, `_X_TO_CN_SPEAK_TPL`, `_SPEAK_TPL`, and `_LISTEN_WRITE_TPL`.
- For every template:
  1. Remove the current early `# Context` block containing `{question}`, `{standards}`, and `{user_answer}`.
  2. Leave its role, task, policy, evaluation steps, grading scale, requirements, and JSON-only output contract unchanged and in their current relative order.
  3. Append a final `# Evaluation Input` block after `# Output Format`, with the same labels and the three existing placeholders in the existing question → references → student-answer order.
- Keep language metadata fields (for example `{lang_name}`, `{target_name}`, `{support_name}`, and `{you}`) in the reusable template prefix. They are selected once per question-type/language template, not from a learner's request; keeping them there enables stable, language-specific cache prefixes.
- Do not change the `get_eval_prompt()` resolution rules, prompt wording, model parameters, or request payload format. `LanguageTools.judge_with_ai()` will continue filling the same three values using `str.format()`.

### `backend/tests/test_new_concept_practice_types.py`
- Retain the existing targeted-template/legacy-alias assertions.
- Add table-driven, offline tests that render one representative from every physical prompt template family using unique sentinels for question, reference answers, and student answer.
- Assert that each sentinel appears only after the final `# Evaluation Input` heading and that the final section places question, references, and student answer in the expected order.
- Cover all exact templates and all five dynamic template families, including language metadata for generic `SPEAK` and `LISTEN_WRITE` rendering. This protects future prompt edits from moving a per-request value back into the cacheable prefix.

## Verification
1. Run the focused regression test:
   ```bash
   cd backend
   python -m unittest tests.test_new_concept_practice_types
   ```
2. Run existing evaluator coverage to confirm the Tier 3 call contract is unchanged:
   ```bash
   cd backend
   python -m unittest tests.test_evaluator_unit
   ```
3. Optionally inspect a rendered prompt for a representative translation and speech item to confirm that the final request text contains the new `# Evaluation Input` section and that its JSON output contract remains unchanged.

## Expected Result and Limitation
This change makes the static instructions a proper shared prefix. It does not itself guarantee Gemini cache hits: the resulting stable prefix must still meet the active model's minimum token threshold (2,048 tokens for Gemini 2.5 Flash implicit caching) and be reused within the provider's cache window. Cache telemetry remains a separate follow-up.
