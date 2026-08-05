# MNN: Convert Teaching Slides to WebP (q85)

## Goal

Make Minna no Nihongo teaching-slide images follow the established Integrated Chinese media strategy:

```text
Remotion PNG → Pillow WebP (quality 85, method 6) → remove local PNG → JSON references WebP
```

The result applies to normal narration decks and no-TTS captioned decks. Future MNN renders will produce `.webp` as their final image artifact, and existing locally generated MNN slide PNGs can be converted without regenerating content or TTS.

## Current state

- Integrated Chinese already uses the shared `convert_pngs_to_webp(..., quality=85)` helper in its deck builder.
- The MNN deck builder currently renders/reuses `.png` and falls back to `.svg`; its JSON asset fields therefore point to PNG.
- The shared uploader, R2 MIME mapping, media route allowlist, and frontend `<img>` rendering already support WebP, so they require no behavior change.
- MNN `--skip-tts` decks are image/caption-only (`audio_mode: "none"`); image compression must remain independent from audio mode.

## Implementation

### 1. Make Pillow a declared backend dependency

**Files:**
- `backend/requirements.txt`
- `backend/Pipfile`

Add Pillow explicitly. WebP conversion becomes a supported build requirement rather than an opportunistic optional dependency.

**Shared helper hardening:**
- Update `backend/content_builder/core/slide_asset_helpers.py` so conversion opens images with a context manager, writes the WebP first, verifies the output exists, then deletes the PNG.
- Preserve its boolean result so callers can retain PNG safely if conversion fails unexpectedly.

### 2. Add WebP-first image selection to the MNN deck builder

**File:** `backend/content_builder/ja/minna_no_nihongo/scripts/build_teaching_slide_deck.py`

- Import `convert_pngs_to_webp` from the shared helper.
- Add `_WEBP_QUALITY = 85` and a small MNN-local conversion wrapper.
- Extend image cleanup to include `(".png", ".webp", ".svg")`.
- For Remotion builds, use this deterministic image selection sequence:
  1. If all requested WebP slides already exist and not forced, reuse WebP.
  2. If all requested PNG slides exist and not forced, convert them to WebP and reuse the resulting WebP.
  3. Otherwise, ask Remotion to emit PNG, convert all rendered PNGs to WebP, then use WebP.
  4. If Remotion fails, preserve the existing SVG fallback.
- Only set the final `image_suffix` to `.webp` after confirming complete WebP output exists. If conversion unexpectedly fails, retain the valid PNG suffix rather than write dangling WebP references.
- After a successful WebP build, remove same-index stale PNG/SVG files so the final local output is WebP only. SVG remains only if the Remotion fallback is actually used.
- Continue deriving `local_path`, `object_key`, and `media_path` from `image_suffix`, so JSON automatically changes to:
  ```json
  {
    "local_path": ".../slide_001.webp",
    "object_key": "ja/slides/zh/lesson001/slide_001.webp",
    "media_path": "/media/teaching-slide/minna_no_nihongo/zh/001/slide_001.webp"
  }
  ```
- Keep no-TTS deck behavior unchanged: `audio_mode: "none"`, captions present, no per-slide audio. It will simply use WebP images.

### 3. Cover existing local MNN assets

No separate conversion program is necessary. After the builder change, the existing Stage 2 command scans the generated MNN JSON and upgrades all locally complete PNG decks in-place without calling TTS:

```powershell
& .\.venv\Scripts\python.exe `
  backend\content_builder\ja\minna_no_nihongo\scripts\render_narration.py `
  --pipeline minna_no_nihongo `
  --lang zh `
  --skip-tts `
  --force-slides
```

This will:

- render any missing slides as needed;
- convert all generated MNN slide PNGs to q85 WebP;
- delete their local PNG originals after successful conversion;
- update `teaching_slide_deck` in each local output JSON;
- preserve caption-only/no-TTS semantics.

It will not upload R2 assets or modify the database.

### 4. Preserve R2 and frontend compatibility

No code change is needed for:

- `backend/database/sync_to_db.py`: already maps `.webp` to `image/webp`;
- `backend/database/sync_to_db_ja.py`: uses the common uploader;
- `backend/main.py`: already permits and serves `.webp` teaching-slide paths;
- `frontend/src/pages/studyPage/teaching/components/LessonSlideDeckPlayer.jsx`: `<img>` consumes the JSON asset path independently of image extension.

Existing remote PNG objects are not automatically deleted by sync. A later sync uploads WebP and updates DB JSON references, leaving old PNG objects unreferenced. Remote deletion remains deliberately separate from this change.

## Tests

### Shared helper tests

**File:** `backend/tests/test_stage2_helpers.py`

- Create a real small PNG with Pillow; convert it at q85; assert WebP exists, has WebP format, and original PNG is removed.
- Confirm failed/unavailable conversion does not cause callers to target a nonexistent WebP.
- Verify stale cleanup handles `.png`, `.webp`, and `.svg` safely.

### MNN deck tests

**File:** `backend/tests/test_mnn_no_tts_slides.py`

- Existing complete PNG deck converts to WebP without invoking Remotion.
- Newly rendered Remotion PNG is converted, removed, and produces WebP JSON asset paths.
- Existing complete WebP deck is reused without invoking Remotion or the converter.
- No-TTS deck retains `audio_mode: "none"` and non-empty captions while using WebP.
- SVG fallback remains SVG if Remotion itself fails.

### Media route regression

**File:** `backend/tests/test_media_artifact_routes.py`

- Add a local MNN `slide_001.webp` media route test asserting a 200 response and `image/webp` content type.
- Retain PNG/SVG tests for legacy compatibility.

## Verification

1. Run focused tests and the MNN regression suite.
2. Run frontend production build.
3. Convert the currently generated local MNN deck artifacts with the no-TTS Stage 2 command above.
4. Inspect an output directory such as:
   ```text
   backend/content_builder/ja/minna_no_nihongo/artifacts/output_slides/zh/lesson001/
   ```
   Expected: `.webp` slides; no matching `.png` originals.
5. Open the local teaching preview and verify image rendering/captions:
   ```text
   http://localhost:5173/dev/teaching-preview?pipeline=minna_no_nihongo&lang=zh&lesson=001
   ```

## Boundaries

- This change compresses teaching-slide raster images only; it does not affect lesson sentence audio, narration audio, or captions.
- SVG remains an intentional fallback only when Remotion cannot render a raster slide.
- Remote historical PNG/SVG cleanup is excluded: normal sync is non-destructive and must not silently delete R2 objects.
