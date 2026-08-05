# Canonical, Language-Agnostic Practice Schema

## Approved scope
Replace direction-encoded **practice-item** question types (`CN_TO_EN`, `EN_TO_CN`, `CN_TO_JA`, `JA_TO_CN`, `TARGET_TO_SUPPORT`, etc.) with canonical activity types backed by explicit per-item language metadata. This affects new content generation, existing JSON/DB records, Tier 3 prompt rendering, frontend presentation, and knowledge lookups.

Course categories such as `EN_TO_CN`, `FR_TO_CN`, and `CN_TO_JA` remain unchanged: they identify a course/catalogue relationship, not the kind of exercise a learner is answering.

## Canonical contract

### Question types
- `TRANSLATE` — semantic translation evaluation.
- `SPEAK` — spoken answer evaluated from ASR text.
- `LISTEN_WRITE` — strict dictation / listening transcription.
- `PATTERN_DRILL`, `PARTICLE_FILL`, and `CONJUGATION` remain distinct skill types because their grading rules are intentionally stricter than semantic translation.

`SUPPORT_TO_TARGET` stays a legacy alias only during artifact migration and becomes `PATTERN_DRILL`, not `TRANSLATE`.

### Required metadata on canonical language exercises
Every generated/migrated language item will carry:

```json
{
  "practice_schema_version": 2,
  "prompt_language": "zh",
  "answer_language": "ja",
  "feedback_language": "zh",
  "answer_mode": "text"
}
```

Additional fields:
- `speech_language` for `SPEAK` (must equal `answer_language` unless a deliberately different ASR locale is required).
- `audio_language` for `LISTEN_WRITE` (normally equals `answer_language`) and for listening/speaking prompt audio.
- optional `vocabulary_word` only where an item is tied to a vocabulary record; this replaces direction-name heuristics when storing or loading vocabulary knowledge.

`target_language`, `support_language`, and direction-derived language inference are removed from new item data. Existing records are converted to the explicit fields during migration. `feedback_language` is deliberately separate from the expected answer language: an English-speaking learner can answer in Chinese but receive English feedback.

## Implementation

### 1. Centralize pure schema normalization
**New:** `backend/services/study/practice_item_schema.py`

Create a dependency-free module shared by content builders, sync/migration tools, and the judge layer. It will:

- define the canonical type constants and supported ISO-style language-code aliases;
- validate/normalize `prompt_language`, `answer_language`, `feedback_language`, `answer_mode`, `speech_language`, and `audio_language`;
- map legacy direction types to a canonical type plus explicit language values only when the pipeline/default language context makes that mapping unambiguous;
- reject incomplete or contradictory canonical metadata instead of silently falling back to Chinese/English;
- preserve unrelated metadata, while stripping retired `target_language` / `support_language` fields only in the explicit migration path;
- provide one helper for determining the optional vocabulary key from `metadata.vocabulary_word` before any legacy fallback.

The normalizer will accept pipeline-level defaults (`course_target_language`, `course_support_language`) so each generator can provide known language context without embedding it in a question-type string.

### 2. Make judge prompts generic and fail closed
**Update:** `backend/services/llm/prompts.py` and `backend/services/llm/tools.py`

Replace the direction-specific `_EXACT_PROMPTS` and `CN_TO_*` / `*_TO_CN` regular-expression routing with generic prompt renderers:

- `TRANSLATE`: semantic equivalence between `prompt_language` and `answer_language`;
- `SPEAK`: ASR-aware semantic evaluation in `answer_language`;
- `LISTEN_WRITE`: strict transcription evaluation in `answer_language`;
- generic strict templates for `PATTERN_DRILL`, `PARTICLE_FILL`, and `CONJUGATION`.

Each renderer derives role wording, expected-answer language, explanation language, and second-person form from explicit metadata. The final `# Evaluation Input` section continues to contain the only per-request values (`question`, `standards`, and `user_answer`), so the cache-friendly prefix layout implemented in the preceding change is retained.

`LanguageTools.judge_with_ai()` will validate/normalize the item metadata before asking for a prompt. A missing required language field becomes a controlled evaluation error rather than falling through to the current `CN_TO_EN` default prompt.

### 3. Emit canonical items from all pipelines
**Update:**
- `backend/content_builder/zh/integrated_chinese/tasks/quiz_generator.py`
- `backend/content_builder/en/new_concept_english/tasks/practice_generator.py`
- `backend/content_builder/ja/minna_no_nihongo/tasks/practice_generator.py`
- language profile sort-order definitions as required.

For each generated item, emit `TRANSLATE`, `SPEAK`, `LISTEN_WRITE`, or the retained skill type and populate the schema-v2 language fields from the known source material:

- Integrated Chinese: Chinese answer exercises use `answer_language=zh`, `feedback_language=en`; reverse comprehension/translation items explicitly indicate their English answer language.
- New Concept English: English-output pattern/speaking/listening drills use `answer_language=en`, `feedback_language=zh`; English-to-Chinese comprehension becomes `TRANSLATE` with `answer_language=zh`, `feedback_language=zh`.
- Minna no Nihongo: Japanese-output exercises use `answer_language=ja`, `feedback_language=zh`; Japanese-to-Chinese comprehension becomes `TRANSLATE` with `answer_language=zh`, `feedback_language=zh`.

Update LLM generation contracts, fallback item builders, type allowlists, deduplication/sort rules, and output normalization to require the canonical shape. Add `vocabulary_word` at generation time for word-level translation cards so later persistence does not infer the word from type names.

### 4. Update persistence and study APIs
**Update:**
- `backend/database/sync_to_db.py`
- `backend/database/backfill_localized_vocab.py`
- `backend/routers/study.py`
- `backend/services/study/init_flow_service.py`

Changes:

- validate schema-v2 metadata before upserting a canonical item;
- use `metadata.vocabulary_word` for vocabulary-knowledge association, retaining legacy regex inference only inside the one-time compatibility/migration path;
- make `/study/knowledge` prefer the metadata-derived vocabulary word rather than `CN_TO_*` / `*_TO_CN` type patterns;
- expose `prompt_language`, `answer_language`, `feedback_language`, `speech_language`, `audio_language`, and `practice_schema_version` through the safe pre-evaluation practice DTO; and
- retain course-level `target_language` / `source_language` fields unchanged because they describe the course, not an item’s expected response.

### 5. Convert historical artifacts and database rows safely
**New:** `backend/database/migrate_practice_item_schema.py`

Provide an explicit, idempotent migration tool with dry-run as the default. It will:

1. scan every registered pipeline artifact root and derive the pipeline/course language defaults;
2. report counts by legacy type, canonical target type, missing/contradictory language metadata, and unresolvable records;
3. write backups before mutating JSON when `--apply-json` is passed;
4. optionally update matching `language_items` rows with `--apply-db`, validating `course_id`, `lesson_id`, `question_id`, and unchanged answers before an update;
5. verify after a DB apply that no direction-encoded item types remain and every canonical item has valid schema-v2 language fields.

Keep `backend/database/migrate_integrated_chinese_practice_types.py` as a short deprecation wrapper until the new script has replaced its documented use; do not silently run either migration during application startup.

Before any production apply, run the dry-run and resolve every unresolvable/conflicting item. Apply JSON first, inspect samples from each pipeline/language direction, then update the database in a separately approved maintenance step.

### 6. Render canonical items dynamically in the frontend
**Update:**
- `frontend/src/pages/studyPage/practice/questionTypeConfig.js`
- `frontend/src/pages/studyPage/teaching/components/LessonPracticePreview.jsx`

Refactor `questionTypeConfig.js` to build practice behavior from canonical type + explicit language metadata:

- `TRANSLATE`: generate the prompt label and badge from `prompt_language → answer_language`; choose a deterministic visual theme from answer mode/language rather than direction-specific config objects.
- `SPEAK` / `LISTEN_WRITE`: keep their existing mode/audio behavior but resolve labels and expected language from schema-v2 metadata.
- retained skill types use generic strict-answer UI behavior with their metadata-supplied languages.

The teaching preview will display a readable dynamic type label and hint (for example, `翻译 · 英→中`) rather than raw legacy direction keys.

Do not change `frontend/src/assets/patterns.js`: it is keyed by **course category**, which intentionally remains directional.

## Tests and verification

### Backend automated coverage
- Add focused schema-normalization tests for every legacy-direction mapping, canonical validation failure, and legacy `SUPPORT_TO_TARGET → PATTERN_DRILL` exception.
- Replace the direction-specific prompt tests in `backend/tests/test_new_concept_practice_types.py` with a matrix covering all canonical activity types across Chinese, English, Japanese, and one additional language. Assert correct role/expected-answer/feedback language wording and that request values remain only in the final `# Evaluation Input` section.
- Extend evaluator unit tests to call Tier 3 using `TRANSLATE` plus schema-v2 metadata.
- Update NCE, MNN, and Integrated Chinese generator tests to assert canonical output types and explicit metadata, including vocabulary-word behavior.
- Add migration-fixture tests for dry-run, idempotence, metadata preservation, rejected ambiguities, JSON backup creation, and DB preflight matching.
- Update vocabulary-knowledge and study-init tests to verify that canonical metadata, not a direction-shaped type string, controls lookup and client projection.

### Commands

```bash
cd backend
../.venv/Scripts/python.exe tests/test_new_concept_practice_types.py
PYTHONIOENCODING=utf-8 ../.venv/Scripts/python.exe tests/test_evaluator_unit.py
../.venv/Scripts/python.exe tests/test_migrate_integrated_chinese_practice_types.py
# plus the new schema/migration/generator focused test files

cd frontend
npm run lint
npm run build
```

### Migration acceptance criteria
- Dry-run reports no unresolved item before a production apply.
- All migrated `language_items` use only canonical activity types.
- Every `TRANSLATE`, `SPEAK`, `LISTEN_WRITE`, and retained skill item has required schema-v2 language metadata.
- A sampled item from every pipeline and language direction renders the expected input, target answer control, audio behavior, and feedback language.
- Tier 3 logs confirm the rendered generic prompt matches the item metadata and preserves the stable-prefix/cache-friendly layout.
