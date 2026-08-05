# MNN: Render Captioned Slides Without TTS

## Goal

Support a full Japanese lesson rebuild that intentionally skips **all** TTS generation while still producing normal static teaching slides and explanation captions for lessons 1–74. The resulting deck must contain usable images and non-empty caption data, but must never create, reference, upload, or try to play narration/slide audio.

The intended one-command workflow will be:

```powershell
python backend\content_builder\ja\minna_no_nihongo\run_mnn_rebuild.py --all --skip-tts --force
```

It will rebuild Stage 1 and static Stage 2 slides for lessons 1–74, using course 303 and Chinese learner support by default. It will not sync to DB/R2; publishing with the existing audio-required publish command remains intentionally separate.

## Current behavior and gap

- `build_lesson.py --lesson-audio-metadata-only` prevents the Stage-1 Japanese sentence TTS, but it does not run Stage 2.
- `render_narration.py` always invokes narration TTS and refuses to build a slide deck unless narration status is `ok`.
- `build_teaching_slide_deck.py` can render slide images without narration, but still calls ffmpeg splitting and writes dangling per-slide audio references.
- Remotion static slide exports explicitly disable `SubtitleBar`, so PNG slides lack the explanation subtitle even when the render plan includes it.
- The slide player assumes every deck has audio controls and playback timing.

## Implementation plan

### 1. Add a no-TTS Stage 2 mode

**Update:** `backend/content_builder/ja/minna_no_nihongo/scripts/render_narration.py`

- Add `--skip-tts`, mutually exclusive with `--force-narration`.
- In this mode, do not create/reuse/delete narration MP3s and do not call `agent.render_narration()`.
- Normalize the existing Stage-1 explanation timeline, validate that every render-plan segment has learner-language narration text (`subtitle_<lang>` → `script` → `subtitle_zh` → `subtitle_en`), and write:
  ```json
  "explanation_narration_audio": {
    "status": "skipped",
    "reason": "tts_disabled"
  }
  ```
- Call `build_deck(..., include_audio=False)` so slides are rendered and captions are persisted despite no narration audio.
- Preserve the default TTS path unchanged.

### 2. Make the deck builder explicitly audio-optional

**Update:** `backend/content_builder/ja/minna_no_nihongo/scripts/build_teaching_slide_deck.py`

- Add `include_audio: bool = True` to `build_deck()` and CLI flag `--without-audio`.
- When `include_audio=False`:
  - do not resolve a narration file;
  - do not call ffmpeg or `_split_narration_audio()`;
  - write `teaching_slide_deck.audio_mode = "none"`;
  - omit every `slides[*].audio` object, rather than writing missing file paths/object keys;
  - build `caption_cues` directly from the current render-plan narration text, using deterministic equal-duration cue timing and ignoring stale TTS sentence timings/text;
  - require at least one non-empty caption cue per slide and fail clearly if the Stage-1 render plan is incomplete;
  - remove obsolete per-slide narration MP3 files for the lesson so a previous TTS run cannot be silently reused.
- Keep the existing audio deck schema and ffmpeg behavior for normal TTS runs, but mark it `audio_mode = "per_slide"`.

**Update:** `backend/content_builder/core/slide_asset_helpers.py`

- Extend stale-asset cleanup with an explicit no-audio mode that removes all `lessonNNN_slide_*.mp3` files for the current lesson/language rather than retaining audio for current slide indexes.

### 3. Render subtitles into static slide images

**Update:** `frontend/scripts/render-explanation-slides.mjs`

- For static MNN slide export, pass `showSubtitleBar: true` to the generated Remotion composition.
- Normalize each segment’s preferred narration text before handing the render plan to Remotion, using the same language priority as the backend deck captions, so PNG subtitle content and `caption_cues` agree.
- Continue rendering one still per segment; without TTS timing, the rendered still will show the initial narration subtitle for that slide, while the deck JSON retains all sentence-level caption cues.

### 4. Make the browser deck usable without audio

**Update:** `frontend/src/pages/studyPage/teaching/components/LessonSlideDeckPlayer.jsx`

- Detect `deck.audio_mode === "none"`.
- Retain slide images, navigation, full-screen controls, and the caption panel.
- Hide narration-specific controls and behavior: play/pause, playback rate, audio preloading, audio progress timer, and audio seek behavior.
- In no-audio mode show a stable caption derived from the slide’s `caption_cues` (the first cue at initial display), so the explanation remains visible in the teaching page even outside the image.
- Keep the existing per-slide audio behavior untouched for `audio_mode = "per_slide"` or legacy decks without the field.

### 5. Add one simple CLI entry point and batch support

**Update:** `backend/content_builder/ja/minna_no_nihongo/scripts/run_stage1_stage2_batch.py`

- Add `--course-id` and `--skip-tts`.
- `--skip-tts` appends `--lesson-audio-metadata-only` to every Stage-1 build command and `--skip-tts` to every Stage-2 command.
- Preserve the normal batch TTS path when the flag is absent.

**New file:** `backend/content_builder/ja/minna_no_nihongo/run_mnn_rebuild.py`

- Provide the user-facing, minimal runner:
  ```powershell
  python backend\content_builder\ja\minna_no_nihongo\run_mnn_rebuild.py --all --skip-tts --force
  ```
- Support `--all` (defaults to 1–74), optional `--start`/`--end`, `--lang` (default `zh`), `--course-id` (default `303`), `--force`, `--skip-tts`, and `--stop-on-error`.
- Delegate to the batch runner so output logging and per-lesson failure reporting remain centralized.
- Do not add DB/R2 sync flags: rebuilding/publishing remain deliberate separate operations.

### 6. Verification

**New backend test:** `backend/tests/test_mnn_no_tts_slides.py`

Using temporary artifacts and SVG rendering (no Node/Remotion dependency):

- `build_deck(include_audio=False)` produces a deck with `audio_mode: "none"`, images, and non-empty captions for every slide.
- It writes no `slides[*].audio` data, invokes no audio splitter, and deletes old per-slide MP3s.
- It fails on a segment that has no narration text.
- Default `include_audio=True` remains compatible with the current deck audio shape.

**Extend/add focused CLI tests:**

- Assert batch `--skip-tts` forwards both no-TTS flags and forwards `--course-id`.
- Assert the convenience runner expands `--all` to the 1–74 range and preserves user flags.
- Assert `render_narration.py --skip-tts` does not call the narrator and persists a skipped narration status plus a no-audio deck.

**Frontend verification:**

```powershell
cd frontend
npm run lint
npm run build
```

Run a single no-TTS MNN slide render smoke test after implementation, then inspect the generated PNG and JSON to confirm:

- each PNG contains a subtitle bar;
- every deck slide includes non-empty `caption_cues`;
- deck `audio_mode` is `none` and no slide contains `audio`.

## Resulting commands

After implementation:

```powershell
# Full 1–74 content + captioned static slides, with no Japanese or narration TTS.
python backend\content_builder\ja\minna_no_nihongo\run_mnn_rebuild.py --all --skip-tts --force

# Optional split runs.
python backend\content_builder\ja\minna_no_nihongo\run_mnn_rebuild.py --start 1 --end 50 --skip-tts --force
python backend\content_builder\ja\minna_no_nihongo\run_mnn_rebuild.py --start 51 --end 74 --skip-tts --force
```

## Deliberate boundaries

- This mode creates no lesson sentence MP3, no explanation narration MP3, and no per-slide MP3.
- It does not invoke the current `run_publish_pipeline.py`, whose validation intentionally requires complete audio.
- It does not upload to R2 or sync to DB automatically. Those are outward-facing/data-modifying steps and should be run only after checking the newly rebuilt JSON and slide artifacts.
