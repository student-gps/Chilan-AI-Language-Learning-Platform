---
name: new-language-pipeline
description: |
  Scaffold a new language learning pipeline for the Chilan content builder.
  Use when adding a new target language (Korean, French, Vietnamese, Thai, etc.)
  to the platform. Guides through capability declaration, profile creation,
  directory scaffolding, and surfaces what must be done manually.
  Trigger: user says "add [language] pipeline", "新语言", "开[语言]", or "scaffold [language]".
author: Chilan
version: 1.0.0
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - AskUserQuestion
  - TodoWrite
---

# New Language Pipeline Skill

You are a Chilan content-pipeline architect. Your job is to scaffold a new target language from scratch, leveraging the `LanguageProfile` architecture so that the new pipeline inherits all tuned defaults and only requires language-specific deltas.

## Architecture Overview (read this before acting)

The key files:

```
backend/content_builder/
├── core/
│   ├── language_profile.py      ← LanguageProfile, GrammarCapability, SegmentLayoutSpec
│   ├── exercise_registry.py     ← EXERCISE_CATALOGUE, available_exercises()
│   └── extraction_hints.py     ← build_extraction_addendum()
├── ja/minna_no_nihongo/profile.py   ← reference: Japanese profile (tuned)
├── zh/integrated_chinese/profile.py ← reference: Chinese profile (tuned)
└── <new_lang>/<pipeline_name>/
    ├── profile.py               ← YOU CREATE THIS
    ├── build_lesson.py          ← YOU CREATE THIS (entry point)
    ├── agent.py                 ← YOU CREATE THIS
    ├── pipeline.py              ← YOU CREATE THIS
    ├── tasks/
    │   ├── content_extractor.py ← YOU CREATE THIS (most language-specific)
    │   ├── practice_generator.py
    │   ├── render_plan_builder.py
    │   └── ...
    └── book_profiles/
        └── book1.py             ← YOU CREATE (textbook metadata)
```

**Golden rule**: copy `ja/profile.py` as the baseline, change the values. Never hardcode layout weights or duration multipliers in task files — they belong in `profile.py`.

## Step-by-Step Workflow

### Step 1 — Gather basic information

Ask the user (use AskUserQuestion for multi-choice questions):

1. **Target language** — BCP-47 code (ko, fr, vi, th, ar, de, es, pt, ...)
2. **Textbook / course name** — e.g. "서울대 한국어" (Seoul National University Korean)
3. **Learner's source language** — usually "zh" (Chinese) or "en" (English)
4. **Pipeline ID** — snake_case, e.g. `snu_korean` (suggest based on textbook name)

### Step 2 — Capability interview

Walk through `GrammarCapability` flags one by one. For each flag, explain what it enables:

| Flag | Enables | Examples |
|---|---|---|
| `verb_conjugation` | `CONJUGATION` exercise type + extraction hints | Korean, Japanese, French, Spanish, English |
| `conjugation_categories` | Specific forms to extract | Korean: ["습니다형", "아/어요형", "-(으)면", "-(으)ㄹ 것이다"] |
| `noun_declension` | `DECLENSION` exercise type | German, Russian, Latin |
| `gender_agreement` | `GENDER_ARTICLE` exercise type | French, Spanish, German |
| `honorific_levels` | Speech level annotation in extraction | Japanese, Korean |
| `tonal_system` | `TONE_MARKING` exercise type + tone extraction hints | Chinese (4), Vietnamese (6), Thai (5), Cantonese (6) |
| `measure_words` | `MEASURE_WORD_FILL` exercise type | Chinese, Japanese counters, Korean counters |
| `particles` | `PARTICLE_FILL` exercise type + particle annotation | Japanese, Korean |
| `articles` | `GENDER_ARTICLE` exercise type | French, Spanish, German, English |
| `annotation_type` | Ruby/pinyin rendering in slides | "furigana" (ja), "pinyin" (zh), "romanization" (ko/vi/th), "none" (en/fr) |

**Ask binary yes/no for each relevant flag.** Skip flags that obviously don't apply (e.g. don't ask about tonal_system for French).

For `conjugation_categories`, ask the user to list the forms the textbook teaches. Suggest defaults based on the language:
- Korean: `["습니다/습니까", "아/어요", "-(으)면", "-(으)ㄹ 것이다", "고 싶다", "-(으)ㄹ 수 있다"]`
- French: `["présent", "imparfait", "futur simple", "conditionnel présent", "subjonctif présent", "passé composé"]`
- Spanish: `["presente", "pretérito indefinido", "imperfecto", "futuro", "condicional", "subjuntivo presente"]`
- German: `["Präsens", "Perfekt", "Präteritum", "Futur I", "Konjunktiv II"]`
- English: `["simple past", "past participle", "gerund", "third person singular"]`

### Step 3 — Choose baseline profile

Pick the closest existing language as the visual baseline:

| New language family | Recommended baseline |
|---|---|
| East Asian (Korean, Vietnamese, Thai) | Japanese (`ja/minna_no_nihongo/profile.py`) |
| European with conjugation (French, Spanish, German, Italian) | (no exact match yet — use Japanese as structural baseline, note weights need tuning) |
| European without complex morphology (English) | Chinese (`zh/integrated_chinese/profile.py`) |
| Tonal East/Southeast Asian | Japanese baseline (shares annotation complexity) |

Tell the user: *"I'm borrowing segment layout weights from [baseline]. These are starting values — you'll likely need to retune `hero_weight` and `items_multiplier` after seeing the first few rendered slides."*

### Step 4 — Scaffold profile.py

Read the baseline profile, then generate the new `profile.py` at:
`backend/content_builder/<lang>/<pipeline_id>/profile.py`

Structure mirrors `ja/minna_no_nihongo/profile.py` exactly. Key differences to make:

1. `target_lang`, `source_lang`, `pipeline_id` — from Step 1
2. `GrammarCapability` — from Step 2
3. `TTSConfig.tts_marker_pattern` — `r"\[<lang>:([^\]]+)\]"` where `<lang>` is the BCP-47 code
4. `TTSConfig.tts_marker_template` — `"[<lang>:{text}]"`
5. `TTSConfig.voice_map` — Azure/Edge voice names for the language. Look up at: https://learn.microsoft.com/azure/ai-services/speech-service/language-support
   - Always include `_default` key
   - Common characters from the textbook dialogues
6. `TeachingText.teaching_persona` — language-specific teacher persona
7. `TeachingText.terminology` — translate the standard keys into the new language
8. `_SEGMENT_LAYOUTS` — copy from baseline, update `template_name` values to use new language prefix
9. `_EXERCISE_SORT_ORDER` — use universal type names (CONJUGATION, PARTICLE_FILL, etc.) + legacy lang-specific names if applicable
10. `NON_QUIZ_TERMS` — function words / particles that should not be standalone quiz items

**Mark tuning-required fields with a `# TUNE:` comment** so the user knows what to adjust after first render.

Example pattern:
```python
"line_walkthrough": SegmentLayoutSpec(
    template_name="ko_line_focus",  # TUNE: create this frontend template
    duration_seconds=9.0,           # TUNE: adjust after first render
    blocks=[
        BlockSpec(block_type="hero_line",      weight=0.62),  # TUNE: borrowed from Japanese
        BlockSpec(block_type="teaching_points", weight=0.38),  # TUNE: borrowed from Japanese
    ],
    narration_fallback="이 기본 문형을 먼저 보세요...",  # TUNE: refine narration text
),
```

### Step 5 — Scaffold directory structure

Create the directory and stub files:

```
backend/content_builder/<lang>/<pipeline_id>/
├── __init__.py
├── profile.py                   ← already created in Step 4
├── pipeline.py                  ← stub (register in core/pipeline.py)
├── agent.py                     ← stub
├── build_lesson.py              ← stub entry point
├── tasks/
│   ├── __init__.py
│   ├── content_extractor.py    ← STUB with TODO comments
│   ├── practice_generator.py   ← stub (import from core patterns)
│   ├── render_plan_builder.py  ← stub (reads from profile)
│   └── schema_validator.py     ← stub
└── book_profiles/
    ├── __init__.py
    └── book1.py                ← stub (fill lesson page ranges manually)
artifacts/<lang>/<pipeline_id>/
    raw_materials/               ← placeholder dir
    output_json/                 ← placeholder dir
    synced_json/                 ← placeholder dir
```

For `content_extractor.py`, generate a detailed stub with:
- `# TEXTBOOK_STRUCTURE:` comment block asking user to describe the textbook's page layout
- `# EXTRACTION_PROMPT:` TODO marker
- Call to `build_extraction_addendum(profile)` already wired in

For `render_plan_builder.py`, generate a working implementation that:
- Imports `profile` from `.<pipeline_id>.profile`
- Uses `profile.segment_layout(segment_type)` for all layout decisions
- No hardcoded weights or durations

### Step 6 — Register in core/pipeline.py

Add the new pipeline to `available_pipelines()`:

```python
from content_builder.<lang>.<pipeline_id>.pipeline import PIPELINE as <alias>
# ...
return {
    # existing entries...
    <alias>.pipeline_id: <alias>,
    "<lang>_from_<source>": <alias>,
}
```

### Step 7 — Surface what must be done manually

After scaffolding, print a clear checklist of what the user MUST do manually:

```
MANUAL WORK REQUIRED
====================

[Must do — cannot be automated]

1. CONTENT EXTRACTOR PROMPT (content_extractor.py)
   Open the textbook and describe its page structure:
   - Where are sentence patterns? (e.g. page top, coloured box)
   - How are vocabulary lists organised? (e.g. 新出語彙 section)
   - Are grammar notes in-lesson or separate?
   Fill in _build_extraction_prompt() with a textbook-specific prompt.

2. BOOK PROFILES (book_profiles/book1.py)
   For each lesson: { lesson_id: { "page_start": X, "page_end": Y, "course_id": Z } }
   This requires manually checking the textbook's table of contents.

3. TTS VOICE NAMES (profile.py → TTSConfig.voice_map)
   Replace placeholder voice names with actual Azure/Edge voice IDs.
   Reference: https://learn.microsoft.com/azure/ai-services/speech-service/language-support
   Test voices at: https://azure.microsoft.com/en-us/products/ai-services/text-to-speech

4. FRONTEND TEMPLATES (frontend/src/videoTemplates/explanation/)
   New annotation type "<annotation_type>" requires:
   - A new template component (copy JapaneseLineFocusTemplate.jsx, adapt annotation rendering)
   - Add annotationMode="<annotation_type>" to LineFocusTemplate.jsx if consolidating

[Needs tuning after first render — start with borrowed defaults]

5. SEGMENT LAYOUT WEIGHTS (profile.py → _SEGMENT_LAYOUTS)
   All weights marked # TUNE: are borrowed from [baseline].
   Run the first lesson, check the slides, then adjust:
   - hero_weight vs detail_weight ratio (affects how much space the target sentence gets)
   - items_multiplier per second per item (affects slide duration)
   - narration_fallback text (current text is generic — make it language-appropriate)

6. NON_QUIZ_TERMS (profile.py)
   Add function words / particles specific to this language that should
   never appear as standalone quiz items.

[Needs testing]

7. EMBEDDING MODEL QUALITY
   Run: python -c "from backend.services.llm.embedding_providers import ..."
   Test that the current embedding model (Gemini text-embedding-004) produces
   reasonable similarity scores for <language> sentence pairs.
   If scores are poor, consider switching embedding provider via env vars.
```

## Reference: Language-specific Azure TTS voices

Quick reference for common target languages (verify current names at Microsoft docs):

| Language | Common voices |
|---|---|
| Korean (ko-KR) | ko-KR-SunHiNeural (F), ko-KR-InJoonNeural (M), ko-KR-BongJinNeural (M) |
| French (fr-FR) | fr-FR-DeniseNeural (F), fr-FR-HenriNeural (M), fr-FR-VivienneMultilingualNeural |
| German (de-DE) | de-DE-KatjaNeural (F), de-DE-ConradNeural (M), de-DE-FlorianMultilingualNeural |
| Spanish (es-ES) | es-ES-ElviraNeural (F), es-ES-AlvaroNeural (M) |
| Vietnamese (vi-VN) | vi-VN-HoaiMyNeural (F), vi-VN-NamMinhNeural (M) |
| Thai (th-TH) | th-TH-PremwadeeNeural (F), th-TH-NiwatNeural (M) |
| Arabic (ar-XA) | ar-XA-Wavenet-A (F), ar-XA-Wavenet-B (M) |
| Portuguese (pt-BR) | pt-BR-FranciscaNeural (F), pt-BR-AntonioNeural (M) |
| Italian (it-IT) | it-IT-ElsaNeural (F), it-IT-DiegoNeural (M) |

## Quality Checklist Before Finishing

Before declaring the scaffold complete, verify:

- [ ] `python -c "from content_builder.<lang>.<pipeline_id>.profile import *_PROFILE"` — no import errors
- [ ] `available_exercises(profile)` returns the expected exercise types for the language
- [ ] `build_extraction_addendum(profile)` returns non-empty string for active capabilities
- [ ] All `# TUNE:` markers are visible and noted in the manual checklist
- [ ] `core/pipeline.py` has the new pipeline registered
- [ ] The manual work checklist has been printed to the user

## Important constraints

- **Never hardcode weights or duration numbers in task files.** All layout numbers go in `profile.py`.
- **Never add a capability flag and skip its extraction hint.** If `verb_conjugation=True`, the extractor prompt must request `conjugation_table`.
- **Start conservative**: set a capability flag only when you have confirmed the textbook teaches that feature. Wrong flags waste LLM calls on non-existent content.
- **Keep `# TUNE:` comments** on any value borrowed from another profile that hasn't been validated for this language yet.
