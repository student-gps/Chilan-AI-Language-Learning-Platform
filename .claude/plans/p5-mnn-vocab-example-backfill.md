# MNN: Reliable Vocabulary Example Backfill

## Goal

Fix Japanese MNN vocabulary example backfill before the user regenerates lessons 1–74. The pipeline must fill examples from the current lesson only when a real, source-addressable lesson sentence is valid for the vocabulary item; it must preserve provenance and never invent example text. It must also keep empty examples out of global vocabulary memory and eliminate duplicate example cards in vocabulary practice questions.

The user accepts higher LLM cost/effort for uncertain matches. The implementation will therefore use deterministic matching first and a restricted two-pass LLM decision only for unresolved terms. The LLM may select a pre-supplied candidate reference or reject all candidates; it cannot write a sentence.

## Current fault

`MinnaNoNihongoVocabMemory._find_example_for_vocab()` uses raw substring matching. Japanese textbook spacing, `〜` variants, and light fixed-expression variants cause real lesson sentences to be missed. Empty examples then enter `global_vocab_memory.json` and later deprive repeated vocabulary of historical examples. At the practice layer, current/historical examples are deduplicated by full dictionary equality rather than learner-visible content.

## Implementation plan

### 1. Introduce a provenance-safe example resolver

**Update:** `backend/content_builder/ja/minna_no_nihongo/tasks/vocab_memory.py`

- Keep candidate sentences restricted to current lesson `sentence_patterns`, `example_sentences`, and `dialogue.lines`. Do not generate or use text from external lessons.
- Add Japanese matching normalization that:
  - uses Unicode NFKC;
  - removes all Unicode whitespace;
  - normalizes `〜`, `～`, and `~` to one marker;
  - removes only presentation/optional brackets where safe;
  - preserves meaningful particles and lexical characters.
- Resolve in stages:
  1. exact raw substring → `match_method: "direct"`;
  2. normalized substring (including space/tilde variants) → `match_method: "normalized"`;
  3. unresolved terms receive a bounded candidate shortlist from the current lesson, ranked by Japanese character overlap/sequence similarity.
- Add `backfill_examples(..., llm_provider, reviewer_provider)` to process unresolved vocabulary in batches. Selection prompt only permits `candidate_id` (a supplied `source_section:source_ref`) or `null`; it forbids generated text.
- Require an independent review response for every selected LLM candidate. Review prompt sees the term, reading, Chinese definition, and selected real candidate, and returns approve/reject only. Rejected/invalid/low-confidence selections remain unfilled.
- Prefer `LLMFactory.create_fallback_provider()` as reviewer when configured through `LLM_CONTENT_GEMINI_FALLBACK_MODEL_ID`; otherwise use the primary provider for a second independent call. This is the high-effort path. Record match counts, unresolved count, selector/reviewer provider names, and rejected count in `pipeline_diagnostics.vocab_memory`.
- Rehydrate examples from the canonical in-memory source table after selection so stored `text`, reading, translation, section, and reference are always lesson-owned. Add `match_method` to the stored example record.

### 2. Do not persist empty historical evidence

**Update:** `backend/content_builder/ja/minna_no_nihongo/tasks/vocab_memory.py`

- In `save_lesson_vocabulary()`, attach `example` only when it has non-empty text.
- Update `_compact_usages()` so it preserves usage metadata but omits `example` for empty/malformed entries.
- Continue deriving `historical_examples` only from valid non-empty examples.
- Add diagnostics that distinguish vocabularies with a valid current example from intentionally unresolved/source-less terms.

The user will delete the existing nine output lessons and global memory; therefore no migration of existing empty memory entries is necessary.

### 3. Remove user-visible duplicate example contexts

**Update:** `backend/content_builder/ja/minna_no_nihongo/tasks/practice_generator.py`

- In `_context_examples_for_vocab()`, deduplicate examples using normalized learner-visible `(text, reading, translation)` values, ignoring provenance and other internal keys.
- Keep current-lesson context first, then distinct historical contexts, capped at two.

### 4. Wire high-effort providers through the Stage 1 agent

**Update:**
- `backend/content_builder/ja/minna_no_nihongo/agent.py`
- `backend/content_builder/ja/minna_no_nihongo/build_lesson.py`

- Create an optional fallback/reviewer provider once per build process.
- Pass the main provider and reviewer provider into the vocabulary-memory annotation step after reading/token auditing and before practice generation.
- Merge reviewer usage reporting into lesson diagnostics/usage reporting so the extra LLM work is visible.
- Placeholder/no-provider runs retain deterministic matching only and do not fail.

### 5. Add regression tests

**Extend:** `backend/tests/test_minna_no_nihongo_pipeline.py`

Cover:

1. direct match preserves a real source reference and `match_method: direct`;
2. full-width/half-width spacing match, e.g. `おはようございます` → `おはよう　ございます。`;
3. tilde pattern normalization, e.g. `〜さん` can choose a real `…さん…` candidate only through the controlled path;
4. LLM selection can only resolve an existing candidate ID; invalid IDs or generated text are rejected;
5. a reviewer rejection leaves the vocabulary example blank;
6. memory saves no empty `example` record, while still saving lesson/meaning usage metadata;
7. next-lesson historical example round-trip retains a real source example;
8. current and historical user-visible duplicate examples produce one `context_examples` entry;
9. distinct current/historical examples both remain and current comes first.

## Regeneration contract

After code verification, the user can delete the current output JSON/slides and `artifacts/vocab_memory/global_vocab_memory.json`, then rerun:

```powershell
& .\.venv\Scripts\python.exe `
  backend\content_builder\ja\minna_no_nihongo\run_mnn_rebuild.py `
  --all --skip-tts --force --stop-on-error
```

The full rebuild will construct memory incrementally from lessons 1 → 74. No old empty examples will influence historical backfill.

## Deliberate safety boundary

No free-form LLM sentence generation will be accepted. Every stored example must be rehydrated by a valid `(source_section, source_ref)` from the current lesson sentence pool; otherwise the item deliberately remains without an example.
