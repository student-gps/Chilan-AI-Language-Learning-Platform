# Teaching slide player: fullscreen caption visibility

## Goal

Ensure the caption panel below the teaching slide stays visible when the learner uses either player enlargement control:

- native browser fullscreen (`Maximize2`), and
- in-page expanded mode (`Scan`).

The change is limited to the teaching-slide player. It will not alter generated slide artwork, narration assets, or existing caption-cue data.

## Findings

- The visible lower caption is rendered by `LessonSlideDeckPlayer` from each slide's `caption_cues`.
- In native fullscreen, the player sizes its 16:9 image from a width limit, then appends the timeline/control/caption block. The total card height therefore exceeds the viewport. Its `max-height` plus `overflow-hidden` crops the lower content.
- In in-page expanded mode, the width limit similarly accounts for the 16:9 image only and not the controls or fixed navigation height. After scrolling the player below the navigation bar, the caption panel begins below the viewport.

## Implementation

### 1. Make expanded-player sizing account for controls

In `frontend/src/pages/studyPage/teaching/components/LessonSlideDeckPlayer.jsx`:

- Add refs for the deck card and the control/caption section.
- Measure the actual control section height rather than relying on a fragile fixed-pixel estimate. The measurement will naturally handle controls wrapping on narrower windows.
- While either enlargement mode is active, calculate the largest 16:9 slide width that fits the remaining visible height **after** the control section:
  - native fullscreen: viewport height minus fullscreen padding;
  - in-page expanded: viewport height below the current deck top (which is positioned beneath the fixed navbar) minus a small visual margin.
- Apply the smaller of that height-derived limit and the existing responsive width limit. Leave the normal, non-expanded player sizing unchanged.
- Recalculate after fullscreen transitions, expansion changes, window resizes, and control-section size changes (via `ResizeObserver`) so caption visibility remains correct across window sizes and responsive control wrapping.

### 2. Preserve the intended visual layout without clipping

- Give the image stage and control/caption section explicit player classes/refs so the stage remains 16:9 and controls retain their current layout.
- Remove/replace the fullscreen card height rule that clips content; the new fitted dimensions will make the *whole* card fit instead.
- Preserve current image `object-contain`, timeline behavior, keyboard-independent buttons, audio playback, cue animation, and fullscreen toggle state.

### 3. Validate

- Run the frontend lint command from the frontend package directory if the package manifest is available.
- Manually verify an audio-backed slide deck in both modes:
  1. open native fullscreen and confirm the cue-caption panel is completely visible while playback advances;
  2. use in-page expand and confirm the caption panel is visible below the fixed navigation bar;
  3. resize to a short/narrow desktop viewport and confirm wrapped controls do not crop captions.
- Also check a no-audio captioned deck: it should continue showing its first `caption_cue` while the bottom control strip remains fully visible.

## Files

- Modify: `frontend/src/pages/studyPage/teaching/components/LessonSlideDeckPlayer.jsx`
- No backend, generated media, or unrelated modified files will be changed.
