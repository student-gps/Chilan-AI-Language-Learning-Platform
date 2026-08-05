# Question Type Canonicalization: File Change Map

## Backend Files to Modify

### 1. **backend/services/llm/prompts.py** (717 lines)

**Current State**:
- Lines 28–300: Hardcoded prompts for 10+ question types
- `_EXACT_PROMPTS` dict with keys: CN_TO_EN, EN_TO_CN, PATTERN_DRILL, TARGET_TO_SUPPORT, TARGET_LISTEN_WRITE, TARGET_SPEAK, CN_TO_JA, JA_TO_CN, JA_LISTEN_WRITE, JA_SPEAK
- `get_eval_prompt(q_type, metadata=None)` function that selects prompt

**Changes Required** (if canonicalizing):
- Consolidate `_EXACT_PROMPTS` to only 4 keys: TRANSLATE, SPEAK, LISTEN_WRITE, PATTERN_DRILL
- Add `_get_evaluator_language(q_type, metadata)` helper to extract explicit evaluator_language from metadata
- Modify `get_eval_prompt()` to:
  - If `q_type == "TRANSLATE"`: use evaluator_language from metadata to pick prompt
  - If `q_type == "SPEAK"` or "LISTEN_WRITE": audience is always English speakers (no change)
  - If `q_type == "PATTERN_DRILL"`: audience is always Chinese speakers (or read from metadata)
- Add fallback logic for old question types (CN_TO_EN → TRANSLATE + metadata) for backward compat

**Impact**: CRITICAL
- Wrong prompt selection will teach students with wrong rubric
- Must test exhaustively before deploying

**Tests to Update**:
- `backend/tests/test_new_concept_practice_types.py` (line 22–73)
  - Add test cases for TRANSLATE with different evaluator_language values
  - Add test cases for missing evaluator_language (should still work but log warning)

---

### 2. **backend/database/migrate_integrated_chinese_practice_types.py** (400+ lines)

**Current State**:
- Migrates EN_TO_CN_SPEAK → SPEAK + metadata
- Migrates CN_LISTEN_WRITE → LISTEN_WRITE + metadata
- Runs on sync_to_db.py or standalone

**Changes Required** (if canonicalizing):
- Extend to migrate ALL named types:
  - CN_TO_EN → TRANSLATE + {target_language: "en", support_language: "zh", evaluator_language: "?"}
  - EN_TO_CN → TRANSLATE + {target_language: "zh", support_language: "en", evaluator_language: "en"}
  - TARGET_TO_SUPPORT → TRANSLATE + {target_language: "zh", support_language: "en", evaluator_language: "zh"}
  - CN_TO_{LANG} → TRANSLATE + {target_language: {LANG}, support_language: "zh"}
  - {LANG}_TO_CN → TRANSLATE + {target_language: "zh", support_language: {LANG}}
  - etc.
- Add heuristic to infer evaluator_language if not present
- Add dry-run mode to preview all changes before applying
- Add validation: "After migration, does metadata have required fields?"
- Ensure idempotency: "If question is already canonical, skip it"

**Impact**: HIGH
- Migration failure = wrong questions in production
- Must run dry-run first; spot-check 50 questions manually

---

### 3. **backend/routers/study.py** (line 75–90)

**Current State**:
- `EvaluateRequest` class takes `question_type: str`
- Passes to evaluator service: `get_eval_prompt(question_type, metadata=None)`

**Changes Required** (if canonicalizing):
- Add validation: Check that `question_type` is one of {TRANSLATE, SPEAK, LISTEN_WRITE, PATTERN_DRILL}
- Add validation: If TRANSLATE, metadata must have target_language + support_language
- Add warning: If question_type is an old named type (EN_TO_CN), log deprecation
- No logic change needed; just validation

**Impact**: LOW
- Validation prevents invalid requests early
- Logging helps identify clients using old types

---

### 4. **backend/services/study/init_flow_service.py** (line 15–79)

**Current State**:
- `PRACTICE_METADATA_FIELDS` whitelist (line 15–34) defines which metadata fields are allowed
- `serialize_practice_item()` filters metadata to safe fields

**Changes Required** (if canonicalizing):
- Add `evaluator_language` to PRACTICE_METADATA_FIELDS
- Ensure serialization includes evaluator_language in response to frontend
- Add comment explaining why this field is needed

**Impact**: LOW
- Just adds one field to whitelist + response
- No breaking changes

---

### 5. **backend/database/sync_to_db.py** (line 743–836)

**Current State**:
- Persists question_type to database
- No validation on question_type values (TEXT column, no constraint)

**Changes Required** (if canonicalizing):
- Add CHECK constraint: `question_type IN ('TRANSLATE', 'SPEAK', 'LISTEN_WRITE', 'PATTERN_DRILL')`
  - OR add to allowlist (permissive for backward compat during transition)
- Add NOT NULL constraint on metadata for new questions
- Call `migrate_integrated_chinese_practice_types.py` during sync if question_type is old named type
- Log migration summary

**Impact**: MEDIUM
- Schema changes are backwards-compatible (just add constraint)
- Must test with existing 7,500 questions to ensure constraint is satisfiable

---

### 6. **backend/content_builder/** (Multiple files)

#### **backend/content_builder/zh/integrated_chinese/tasks/quiz_generator.py**
- Line 850: Sets `"question_type": "EN_TO_CN"`
- Lines 935, 989, 1085, 1139, 1174, 1215: Sets `"question_type": "SPEAK"` or `"LISTEN_WRITE"`

**Changes Required** (if canonicalizing):
- Change EN_TO_CN → TRANSLATE (or keep as-is if backward compat is maintained during transition)
- Ensure metadata includes `target_language`, `support_language`, `evaluator_language`
- SPEAK/LISTEN_WRITE are already canonical ✓

**Impact**: LOW

#### **backend/content_builder/en/new_concept_english/tasks/content_extractor.py**
- Line 166: Sets `"question_type": "PATTERN_DRILL"`
- Line 182: Sets `"question_type": "TARGET_TO_SUPPORT"`

**Changes Required** (if canonicalizing):
- PATTERN_DRILL is already canonical ✓
- TARGET_TO_SUPPORT → TRANSLATE (with evaluator_language: "zh")
- Add metadata for support_language, target_language

**Impact**: LOW

#### **backend/content_builder/ja/minna_no_nihongo/tasks/practice_generator.py**
- Sets `"question_type": "JA_TO_CN"`, `"JA_SPEAK"`, `"JA_LISTEN_WRITE"`

**Changes Required** (if canonicalizing):
- JA_TO_CN → TRANSLATE + metadata
- JA_SPEAK → SPEAK + metadata
- JA_LISTEN_WRITE → LISTEN_WRITE + metadata
- Ensure metadata includes target_language, support_language, evaluator_language

**Impact**: LOW

---

## Frontend Files to Modify

### 1. **frontend/src/pages/studyPage/practice/questionTypeConfig.js** (500 lines)

**Current State**:
- Lines 200–321: Hardcoded CONFIGS for 10 named types
- Lines 354–403: `buildCanonicalSpeakConfig()` and `buildCanonicalListenWriteConfig()`
- Lines 405–486: `getQuestionTypeConfig()` with pattern matching for dynamic types

**Changes Required** (if canonicalizing):
- Remove lines 200–321 (hardcoded CONFIGS)
- Consolidate config builders into single `buildConfigFromMetadata(question_type, metadata)`
- Modify pattern matching to handle backward compat only (with deprecation logging)
- Add theme selection function based on target_language + answerMode:
  ```javascript
  function selectTheme(targetLanguage, answerMode) {
    if (answerMode === 'speech') {
      if (targetLanguage === 'zh') return THEMES.rose;
      if (targetLanguage === 'en') return THEMES.teal;
      return THEMES.teal; // default for other languages
    }
    if (answerMode === 'listen_write') return THEMES.indigo;
    if (answerMode === 'pattern') return THEMES.amber;
    // else text/translate
    if (targetLanguage === 'en') return THEMES.blue;
    return THEMES.emerald;
  }
  ```
- Add i18n keys for badge labels for all language pairs

**Impact**: CRITICAL
- 300+ lines of code change
- Affects all practice questions
- Must test all language pairs

**Tests to Add**:
- Theme selection: All 16 languages × 4 answer modes = 64 combinations
- Badge generation: All language pair combinations
- Metadata fallback chain: Missing fields, conflicting fields
- Backward compat: Old pattern-matched types still work

---

### 2. **frontend/src/pages/studyPage/practice/PracticeSection.jsx** (line 74)

**Current State**:
- Line 74: `const questionConfig = useMemo(() => getQuestionTypeConfig(currentQuestion), [currentQuestion])`

**Changes Required**:
- No changes needed if `getQuestionTypeConfig()` is updated
- Ensure metadata is passed correctly to getQuestionTypeConfig

**Impact**: LOW

---

### 3. **frontend/src/pages/studyPage/teaching/components/LessonPracticePreview.jsx**

**Current State**:
- Uses `getQuestionTypeConfig()` for preview rendering

**Changes Required**:
- No changes needed if `getQuestionTypeConfig()` is updated

**Impact**: LOW

---

## Test Files to Update/Create

### 1. **backend/tests/test_new_concept_practice_types.py** (78 lines)

**Current State**:
- Tests 16 question type + metadata combinations
- Validates prompt templates
- Checks format compliance

**Changes Required** (if canonicalizing):
- Extend to test TRANSLATE with all evaluator_language values
- Add tests for missing evaluator_language (backward compat)
- Add tests for theme selection in frontend
- Add tests for new language pairs (FR, DE, KO, etc.)

**Impact**: LOW
- Just add test cases; existing tests still pass

---

### 2. **backend/tests/test_migrate_integrated_chinese_practice_types.py** (NEW or extended)

**Current State**:
- Tests migration of EN_TO_CN_SPEAK → SPEAK

**Changes Required** (if canonicalizing):
- Add tests for migration of all 20+ named types
- Test idempotency: Re-running migration doesn't break already-migrated questions
- Test validation: Check metadata is complete after migration
- Test with actual DB data (dry-run)

**Impact**: MEDIUM
- Comprehensive migration tests are critical

---

### 3. **frontend/src/pages/studyPage/practice/__tests__/** (NEW)

**Changes Required** (if canonicalizing):
- Add test file for `questionTypeConfig.js`
  - Test theme selection for all language pairs
  - Test badge generation for all language pairs
  - Test metadata fallback chain
  - Test backward compat (pattern matching)
- Add snapshot tests for config objects

**Impact**: MEDIUM
- Frontend tests currently missing; need to add

---

## Configuration Files to Update

### 1. **CLAUDE.md** (Project documentation)

**Current State**:
- Lines ~50–100: Documents architecture and routes
- No mention of question types or canonicalization

**Changes Required**:
- Add section: "Question Types and Metadata"
- Document canonical types: TRANSLATE, SPEAK, LISTEN_WRITE, PATTERN_DRILL
- Document metadata schema: target_language, support_language, evaluator_language, etc.
- Explain design decision: why evaluator_language is needed

**Impact**: LOW
- Documentation only; no code impact

---

## Summary Table: Changes by File

| File | Lines | Changes | Risk | Tests |
|---|---|---|---|---|
| prompts.py | 300+ | Consolidate prompts to 4 types; add evaluator_language logic | CRITICAL | 10+ new cases |
| migrate_integrated_chinese_practice_types.py | 100+ | Extend to all named types; add dry-run | HIGH | 50+ scenarios |
| init_flow_service.py | 5 | Add evaluator_language to whitelist | LOW | 0 |
| sync_to_db.py | 20 | Add schema validation; call migration | MEDIUM | 5 |
| quiz_generator.py (zh) | 5 | Output TRANSLATE instead of EN_TO_CN | LOW | 0 |
| content_extractor.py (en) | 5 | Output TRANSLATE instead of TARGET_TO_SUPPORT | LOW | 0 |
| practice_generator.py (ja) | 5 | Output TRANSLATE, SPEAK, LISTEN_WRITE | LOW | 0 |
| questionTypeConfig.js | 300+ | Remove hardcoded configs; compute from metadata | CRITICAL | 64+ combinations |
| test_new_concept_practice_types.py | 20+ | Add test cases for TRANSLATE + evaluator_language | MEDIUM | New cases |
| test_migrate_*.py | 100+ | Comprehensive migration tests | HIGH | New file |
| CLAUDE.md | 50+ | Document canonical types and metadata | LOW | 0 |
| **Total** | **~700 LOC changed** | **~11 files touched** | **CRITICAL-HIGH** | **~150 tests** |

---

## Recommended Implementation Order

### Phase 1 (Week 1): Backend Groundwork
1. Modify `prompts.py`: Add evaluator_language logic, keep fallback for old types
2. Extend `migrate_integrated_chinese_practice_types.py`: Add all named types
3. Update `sync_to_db.py`: Add schema validation
4. Update `init_flow_service.py`: Add evaluator_language to whitelist
5. **Test**: Run migration script on test DB; verify 100 spot-check questions

### Phase 2 (Week 2): New Content Builders
1. Update `quiz_generator.py`, `content_extractor.py`, `practice_generator.py` to output canonical types
2. Ensure all new content includes complete metadata
3. **Test**: Generate lesson 101 in each language; verify questions render

### Phase 3 (Week 3): Frontend Refactor
1. Refactor `questionTypeConfig.js`: Build configs from metadata
2. Add theme selection logic for all language pairs
3. Add i18n entries for all badge/prompt labels
4. **Test**: Add 64+ test cases for theme selection; add snapshot tests for configs

### Phase 4 (Week 4): Database Migration
1. Run migration script in dry-run mode
2. Spot-check 50 questions per language
3. Verify prompts are selected correctly for spot-check
4. Run with `--apply-json --sync-db`
5. Monitor production for errors

### Phase 5 (Week 5+): Cleanup
1. Remove pattern matching from frontend (keep only canonical types)
2. Remove fallback prompt logic from backend
3. Add CHECK constraint to database schema
4. Update CLAUDE.md with final canonical definitions

---

## Rollback Procedures

| Phase | Rollback | Effort |
|---|---|---|
| After Phase 1 | Revert prompts.py; fallback to old type names | LOW (5 min) |
| After Phase 2 | Revert generators; new lessons use old types | LOW (10 min) |
| After Phase 3 | Revert questionTypeConfig.js; use pattern matching | LOW (10 min) |
| After Phase 4 | Restore from DB backup; revert sync_to_db.py | MEDIUM (30 min) |
| After Phase 5 | Restore pattern matching code; restore prompts.py | HIGH (2 hours) |

