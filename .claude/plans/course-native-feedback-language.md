# Correct Tier-3 Feedback Language by Course Support Language

## Problem
The generic judge prompt now follows each item's `feedback_language`. That field can be missing, stale, or incorrectly authored in existing item metadata. In the reported Chinese-to-English exercise, the expected answer is English and the learner's course support/native language is English, but the Tier-3 explanation was generated in Chinese.

The learner-facing feedback language must be determined from the enrolled course's canonical support language, not inferred from the answer language and not trusted from historical item metadata. A learner changing the UI locale does not change the pedagogical language of the course; `courses.source_language` remains the authoritative course support/native language.

## Changes

### `backend/routers/study.py`
- Extend the existing authoritative evaluation query for `language_items` to join `courses` by `q.course_id` and select `c.source_language` as the resolved course feedback language.
- After loading `item_metadata`, create a request-local copy and override only `feedback_language` with this server-owned course value when it is present.
- Pass that enriched metadata to `StudyEvaluator.process_judge()` as today.
- Do not accept a feedback-language value from the evaluate request, and do not mutate the database during evaluation.

This makes an English-support Chinese course consistently generate English Tier-3 feedback, e.g. for `好 → bien`: “You answered ‘bien’, which is French… This exercise requires an English answer.”

### `backend/services/study/practice_item_schema.py`
- Keep `feedback_language` as an explicit schema-v2 field for artifacts and offline validation.
- Document/encode the distinction that it is a stored default, while online evaluation may replace it with the enrolled course's `source_language` for a server-authoritative learner-facing explanation.
- Preserve existing language-code normalization (`english` → `en`, etc.) so course rows that store full language names work without changing database values.

### Tests
- Add a focused study-evaluation route test with an item whose persisted metadata says `feedback_language: zh` but whose joined course has `source_language: english`; assert the mocked evaluator receives `feedback_language: english` (or normalized `en` at the prompt boundary) while `prompt_language` and `answer_language` are unchanged.
- Add a prompt-level assertion that the metadata after normalization produces an English explanation instruction for the Chinese-to-English example.
- Retain a fallback test for a course whose `source_language` is empty: preserved item-level `feedback_language` remains available rather than replacing it with an empty value.

## Verification

```bash
cd backend
../.venv/Scripts/python.exe -m unittest backend.tests.test_study_evaluate
../.venv/Scripts/python.exe tests/test_practice_item_schema.py
../.venv/Scripts/python.exe tests/test_new_concept_practice_types.py
```

No frontend payload or UI-language change is needed for this repair: the backend resolves feedback language from the authenticated learner's enrolled course and the canonical item/course records.
