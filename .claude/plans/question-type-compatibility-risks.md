# Question Type Canonicalization: Compatibility Risk Matrix

## Type Inventory Across Courses

| Course | Current Question Types | Target Canonical Types | Migration Barrier |
|--------|---|---|---|
| **Integrated Chinese (zh)** | EN_TO_CN, CN_TO_EN, SPEAK, LISTEN_WRITE | TRANSLATE, SPEAK, LISTEN_WRITE | ✓ Low; SPEAK/LISTEN_WRITE already canonical |
| **New Concept English (en)** | PATTERN_DRILL, TARGET_TO_SUPPORT, TARGET_SPEAK, TARGET_LISTEN_WRITE | PATTERN_DRILL, TRANSLATE, SPEAK, LISTEN_WRITE | ⚠️ Medium; requires renaming TARGET_* |
| **Minna no Nihongo (ja)** | JA_TO_CN, CN_TO_JA, JA_SPEAK, JA_LISTEN_WRITE | TRANSLATE, SPEAK, LISTEN_WRITE | ⚠️ Medium; SPEAK/LISTEN_WRITE already canonical |
| **Multi-language variants** | CN_TO_{LANG}, {LANG}_TO_CN, {LANG}_SPEAK, {LANG}_LISTEN_WRITE | TRANSLATE, SPEAK, LISTEN_WRITE | ✓ Low; already use metadata for language |

**Total Questions**: ~5,000–10,000 across all courses
**Named Types**: 20+ unique types (CN_TO_EN, EN_TO_CN, PATTERN_DRILL, TARGET_SPEAK, JA_SPEAK, CN_TO_JA, etc.)
**Canonical Types Needed**: 4 (TRANSLATE, SPEAK, LISTEN_WRITE, PATTERN_DRILL)

---

## Metadata Completeness Audit Required

| Scenario | Likelihood | Impact | Detection |
|---|---|---|---|
| Old question has `question_type = "EN_TO_CN"` but NO metadata | HIGH | Wrong evaluation prompt (assumes English speaker when direction says English input) | Scan DB for NULL metadata + old types |
| Metadata has `answer_language` but NOT `target_language` | MEDIUM | Frontend fallback chain works, but inconsistent | Grep metadata JSON |
| Metadata has conflicting values: `answer_language = "en"` AND `target_language = "zh"` | LOW-MEDIUM | Fallback chain picks one; may be wrong | Compare fields |
| New content builder outputs metadata but old handwritten JSON doesn't | HIGH | Must backfill or version migrations | Check all ~300 JSON files in artifacts/ |

---

## Backend Compatibility Analysis

### LLM Prompt Selection (`backend/services/llm/prompts.py`)

| Prompt Type | Current Storage | Named Types | Generic Types | Risks |
|---|---|---|---|---|
| CN→EN translation | Explicit `_EXACT_PROMPTS["CN_TO_EN"]` | CN_TO_EN | TRANSLATE + metadata | ✓ Safe; prompt is language-agnostic |
| EN→CN translation | Explicit `_EXACT_PROMPTS["EN_TO_CN"]` | EN_TO_CN, {LANG}_TO_CN | TRANSLATE + metadata | ⚠️ Audience unclear; assumes English speaker |
| Chinese speaking | Generated per target_language | SPEAK, EN_TO_CN_SPEAK | SPEAK + metadata | ✓ Safe; explicitly "for English speakers" |
| English dictation | Explicit `_EXACT_PROMPTS["TARGET_LISTEN_WRITE"]` | TARGET_LISTEN_WRITE, JA_LISTEN_WRITE | LISTEN_WRITE + metadata | ⚠️ Audience implicit in type |
| English pattern drill | Explicit `_EXACT_PROMPTS["PATTERN_DRILL"]` | PATTERN_DRILL, SUPPORT_TO_TARGET | PATTERN_DRILL + metadata | ⚠️ Audience = Chinese speakers; must be explicit |

**Risk Level**: ⚠️ **MEDIUM-HIGH**
- Canonicalization requires explicit `evaluator_language` metadata to avoid wrong prompts

### Database Persistence Layer (`backend/database/sync_to_db.py`)

| Operation | Current Code | Impact of Canonicalization |
|---|---|---|
| INSERT new question | Stores question_type as-is; no validation | ✓ Just ensure metadata is populated |
| UPDATE existing question | Rare; typically read-only after insert | ✓ No change |
| Migration of old types | `migrate_integrated_chinese_practice_types.py` exists | ✓ Already canonicalizes SPEAK/LISTEN_WRITE variants |
| Query by type | `WHERE question_type = %s` (indexed) | ⚠️ Queries break if types change; must update all | 
| Backward compatibility reads | Old code reads old types via pattern matching | ✓ Safe; just slow if 1000s of queries |

**Risk Level**: ⚠️ **LOW-MEDIUM**
- Schema change is not needed (question_type is TEXT, flexible)
- Query updates needed only if backward compat is dropped

---

## Frontend Compatibility Analysis

### Question Type Config Resolution (`frontend/src/pages/studyPage/practice/questionTypeConfig.js`)

| Code Path | Current Behavior | Canonicalization Behavior | Risk |
|---|---|---|---|
| **Hardcoded CONFIGS** (10 types) | Direct lookup: `CONFIGS["CN_TO_EN"]` | Remove; all types use metadata | HIGH—must compute all configs from metadata |
| **Pattern matching CN_TO_{LANG}** | Regex extracts LANG; builds config | Can stay as fallback for old questions | MEDIUM—tech debt if not removed later |
| **buildCanonicalSpeakConfig()** | Uses metadata to build UI config | Becomes primary code path | ✓ Already works |
| **Fallback (unknown type)** | Returns CN_TO_EN defaults | Should not exist if all types canonical | MEDIUM—need to remove fallback |
| **Metadata fallback chain** | Tries 6 field names for language | Works; but inconsistent | LOW—add validation |

**Risk Level**: ⚠️ **MEDIUM-HIGH**
- 500 lines of UI config code must be rewritten
- Pattern matchers must persist as backward compat until DB is migrated
- Theme selection becomes data-driven (no hardcoded rose/teal)

**Specific Compatibility Issues**:

1. **Theme selection for new language pairs**:
   - Currently: `EN_TO_CN_SPEAK` → hardcoded rose (romantic, Chinese)
   - Proposed: Compute from target_language = "zh" AND answerMode = "speech"
   - **Risk**: What theme for German SPEAK? French SPEAK? No rules exist.

2. **Badge generation for new language pairs**:
   - Currently: `_buildTranslateBadge("CN", "EN")` → "翻译 · 中→英"
   - Proposed: `_buildTranslateBadge(support_language, target_language)` with LANG_ABBREV lookup
   - **Risk**: If LANG_ABBREV is missing a language, badge breaks silently.

3. **Prompt label generation**:
   - Currently: Hardcoded per type + localization table
   - Proposed: Build from canonical type + metadata + i18n
   - **Risk**: Must ensure all language + direction combinations have i18n entries.

---

## Data Migration Risks

### Estimated Question Volume

| Course | Questions | Named Types | Metadata Completeness |
|---|---|---|---|
| Integrated Chinese | ~4,000 | EN_TO_CN, CN_TO_EN, SPEAK, LISTEN_WRITE | ⚠️ Unknown |
| New Concept English | ~2,000 | PATTERN_DRILL, TARGET_* | ⚠️ Unknown |
| Minna no Nihongo | ~1,000 | JA_TO_CN, JA_SPEAK, JA_LISTEN_WRITE | ⚠️ Unknown |
| Multi-lang (French, German, etc.) | ~500 | CN_TO_FR, FR_TO_CN, etc. | ✓ Likely complete (newer) |
| **Total** | **~7,500** | **20+ types** | **⚠️ Partial** |

### Migration Failure Scenarios

| Scenario | Probability | Damage | Example |
|---|---|---|---|
| Metadata backfill creates wrong `target_language` | MEDIUM | User sees wrong language badge + evaluator uses wrong prompt | EN_TO_CN question backfilled with target_language="en" instead of "zh" |
| Old JSON files lack metadata field entirely | HIGH | Fallback chain uses wrong defaults | Old Integrated Chinese question has no metadata dict; frontend assumes target_language="zh" (lucky), but backend prompt assumes target_language="en" (unlucky) |
| Inconsistent metadata keys (camelCase vs snake_case) | MEDIUM | Fallback chain picks wrong field | Metadata has `answerLanguage: "en"` but code looks for `answer_language: "en"`; frontend uses fallback default |
| Content builder outputs new metadata format, old code can't parse | LOW | New questions fail to render | New pipeline outputs `target_language_code: "zh-Hans"`, old code expects `target_language: "zh"` |

---

## Test Coverage Gaps

### Currently Tested (✓)

```
✓ test_new_concept_practice_types.py:
  - 16 question_type + metadata combinations
  - Validates prompt templates for each type
  - Checks "# Evaluation Input:" section layout
  
✓ Frontend pattern matching (implicit in PracticeSection):
  - SPEAK + metadata renders correctly
  - CN_TO_{LANG} extracts language correctly
```

### NOT Currently Tested (✗)

```
✗ Metadata fallback chain:
  - What if metadata.target_language is missing but answer_language exists?
  - Does frontend use correct fallback?
  - Does backend?
  
✗ Theme selection for all languages:
  - CN SPEAK → rose (tested)
  - EN SPEAK → teal (tested)
  - FR SPEAK → ? (not tested)
  - DE SPEAK → ? (not tested)
  
✗ Badge generation for new pairs:
  - CN_TO_EN → "翻译 · 中→英" (maybe tested)
  - FR_TO_KO → ? (definitely not tested)
  
✗ Migration idempotency:
  - Can migrate_integrated_chinese_practice_types.py re-run without breaking?
  - Does it detect already-migrated questions?
  
✗ Database constraint validation:
  - Can user insert question_type = "SPEAK_CHINESE" (typo)? Should be rejected.
  - No CHECK constraint exists in schema.
  
✗ Circular dependency in canonicalization:
  - New content builder outputs canonical types
  - But old questions still have named types
  - Frontend must support both indefinitely
  - Can't remove pattern matchers until ALL questions are migrated
```

---

## Safe Canonicalization Prerequisites

### Must Have Before Proceeding

| Prerequisite | Status | Work Required |
|---|---|---|
| Explicit `evaluator_language` metadata | ✗ Missing | Add field; backfill for all 7,500 questions |
| Audit metadata completeness | ✗ Not done | Scan DB for NULL/missing/conflicting values |
| Theme assignment rules for all 16 languages | ⚠️ Partial | Define rules for FR, DE, KO, RU, ES, PT, VI, TH, AR, IT, ID, MS SPEAK |
| i18n entries for all language pairs | ⚠️ Partial | Add translations for badge labels, prompt labels |
| Test coverage for canonicalization | ✗ Not done | Add 50+ test cases for metadata combinations |
| Database schema validation | ✗ Not done | Add CHECK constraint on question_type; add NOT NULL on metadata |

### Rollback Plan

| Situation | Rollback Strategy | Effort |
|---|---|---|
| 10% of questions have wrong metadata after migration | Re-run migration script with corrected metadata; verify correctness | LOW |
| 50% of questions fail rendering after canonicalization | Revert frontend code; keep database as-is; questions still render | LOW |
| New canonical prompt is wrong audience | Revert `backend/services/llm/prompts.py`; use old named-type prompts | MEDIUM |
| Can't remove pattern matchers (old DB questions persist) | Accept as technical debt; document why matchers exist | LOW |

---

## Recommendation Summary

### ✅ Safe to Canonicalize IF:

1. **Add explicit `evaluator_language` metadata first**
   - Otherwise, audience inference is fragile
   - Estimated work: 200 lines backend + 1 DB migration script + tests

2. **Migrate in phases**:
   - Phase 1: New content builders output canonical types (low risk)
   - Phase 2: Backend accepts canonical types (add to prompts.py; keep old types as fallback)
   - Phase 3: Frontend accepts canonical types (add to questionTypeConfig.js; keep pattern matchers)
   - Phase 4: Migrate DB using script (dry-run first; spot-check 50 questions)
   - Phase 5: Remove fallback code (1+ month after Phase 4)

3. **Comprehensive test suite**:
   - Add 50+ test cases for metadata combinations
   - Add theme selection tests for all 16 languages
   - Add badge generation tests for new language pairs
   - Add migration validation tests

4. **Document the canonical types**:
   - Create a schema spec: "TRANSLATE = {target_language, support_language, evaluator_language}"
   - Justify why audience is needed
   - Update CLAUDE.md with type definitions

### ⚠️ Risks If NOT Canonicalized:

1. Each new language pair requires hardcoding in frontend (e.g., FR_TO_KO → new config)
2. Backend prompts will keep growing (now 10 explicit prompts, eventually 30+)
3. New language pipelines must follow naming convention (e.g., {LANG}_SPEAK)
4. "What should French dictation look like?" has no documented answer

### ❌ NOT Safe to Canonicalize Without:

1. Explicit evaluator_language metadata
2. Theme rules for all language pairs
3. Database audit for metadata completeness
4. Test coverage for canonicalization scenarios

