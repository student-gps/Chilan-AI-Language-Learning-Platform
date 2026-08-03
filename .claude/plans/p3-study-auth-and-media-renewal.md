# P3: Secure Study APIs, Preserve Teaching Previews, and Prepare Renewable Media

## Product decision
Unauthenticated access remains disallowed for study endpoints. A logged-in learner who is not actively enrolled may continue to open a direct course lesson **for teaching-only preview**. They will never receive practice items/answers, transcribe speech, evaluate answers, write progress, or renew private lesson audio. Active enrollment remains required for all practice and progress operations.

## Goals
1. Make JWT `sub` the only trusted identity for learner study APIs.
2. Preserve explicit teaching preview while closing answer/progress leakage.
3. Prepare an authenticated, course-scoped media renewal contract for later lazy signing and expired-audio retry.
4. Perform a safe database maintenance run, then remeasure the already-identified course catalog query.

## Phase 1 — Shared JWT dependency and study authorization

### Shared dependency

**New file:** `backend/dependencies/auth.py`

- Move `HTTPBearer(auto_error=False)`, `require_current_user_id`, and `require_matching_user_id` from `backend/main.py` to this module.
- Keep the exact 401 response and `WWW-Authenticate: Bearer` header behavior.
- Continue verification through `database.utils.decode_access_token_subject`.
- Validate that the decoded subject is a UUID before passing it to study services that bind `::uuid` values; malformed subjects return 401.

**Update:** `backend/main.py`

- Import the shared functions and remove the duplicate local dependency implementation.
- Existing private Classroom/enrollment endpoints keep their current behavior.

### Course access helpers

**New file:** `backend/services/study/access_service.py`

Implement small cursor-scoped helpers so route handlers do not open extra database connections:

- `assert_lesson_belongs_to_course(cur, course_id, lesson_id)` → 404 when absent.
- `is_active_course_enrollment(cur, user_id, course_id)` → bool.
- `assert_active_course_enrollment(cur, user_id, course_id)` → 403 when no active enrollment.
- `get_item_course_context(cur, item_id)` → canonical item/course/lesson context, 404 when absent.

All checks must use the JWT subject, no client user ID. The enrollment predicate requires `user_courses.status = 'active'`.

### Server-owned capabilities

**Files:**
- `backend/services/study/init_flow_service.py`
- `backend/routers/study.py`

1. Change init flow to return a server-computed capability object:
   ```json
   {
     "capabilities": {
       "can_view_lesson": true,
       "can_practice": false,
       "can_write_progress": false,
       "can_renew_lesson_media": false
     }
   }
   ```
2. Policy:
   - Normal entry without `lesson_id`: active enrollment required; retain current `200 { "mode": "not_enrolled" }` behavior for authenticated non-enrolled learners.
   - Direct browse (`lesson_id`, `browse=true`): authenticated learner receives teaching content only if the lesson belongs to the course. For non-enrolled learners, omit pending items and set all practice/write/media capabilities false.
   - Direct browse by an active learner retains authorized practice.
3. Ignore client-controlled `defer_practice` for authorization purposes. The server determines whether practice data can be loaded.
4. Ensure the Minna local-artifact preview shortcut runs only after the same course/lesson authorization decision and reports the correct capabilities.

### Private study endpoints

Apply `Depends(require_current_user_id)` to:

- `GET /study/init`
- `GET /study/practice_items`
- `POST /study/evaluate`
- `POST /study/content_viewed`
- `POST /study/practice_progress`
- `POST /study/complete_lesson`
- `GET /study/knowledge`
- `POST /study/speech/transcribe`

During this compatibility patch, accept a legacy `user_id` only where existing client models require it, reject a mismatch with `403`, and always use JWT `sub` internally. Then remove legacy fields from frontend calls in the same patch; a later cleanup can make Pydantic reject the legacy fields entirely.

For each practice/write endpoint:

- Validate active enrollment before loading answers, calling ASR/LLM, or writing progress.
- Validate a requested lesson belongs to the requested course.
- For evaluate/knowledge/ASR, resolve the canonical course/lesson from `item_id`; never trust a client-provided course, lesson, question, prompt, or answer list.
- Preserve generic `GET /study/tts` as public because it is used by raw browser `Audio` objects, but leave it out of learner identity/progress logic.

## Phase 2 — Frontend identity cleanup and capability gating

**Files:**
- `frontend/src/pages/studyPage/index.jsx`
- `frontend/src/pages/studyPage/practice/PracticeSection.jsx`
- `frontend/src/pages/studyPage/practice/hooks/usePracticeFlow.js`
- `frontend/src/pages/studyPage/practice/hooks/useSpeechPractice.js`
- `frontend/src/api/apiClient.js`
- `frontend/src/pages/studyPage/english/NewConceptTeachingSection.jsx`

1. Remove `user_id` from init, practice item, content-viewed, practice-progress, completion, evaluate, and ASR payloads/parameters.
2. Replace local enrollment-derived decisions with `data.capabilities` from init:
   - do not prefetch practice items for teaching-only previews;
   - hide/disable Start Practice for `can_practice=false`;
   - do not call content-viewed, progress, or completion when `can_write_progress=false`.
3. Remove `userId` plumbing from practice components/hooks and delete the current local-storage/`test-user-id` fallback.
4. Pass `item_id` with speech transcription form data so the backend can authorize its course before calling the ASR provider.
5. Remove the duplicate New Concept `content_viewed` request; parent `onStartPractice` handles the guarded write consistently.

## Phase 3 — Answer-safe projection

The browser currently receives `standard_answers` in practice items. JWT authorization alone does not prevent a learner from inspecting those answers, so this phase is mandatory before claiming answer leakage is fixed.

**Files:**
- `backend/services/study/init_flow_service.py`
- `backend/routers/study.py`
- `frontend/src/pages/studyPage/practice/PracticeSection.jsx`
- `frontend/src/pages/studyPage/practice/components/PracticeFeedbackPanel.jsx`
- related practice flow tests

1. Define an allowlisted practice DTO with only the client-required display and audio-reference fields.
2. Omit `standard_answers` and arbitrary database metadata from `/study/init` review payloads and `/study/practice_items`.
3. Refactor evaluation to use only `item_id`, answer/speech payload, and forfeit flag; load canonical prompt/type/answers from the database.
4. Return canonical `expected_answers` only in the evaluation feedback after a submission or forfeit.
5. Update feedback UI to use `feedback.expected_answers` rather than `currentQuestion.standard_answers`.
6. Replace the listen-write fallback currently based on `standard_answers[0]` with a lesson audio asset or server-authorized item audio endpoint.

## Phase 4 — Renewable audio URL contract

Implement this after study authorization is in place. It will initially provide safe renewal; lazy signing can follow once runtime timing establishes signing volume as meaningful.

**Backend:**
- Add `POST /study/media/audio-url` with `{ course_id, lesson_id, asset_ref }`.
- JWT plus active enrollment required.
- Load the canonical lesson audio JSON from the database, match `asset_ref` only against a full-lesson marker or known sentence asset `line_ref`/`audio_id`, and resolve only that canonical object key.
- Do not accept raw object keys, paths, filenames, or URLs from the browser.
- If R2 has a public base URL, return the stable public URL; otherwise return a freshly signed URL.
- Return an opaque asset reference and expiration hint; no storage credentials.

**Frontend:**
- Add one audio-load retry on full/sentence audio errors: call the renewal endpoint using the known course/lesson/reference, replace the in-memory URL, retry playback once.
- Do not persist signed URLs in localStorage or React Query shared caches.
- Preserve current immediate full-audio behavior; defer all-sentence lazy signing until measured server timing shows it is worthwhile.

## Phase 5 — Production maintenance and remeasurement

The production audit found the course catalog’s 45.879 ms duration is dominated by language-item aggregation and 24,638 heap fetches. It also found stale `language_items` statistics.

1. In an approved maintenance window, run:
   ```sql
   VACUUM (ANALYZE) language_items;
   ```
   This is an operational database action, not a code-path migration. It may generate I/O; schedule it deliberately.
2. Re-run the read-only diagnostics tool for `course-catalog` and `index-audit`.
3. Compare execution time, heap fetch count, visibility behavior, table stats, and shared block activity before deciding on a larger catalog-count cache or materialized summary.
4. Do not create indexes merely from scan counts. The production audit already confirms the lesson-item unique index exists and is used.

## Tests and verification

### Backend
Add focused tests for:

- 401 missing/invalid bearer tokens on every listed private study endpoint;
- 403 when an optional legacy user ID mismatches the token subject;
- normal non-enrolled init remains `mode: not_enrolled`;
- non-enrolled direct browse returns teaching-only capabilities and no practice payload;
- active enrolled direct browse returns practice capabilities;
- paused/completed enrollment blocks practice, ASR, evaluate, knowledge, and writes before any sensitive query/provider call;
- lesson/course mismatch is rejected;
- evaluate/knowledge/ASR resolve canonical item context, not payload context;
- media renewal rejects raw paths, unknown asset references, wrong course/lesson, and inactive enrollment;
- public R2 vs. signed R2 URL behavior.

### Frontend
Run:

```bash
cd frontend
npx eslint src/api/apiClient.js src/pages/studyPage/index.jsx src/pages/studyPage/practice src/pages/studyPage/english/NewConceptTeachingSection.jsx
npm run build
```

Manual flows:

1. active enrolled learner starts a normal lesson, direct lesson, review, practice, speech answer, and completion;
2. non-enrolled authenticated learner opens a course lesson and sees teaching-only preview, without a practice request;
3. expired audio URL renews and plays once;
4. logout/expired JWT leads to existing login redirect behavior;
5. verify browser network payloads no longer include `user_id`, standard answers, or raw media object keys.

## Explicitly deferred
- Full conversion from text-cast UUID predicates to native UUID bind parameters.
- Private protection of generic TTS and dev preview routes.
- Full CDN/static lesson content split.
- Bulk lazy-signing rollout without timing evidence.
