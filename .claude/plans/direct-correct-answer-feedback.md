# Direct Correct-Answer Feedback

## Goal
When Tier 3 marks an answer incorrect, its **second of exactly two feedback sentences** must state a usable expected answer drawn from the stored reference answers. This prevents vague feedback such as “it is incorrect” without telling the learner what to say instead.

Because translation references are examples rather than an exhaustive semantic set, the feedback will say **“A correct answer is …”**, not imply that one stored wording is the only valid phrasing.

## `backend/services/llm/prompts.py`

Update the `# Requirements` block of every generic judge template:

- `_TRANSLATE_TPL`
- `_SPEAK_TPL`
- `_LISTEN_WRITE_TPL`
- `_PATTERN_DRILL_TPL` (including particle, conjugation, tone, and measure-word variants that reuse it)

Keep the two-sentence contract, but make the second-sentence behavior explicit:

1. **Sentence 1** continues to explain what the student answer means, says, or got wrong.
2. **Sentence 2** branches by judgment:
   - If incorrect (`is_correct=false`, normally levels 1–2): begin with an expected answer, quoting one or two suitable references from `Reference ... Answers`; then briefly say why it is the needed correction.
   - If correct (`is_correct=true`, levels 3–4): confirm correctness and, where useful, offer a concise improvement. Do not invent a correction.

Use activity-specific wording:

- Translation / speaking / pattern: “A correct answer is ‘…’.” If two references are appropriate: “A correct answer is ‘…’ or ‘…’.”
- Dictation: “The corrected sentence is ‘…’.” because exact/near-exact wording is the requirement.

Explicitly preserve the existing semantic-paraphrase rule for `TRANSLATE` and `SPEAK`: reference answers are examples, and an equivalent answer can still be accepted. The response should choose a reference only as a concrete correction for a response already judged incorrect.

No changes to prompt order: the request-specific references remain in the final `# Evaluation Input` section, preserving the cache-friendly stable prefix.

## `backend/tests/test_new_concept_practice_types.py`

Add prompt-contract assertions covering all four generic template families:

- Translation and speaking include a rule to quote an appropriate reference answer when incorrect.
- Dictation includes the explicit corrected-sentence rule.
- Pattern drills include the direct expected-answer rule.
- All still contain “exactly 2 short sentences” and retain the final `# Evaluation Input` order regression.

This is a template-contract test, not a live-model judgment test; real output quality remains observed through production feedback after deployment.

## Verification

```bash
cd backend
../.venv/Scripts/python.exe tests/test_new_concept_practice_types.py
../.venv/Scripts/python.exe tests/test_llm_engine_deepseek.py
../.venv/Scripts/python.exe tests/test_evaluator_unit.py
```

## Expected Learner Result

For `小姐` answered as `mister`, feedback should follow this form:

```text
Your answer means “mister,” which refers to a male.
A correct answer is “Miss” or “young lady,” because 小姐 refers to a female.
```

The answer card returned by the API remains unchanged; this change makes the in-line explanatory feedback independently actionable as well.
