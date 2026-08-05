# Question Type and Language Metadata Canonicalization Audit

**Investigation Date**: 2026-08-04  
**Status**: Read-only investigation (no modifications made)

## Executive Summary

The Chilan platform currently uses **named direction-specific question types** (e.g., `CN_TO_EN`, `EN_TO_CN`, `JA_SPEAK`) alongside **canonical generic types** (e.g., `SPEAK`, `LISTEN_WRITE`, `TRANSLATE`). A transition to purely canonical generic types with language metadata is feasible but requires careful orchestration across:

- **Frontend UI rendering** (language badges, prompts, themes)
- **Backend LLM evaluation prompts** (tuned to audience + direction)
- **Content builder pipelines** (question generation for 4+ languages)
- **Database schema** (storage and query patterns)
- **Migration paths** for 1000s of existing questions

---

## I. Current Architecture

### A. Question Type Definition Points

#### 1. Content Builder (Question Generation)

**Files**:
- `backend/content_builder/zh/integrated_chinese/tasks/quiz_generator.py`
- `backend/content_builder/en/new_concept_english/tasks/content_extractor.py`
- `backend/content_builder/ja/minna_no_nihongo/tasks/practice_generator.py`

**Current Types Generated**:
- **Chinese course** (Integrated Chinese):
  - `EN_TO_CN` (English → Chinese translation)
  - `CN_TO_EN` (Chinese → English translation)
  - `SPEAK` (spoken Chinese; metadata includes `speech_language`, `audio_language`, `support_language`)
  - `LISTEN_WRITE` (Chinese dictation; metadata includes `audio_language`, `support_language`)

- **English course** (New Concept English):
  - `PATTERN_DRILL` (English grammar pattern exercises)
  - `TARGET_TO_SUPPORT` (English → Chinese translation)
  - `TARGET_SPEAK` (English speaking)
  - `TARGET_LISTEN_WRITE` (English dictation)

- **Japanese course** (Minna no Nihongo):
  - `JA_TO_CN` (Japanese → Chinese)
  - `CN_TO_JA` (Chinese → Japanese)
  - `JA_SPEAK` (Japanese speaking)
  - `JA_LISTEN_WRITE` (Japanese dictation)

- **Multi-language variants** (dynamic patterns):
  - `CN_TO_{LANG}` → generates `TARGET_LANGUAGE={LANG}`, `SUPPORT_LANGUAGE=zh`
  - `{LANG}_TO_CN` → generates `TARGET_LANGUAGE=zh`, `SUPPORT_LANGUAGE={LANG}`
  - `{LANG}_SPEAK` → canonical `SPEAK` + metadata
  - `{LANG}_LISTEN_WRITE` → canonical `LISTEN_WRITE` + metadata

#### 2. Database Layer

**Files**:
- `backend/database/sync_to_db.py` (persistence)
- `backend/database/migrate_integrated_chinese_practice_types.py` (migration utility)

**Storage**:
- `language_items` table has `question_type` column (TEXT, no constraint)
- Metadata stored in `metadata` JSONB column with fields:
  - `target_language` (e.g., "en", "zh", "ja")
  - `support_language` (e.g., "en", "zh")
  - `speech_language` (for SPEAK questions)
  - `audio_language` (for LISTEN_WRITE questions)
  - `answer_language`, `answer_mode`, `source_language`, `prompt_language`

**Migration Pattern** (pre-canonicalization):
```
Legacy: "EN_TO_CN_SPEAK" → Canonical: "SPEAK" + {target_language: "zh", support_language: "en", speech_language: "zh", audio_language: "en"}
Legacy: "CN_LISTEN_WRITE" → Canonical: "LISTEN_WRITE" + {target_language: "zh", support_language: "en", audio_language: "zh"}
```

#### 3. Backend LLM Evaluation

**Files**:
- `backend/services/llm/prompts.py` (evaluation rubrics)
- `backend/routers/study.py` (evaluation request handling)

**Current Prompt Mapping** (lines ~28-300):
```python
_EXACT_PROMPTS = {
    "CN_TO_EN":           # For Chinese native speakers, evaluate CN→EN translation
    "EN_TO_CN":           # For English native speakers, evaluate EN→CN translation
    "PATTERN_DRILL":      # For Chinese native speakers, evaluate English pattern
    "TARGET_TO_SUPPORT":  # For Chinese native speakers, evaluate EN→CN translation
    "TARGET_LISTEN_WRITE": # For English speakers, evaluate English dictation
    "TARGET_SPEAK":       # For English speakers, evaluate English speaking
    "CN_TO_JA":           # For Chinese native speakers, evaluate CN→JA translation
    "JA_TO_CN":           # For Chinese native speakers, evaluate JA→CN translation
    "JA_LISTEN_WRITE":    # For English speakers, evaluate Japanese dictation
    "JA_SPEAK":           # For English speakers, evaluate Japanese speaking
}
```

**Prompt Selection Logic** (`get_eval_prompt()`):
```
if normalized_type == "SPEAK":
    → Dynamic prompt based on metadata.target_language (audience = English speakers)
if normalized_type == "LISTEN_WRITE":
    → Dynamic prompt based on metadata.target_language (audience = English speakers)
if normalized_type in ("SUPPORT_TO_TARGET",):
    → Use PATTERN_DRILL prompt (for Chinese native speakers)
if {CN_LISTEN_WRITE, JA_LISTEN_WRITE, TARGET_LISTEN_WRITE}:
    → Use LISTEN_WRITE prompt (audience = English speakers)
```

#### 4. Frontend UI Rendering

**File**: `frontend/src/pages/studyPage/practice/questionTypeConfig.js`

**Current Approach**:
- Hardcoded `CONFIGS` for 10 named types: `CN_TO_EN`, `EN_TO_CN`, `EN_TO_CN_SPEAK`, `CN_LISTEN_WRITE`, `PATTERN_DRILL`, `SUPPORT_TO_TARGET`, `TARGET_TO_SUPPORT`, `TARGET_LISTEN_WRITE`, `TARGET_SPEAK`
- Dynamic matching for patterns: `CN_TO_{LANG}`, `{LANG}_TO_CN_SPEAK`, `{LANG}_TO_CN`, `{LANG}_LISTEN_WRITE`, `{LANG}_SPEAK`
- For `SPEAK` and `LISTEN_WRITE`: calls `buildCanonicalSpeakConfig()` / `buildCanonicalListenWriteConfig()` to resolve metadata into UI config

**Metadata Resolution** (fallback chain):
```javascript
target_language ← metadata.target_language 
                 || metadata.targetLanguage 
                 || metadata.answer_language 
                 || metadata.answerLanguage
                 || metadata.speech_language 
                 || metadata.audio_language

support_language ← metadata.support_language 
                  || metadata.supportLanguage
                  || metadata.source_language 
                  || metadata.sourceLanguage
                  || metadata.prompt_language 
                  || metadata.promptLanguage
```

**Badge and Prompt Labels**:
- `CN_TO_EN` badge: "翻译 · 中→英" (Chinese to English)
- `SPEAK` badge: "_buildSpeakBadge(targetLanguage)" (e.g., "口语 · 中文" for Chinese speaking)
- `LISTEN_WRITE` badge: "_buildDictationBadge(targetLanguage)" (e.g., "听写 · 中文" for Chinese dictation)

**Fallback Config** (if no match):
```javascript
CN_TO_EN config (answerMode: "text", targetLanguage: "en", supportLanguage: "zh", theme: blue)
```

---

## II. Named Direction Types - Complete Inventory

### Translation Types
| Type | Source | Target | Audience | Backend Prompt | Frontend Theme |
|------|--------|--------|----------|---|---|
| `CN_TO_EN` | Chinese | English | ? (unclear) | ✓ explicit | blue |
| `EN_TO_CN` | English | Chinese | English speakers | ✓ explicit | emerald |
| `TARGET_TO_SUPPORT` | English | Chinese | Chinese native speakers | uses PATTERN_DRILL | emerald |
| `CN_TO_{LANG}` | Chinese | *dynamic* | English speakers | derived from CN_TO_EN | blue |
| `{LANG}_TO_CN` | *dynamic* | Chinese | English speakers | derived from EN_TO_CN | emerald |
| `CN_TO_JA` | Chinese | Japanese | ? | ✓ explicit | (unknown) |
| `JA_TO_CN` | Japanese | Chinese | ? | ✓ explicit | (unknown) |

### Speech Types
| Type | Language | Audience | Backend Prompt | Frontend Theme |
|---|---|---|---|---|
| `EN_TO_CN_SPEAK` | Chinese | English speakers | derived from SPEAK | rose |
| `TARGET_SPEAK` | English | English speakers | ✓ explicit | teal |
| `JA_SPEAK` | Japanese | ? | ✓ explicit | (unknown) |
| `SPEAK` (canonical) | *metadata.target_language* | English speakers | derived dynamically | rose/teal/varies |
| `{LANG}_SPEAK` | *dynamic* | English speakers | derived from SPEAK | (dynamic) |

### Dictation Types
| Type | Language | Audience | Backend Prompt | Frontend Theme |
|---|---|---|---|---|
| `CN_LISTEN_WRITE` | Chinese | English speakers | implicit via config | indigo |
| `TARGET_LISTEN_WRITE` | English | English speakers | ✓ explicit | indigo |
| `JA_LISTEN_WRITE` | Japanese | ? | ✓ explicit | indigo |
| `LISTEN_WRITE` (canonical) | *metadata.target_language* | English speakers | derived dynamically | indigo |
| `{LANG}_LISTEN_WRITE` | *dynamic* | English speakers | derived from LISTEN_WRITE | indigo |

### Pattern Drills
| Type | Purpose | Target Audience | Backend Prompt |
|---|---|---|---|
| `PATTERN_DRILL` | English grammar | Chinese native speakers | ✓ explicit |
| `SUPPORT_TO_TARGET` | English→Chinese pattern | Chinese native speakers | uses PATTERN_DRILL |

---

## III. Metadata Schema - Current State

### Fields Always in `metadata` Dict

**Frontend-consumed fields** (in `PRACTICE_METADATA_FIELDS`):
```
answer_mode, answer_language, answerLanguage, audio_id, audio_language,
line_ref, prompt_language, show_knowledge_card, source_language,
source_ref, source_section, speech_eval_config, speech_language,
support_language, supportLanguage, target_language, targetLanguage, tts_language
```

**Backend-consumed fields** (in `PRACTICE_CONTEXT_FIELDS`):
```
audio_id, audio_language, line_ref, pattern, slot, source_ref,
source_section, support_language, target_language
```

### Encoding Ambiguities

1. **Language code inconsistency**:
   - Database/prompts use lowercase: `zh`, `en`, `ja`
   - UI labels use uppercase: `CN`, `EN`, `JA`, `FR`, etc.
   - Conversion via `LABEL_CODE_ALIASES` and `LANG_CODE_ALIASES`

2. **Metadata key case variance**:
   - snake_case: `target_language`, `support_language`, `audio_language`, `speech_language`, `tts_language`, `source_language`, `prompt_language`, `answer_language`
   - camelCase: `targetLanguage`, `supportLanguage`, `answerLanguage`, `answerLanguage`
   - Frontend uses both; fallback chain prefers snake_case

3. **Fallback ambiguity in "speech" vs. "audio"**:
   - `speech_language` = language student speaks (for SPEAK questions)
   - `audio_language` = language of the audio prompt (for LISTEN_WRITE questions)
   - But both can appear in metadata; no mutual exclusivity constraint

4. **`answer_language` vs. `target_language`**:
   - `answer_language` used in some prompts/metadata
   - `target_language` is the canonical field
   - Fallback chain tries both but may diverge if both exist with different values

---

## IV. Canonicalization Feasibility Analysis

### ✅ What's Already Canonical

1. **Generic `SPEAK` and `LISTEN_WRITE` exist and work**:
   - Frontend has builders: `buildCanonicalSpeakConfig()`, `buildCanonicalListenWriteConfig()`
   - Backend handles them dynamically: `if normalized_q_type == "SPEAK"` deriving prompt from metadata

2. **Metadata-based language resolution is plumbed**:
   - Frontend already uses `resolveTargetLanguage()` and `resolveSupportLanguage()` to extract language from metadata
   - Database schema already stores metadata JSONB
   - Migration script (`migrate_integrated_chinese_practice_types.py`) already canonicalizes `EN_TO_CN_SPEAK` → `SPEAK` + metadata

3. **Multi-language pipelines are emerging**:
   - Japanese and French content exist; they use variants like `JA_TO_CN`, `CN_TO_JA`, `CN_TO_FR`
   - Frontend pattern matching already supports `CN_TO_{LANG}`, `{LANG}_SPEAK`, etc.

### ⚠️ Critical Compatibility Risks

#### Risk 1: Backend Prompt Mapping is Audience-Specific
**Problem**: Evaluation prompts are tuned for a **specific audience** (e.g., "for Chinese native speakers" vs. "for English speakers"). Named types encode this:
- `CN_TO_EN` → assumes evaluator is English speaker (evaluates for naturalness in English)
- `EN_TO_CN` → assumes evaluator is English speaker (evaluates for semantic equivalence in Chinese)
- `PATTERN_DRILL` → assumes evaluator is Chinese speaker (evaluates for correctness in a teaching context)

If we canonicalize to generic `TRANSLATE`, the backend must infer audience from metadata. Current logic:
```python
if metadata.target_language == "en":
    # Assume audience is English speaker
else:
    # Assume audience is Chinese speaker (fallback)
```

**Risk**: This breaks if:
- A Chinese speaker needs to evaluate English (e.g., for fluency in an intermediate lesson)
- A Japanese speaker needs to evaluate Chinese translation
- Audience is not deterministically derivable from direction

**Mitigation**: Add explicit `audience` or `evaluator_language` metadata field; otherwise, canonicalization **cannot safely replace named types**.

#### Risk 2: Frontend Theme Selection Loses Semantic Coupling
**Problem**: Named types hardcode theme selection:
```javascript
EN_TO_CN_SPEAK → rose (romantic; Chinese speaking)
TARGET_SPEAK → teal (calm; English speaking)
```

With pure metadata, theme selection becomes algorithmic:
```javascript
if (targetLanguage === "zh" && answerMode === "speech") theme = rose
else if (targetLanguage === "en" && answerMode === "speech") theme = teal
```

**Risk**: If theme logic must change (e.g., new UI colors, new language pairs), it's scattered across 20+ lines of conditional logic, harder to maintain.

**Mitigation**: Use a **composition function** instead of conditionals, e.g., `selectTheme(targetLanguage, answerMode, targetCourse)`.

#### Risk 3: Badge and Prompt Label Generation Breaks for Unfamiliar Language Pairs
**Problem**: Current badge builders assume specific known pairs:
```javascript
_buildTranslateBadge('CN', 'EN') → "翻译 · 中→英"
_buildTranslateBadge('JA', 'CN') → "翻译 · 日→中"
```

For new language pairs, the fallback is:
```javascript
_buildTranslateBadge('DE', 'KO') → "翻译 · 德→韩" (using LANG_ABBREV[lang])
```

**Risk**: If LANG_ABBREV is not updated with a new language, or abbreviation is culturally inappropriate, badge is wrong.

**Mitigation**: Ensure `LANG_ABBREV` and `LANG_NAME` are always complete before adding new language pairs.

#### Risk 4: Existing Questions Can't Be Safely Re-typed Retroactively
**Problem**: ~5,000 questions are already in the database with type `EN_TO_CN`, `PATTERN_DRILL`, etc. If we globally change `question_type` to `TRANSLATE`, we must:
1. Back-fill metadata for ~5,000 questions with the correct `target_language`, `support_language`
2. Handle questions that don't have metadata (fill with defaults)
3. Update all existing user progress, review logs, embeddings by question_type

**Risk**: If a single question is mis-typed during migration, it will:
- Use wrong evaluation prompt (wrong audience)
- Display wrong badge/theme
- Break cached embeddings for evaluation (if any)

**Mitigation**: Run migration in a **dry-run mode first**, verify metadata is correct for 100% of questions before applying.

#### Risk 5: Frontend Pattern Matching Becomes Ad-Hoc
**Problem**: Current frontend has explicit pattern matchers:
```javascript
if ((m = type.match(/^CN_TO_(\w+)$/))) { /* handle CN_TO_JA, CN_TO_FR, etc. */ }
if ((m = type.match(/^(\w+)_SPEAK$/))) { /* handle JA_SPEAK, FR_SPEAK, etc. */ }
```

If canonicalized to `SPEAK` + metadata, pattern matching is no longer needed. But **old databases might still have `JA_SPEAK` questions**. Compatibility requires:
- Keep pattern matchers indefinitely, OR
- Migrate all old questions before deploying canonical-only code

**Mitigation**: Make migration a **prerequisite**, not an afterthought.

---

## V. File Map: Changes Required for Canonicalization

### Backend

| File | Current Role | Change Type | Risk Level |
|------|---|---|---|
| `backend/services/llm/prompts.py` | Hardcoded prompts per type | Consolidate to `TRANSLATE`, `SPEAK`, `LISTEN_WRITE`, `PATTERN_DRILL`; add audience inference | HIGH |
| `backend/routers/study.py` | Question type used in evaluation requests | Add metadata validation; ensure audience is resolved | MEDIUM |
| `backend/services/study/init_flow_service.py` | Serializes questions for frontend | Ensure metadata is always present | MEDIUM |
| `backend/database/sync_to_db.py` | Persists questions | Add migration on INSERT for legacy types | MEDIUM |
| `backend/database/migrate_integrated_chinese_practice_types.py` | One-time migration script | Extend to all named types; make idempotent | MEDIUM |
| `backend/content_builder/zh/integrated_chinese/tasks/quiz_generator.py` | Generates questions | Output canonical `SPEAK`, `LISTEN_WRITE`, `EN_TO_CN` only | LOW |
| `backend/content_builder/en/new_concept_english/tasks/content_extractor.py` | Generates questions | Output canonical `SPEAK`, `LISTEN_WRITE`, `TRANSLATE` only | LOW |
| `backend/content_builder/ja/minna_no_nihongo/tasks/practice_generator.py` | Generates questions | Output canonical types only | LOW |

### Frontend

| File | Current Role | Change Type | Risk Level |
|------|---|---|---|
| `frontend/src/pages/studyPage/practice/questionTypeConfig.js` | Type config lookup | Remove hardcoded CONFIGS; compute from metadata | HIGH |
| `frontend/src/pages/studyPage/practice/PracticeSection.jsx` | Question rendering | Use only `getQuestionTypeConfig()`; no fallback to type name | MEDIUM |
| `frontend/src/pages/studyPage/teaching/components/LessonPracticePreview.jsx` | Preview rendering | Same as above | MEDIUM |

### Tests

| File | Current Role | Change Type | Risk Level |
|------|---|---|---|
| `backend/tests/test_new_concept_practice_types.py` | Validates prompt selection | Update to test canonical types + metadata combinations | MEDIUM |
| `backend/tests/test_migrate_integrated_chinese_practice_types.py` | Validates migration | Extend to all 20+ named types | MEDIUM |
| Any integration tests | E2E question flow | May need to generate canonical types instead of named | LOW |

---

## VI. Recommended Migration Path

### Phase 1: Metadata Completeness Audit (No code changes)
- Scan all 5,000+ questions in DB
- Identify which lack `target_language`, `support_language`
- Identify which have inconsistent metadata (both `answer_language` and `target_language` but with different values)

### Phase 2: Explicit Audience Metadata (Backend changes only)
- Add `evaluator_language` or `rubric_audience` field to metadata
- Back-fill based on question_type:
  - `EN_TO_CN`, `PATTERN_DRILL` → `evaluator_language: "zh"`
  - `CN_TO_EN`, others → `evaluator_language: "en"`
- Update `get_eval_prompt()` to use explicit field, not inferred

### Phase 3: Backend Canonicalization (Incremental)
- New content builder pipelines output only `SPEAK`, `LISTEN_WRITE`, `TRANSLATE`, `PATTERN_DRILL`
- Modify `get_eval_prompt()` to accept canonical types + metadata
- Keep hardcoded prompts as fallback; log warnings for old types

### Phase 4: Frontend Canonicalization (Incremental)
- Modify `questionTypeConfig.js` to build all configs from metadata
- Keep pattern matchers as fallback; log warnings for old types
- Ensure all 4 languages have appropriate badges/themes

### Phase 5: Database Migration (Scheduled maintenance)
- Run `migrate_integrated_chinese_practice_types.py --all-langs --apply-json --sync-db`
- Verify prompt selection for spot-check of 20 questions per language/type
- Verify badges/themes render correctly in frontend

### Phase 6: Cleanup (Post-migration, 1+ month later)
- Remove pattern matchers from frontend
- Remove fallback prompts from backend
- Remove hardcoded CONFIGS from `questionTypeConfig.js`

---

## VII. Canonical Type Definitions (Proposed)

### Core Types
1. **`TRANSLATE`** (generic translation)
   - Metadata: `target_language`, `support_language`
   - Audience inferred from: `evaluator_language` field (if explicit) or language pair heuristic
   - Frontend: Dynamic badge using `_buildTranslateBadge(support_language, target_language)`
   - Theme: Varies by target language; no hardcoded theme

2. **`SPEAK`** (generic speaking)
   - Metadata: `target_language`, `support_language`, `speech_language` (optional; defaults to `target_language`), `audio_language` (for prompt audio)
   - Backend audience: Always English speakers (learning target language)
   - Frontend: Dynamic badge `_buildSpeakBadge(target_language)`
   - Theme: `rose` for Chinese, `teal` for English, varies for others

3. **`LISTEN_WRITE`** (generic dictation)
   - Metadata: `target_language`, `support_language`, `audio_language` (language of prompt audio)
   - Backend audience: Always English speakers
   - Frontend: Dynamic badge `_buildDictationBadge(target_language)`
   - Theme: Always `indigo`

4. **`PATTERN_DRILL`** (grammar pattern exercises)
   - Metadata: `target_language` (English), `support_language` (language of instructions)
   - Backend audience: Chinese native speakers (specific audience)
   - Frontend: Static badge (no language variation)
   - Theme: `amber`

---

## VIII. Open Questions / Unclear Mappings

1. **Who is the audience for `CN_TO_EN`?**
   - Prompt doesn't specify ("Expert Language Coach" without "for whom")
   - Is it for English speakers learning Chinese, or Chinese speakers learning English?
   - Affects evaluation criteria (naturalness vs. semantic equivalence weighting)

2. **Why do Japanese questions have explicit prompts (JA_SPEAK, JA_LISTEN_WRITE) but Chinese/English speak/dictation use generic SPEAK?**
   - Is it because Japanese is newer and uses canonical types?
   - Or because Japanese has a different target audience?

3. **What should the theme be for French, German, Korean, etc. SPEAK questions?**
   - Currently hardcoded only for Chinese (rose) and English (teal)
   - Is rose reserved for target_language="zh"? Should German SPEAK be teal?

4. **Can metadata be incomplete in production?**
   - Some old questions might have `question_type` but no `metadata` dict
   - Frontend fallback assumes `metadata` exists and is a dict; what if it's null/missing?

---

## IX. Test Coverage Gaps

### Currently Tested (✓)
- `test_new_concept_practice_types.py`: Validates 16 question type + metadata combinations
- Pattern matching for `CN_TO_{LANG}`, `{LANG}_SPEAK`, etc. works in frontend

### NOT Currently Tested (✗)
- Metadata fallback chain: What if `target_language` is missing but `answer_language` exists?
- Theme selection: No test for "does French SPEAK use the right theme?"
- Badge generation: No test for "new language pair generates correct badge without error"
- Migration: No test for "can re-migrate a question that's already canonical?"
- Database schema: No constraint preventing `question_type` typos (e.g., "SPEAK_CHINESE" vs "SPEAK")

---

## X. Summary Table: Type Ecosystem

| **Dimension** | **Status** | **Notes** |
|---|---|---|
| **Generic SPEAK type** | ✓ Exists, used | Works, but metadata must be complete |
| **Generic LISTEN_WRITE type** | ✓ Exists, used | Works, but metadata must be complete |
| **Generic TRANSLATE type** | ✗ Doesn't exist | Would require consolidating CN_TO_EN, EN_TO_CN, CN_TO_{LANG}, {LANG}_TO_CN, etc. |
| **Named types (CN_TO_EN, etc.)** | ✓ Widely used | ~5,000 questions in production; migration required |
| **Pattern matching (CN_TO_{LANG})** | ✓ Works | Frontend handles dynamically; backend doesn't |
| **Metadata completeness** | ⚠️ Partial | Old questions may lack metadata; new ones include it |
| **Backend audience inference** | ⚠️ Implicit | Inferred from question_type; not explicit metadata |
| **Frontend theme selection** | ⚠️ Hardcoded | Specific types → specific themes; breaks for new language pairs |
| **Documentation** | ✗ Missing | No spec for "which prompts are for which audiences" |

---

## Recommendations for Safe Canonicalization

### If Proceeding with Canonicalization:

1. **Make audience explicit**: Add `evaluator_language` to metadata; don't infer from direction
2. **Test exhaustively**: Add tests for all 50+ metadata combinations
3. **Migrate incrementally**: New content uses canonical types; old content uses migration script
4. **Validate before deletion**: Spot-check 50 migrated questions before removing old prompt code
5. **Version the schema**: Document canonical types in a schema constant; update in parallel with code

### If Staying with Named Types:

1. **Document the mapping**: Create a table of type → prompt → audience
2. **Enforce in schema**: Add CHECK constraint to `language_items.question_type` to prevent typos
3. **Limit additions**: Don't add new named types; use `{LANG}_SPEAK` pattern instead
4. **Formalize patterns**: Document regex patterns for multi-language types

---

## Files to Review

**Backend Priority**:
1. `/d/gaopeng16/Desktop/Chilan/backend/services/llm/prompts.py` (lines 1–300) – evaluate audience mapping
2. `/d/gaopeng16/Desktop/Chilan/backend/database/migrate_integrated_chinese_practice_types.py` – understand migration pattern
3. `/d/gaopeng16/Desktop/Chilan/backend/services/study/init_flow_service.py` – serialization of metadata

**Frontend Priority**:
1. `/d/gaopeng16/Desktop/Chilan/frontend/src/pages/studyPage/practice/questionTypeConfig.js` (lines 200–486) – type config and pattern matching
2. `/d/gaopeng16/Desktop/Chilan/frontend/src/pages/studyPage/practice/PracticeSection.jsx` (line 74) – usage of `getQuestionTypeConfig()`

**Tests**:
1. `/d/gaopeng16/Desktop/Chilan/backend/tests/test_new_concept_practice_types.py` – current coverage baseline

