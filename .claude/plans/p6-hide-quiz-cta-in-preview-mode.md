# Hide Quiz CTA in Lesson Preview Mode

## Goal
Ensure a URL entered from a course lesson preview (`?lesson_id=…&browse=1`) is read-only teaching content. It must not render a **Finish Lesson & Start Quiz** CTA or expose an interactive transition into the practice flow, even when the learner is enrolled in the course.

## Root cause
[StudyPage](../../frontend/src/pages/studyPage/index.jsx) correctly identifies `browse=1`, but it currently passes only enrollment-derived `can_practice` to the teaching view. For an enrolled learner, that capability is `true`, so [TeachingSection](../../frontend/src/pages/studyPage/teaching/index.jsx) renders the quiz CTA. Preview is a navigation mode, not an enrollment state, so enrollment cannot be used as the visibility condition by itself.

## Implementation
1. In [StudyPage](../../frontend/src/pages/studyPage/index.jsx), use `isBrowseEntry` as an explicit preview-mode constraint when rendering teaching components:
   - prevent a preview from invoking the start-practice callback as a defensive guard;
   - pass a preview-mode prop to both teaching implementations; and
   - make the normal teaching CTA available only when the learner is enrolled **and** the route is not browse mode.
2. In [TeachingSection](../../frontend/src/pages/studyPage/teaching/index.jsx), consume the preview-mode prop in the CTA condition so `browse=1` always suppresses **Finish Lesson & Start Quiz**, independent of returned practice data or enrollment capability.
3. In [NewConceptTeachingSection](../../frontend/src/pages/studyPage/english/NewConceptTeachingSection.jsx), apply the same preview-mode gate to its equivalent CTA, preserving the existing direct-lesson behavior while covering the alternate teaching renderer.
4. Run the frontend linter and production build. Manually verify the two intended paths:
   - an enrolled learner opening a course lesson with `browse=1` sees teaching content and the Back to Course control but no quiz CTA;
   - opening the normal study route (without `browse=1`) retains the CTA and practice transition.

## Scope
Frontend only. The backend capability contract correctly identifies whether enrollment permits practice; it does not encode a presentation-only browsing mode and does not need to change.
