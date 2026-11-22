# Minna no Nihongo Pipeline Standards

This pipeline is still in test iteration. Prefer correcting the generator and rerunning artifacts over preserving compatibility with older JSON or slide outputs.

## Reading And Ruby

- Japanese reading annotations are data, not presentation guesses.
- Stage 1 owns sentence-level `reading` and token-level `tokens` for every Japanese line used by teaching slides.
- This includes:
  - `course_content.sentence_patterns`
  - `course_content.example_sentences`
  - `course_content.dialogue.lines`
  - `course_content.grammar_sections[].patterns`
  - `course_content.grammar_sections[].examples`
- Render plans must pass tokens through to slide templates whenever Japanese text can display ruby.
- Frontend templates may hide or style ruby, but should not infer broad whole-line readings from raw sentence reading.
- If tokenization is uncertain, prefer no ruby over wrong whole-line ruby.

## LLM Role

- LLMs may create or repair readings/tokens during Stage 1.
- The preferred flow is deterministic tokenization first, then LLM audit/repair only for risky cases.
- LLM output should be written back into JSON before Stage 2. Stage 2 should render from finalized JSON.

## Teaching Coverage

- The explanation director may decide grouping, order, titles, and narration, but it must not silently drop textbook modules.
- Lessons should open on the first real teaching page. A brief natural greeting is fine when it immediately leads into the first pattern or sentence, but do not create standalone objective, overview, or "what we will learn" slides.
- `sentence_patterns` should be covered one by one with `line_walkthrough` pages.
- `example_sentences` and `dialogue.lines` should be covered in textbook order, grouped into readable pages rather than sampled down to a few representative lines.
- `grammar_sections` should all be covered. Closely related adjacent sections may share a page, but independent grammar points should not disappear.
- Learnable vocabulary is split into:
  - `core_vocabulary`: main-text vocabulary used by patterns, examples, and dialogue.
  - `supplementary_vocabulary`: practice and extension vocabulary.
- Both `core_vocabulary` and `supplementary_vocabulary` must be taught in vocabulary slides and remain reviewable.
- `display_only_vocabulary` is for proper nouns and temporary reference terms. It should be shown briefly for recognition, not treated as quiz/review vocabulary.
- If an LLM-directed plan omits required coverage, the composer should add deterministic pages before recap rather than silently shipping a partial lesson.
- Vocabulary narration should feel like a teacher walking through the words, not a repeated template. When a group has a natural relation, such as shared scene, suffix, word family, question function, or review status, mention it briefly. When no relation is obvious, clear word-by-word explanation is fine.
- Context links between pages should be opportunistic, not forced. Use them only when the connection is real, such as moving from people to jobs, demonstratives to objects, or core text to practice substitutions.
- Repeated foundation reminders should be lightweight. Once `は` as topic particle, `です`, or sentence-final `か` has been taught, later lessons should treat them as review context rather than re-explaining them in full.
- Line-focus visual highlights should prioritize lesson-specific words and new grammar focus. Foundation items such as `は` and `です` should not repeatedly occupy highlight cards when two or more more-specific highlights are available.

## Narration TTS

- Mixed Chinese/Japanese narration should use single SSML requests with voice spans when Azure is available, so Chinese explanation and Japanese examples flow naturally.
- One-kana Japanese teaching snippets, such as `[ja:は]` and `[ja:わ]`, should be pronounced with a long-vowel teaching style: `はー`, `わー`.
- Do not repeat one-kana snippets as `は、は` or `わ、わ`; that sounded less natural and made the explanation feel choppy.
- Keep the short snippet slightly slower and louder than surrounding speech so the learner can hear the particle clearly.

## Artifact Policy

- During test iteration, generated lesson JSON, narration metadata, and slide images may be regenerated.
- Do not add frontend compatibility hacks solely for stale artifacts.
- If a slide reveals a systemic issue, fix Stage 1, render-plan construction, or the shared template, then rerun affected lessons.
