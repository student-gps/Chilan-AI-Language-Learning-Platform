# P2: Production Database Diagnostics and Study-Initialization Performance

## Goal
First collect safe, redacted production evidence for query plans and indexes. Then use that evidence to reduce study-start latency caused by sequential database work, duplicated lesson JSON, connection retention, and per-asset R2 signing—without changing lesson behavior or leaking learner/media access.

## Verified environment facts
- The primary workspace contains `backend/.env`; its contents will not be read into chat or output.
- The local Python runtime can import `psycopg2`; `psql` is not installed.
- Production access is therefore feasible through Python only when the configured database URL is valid. Diagnostics must never print connection URLs, credentials, raw user IDs, answer text, lesson JSON, or JWTs.

## Phase A — Read-only production diagnostics

### 1. Add a fixed-query diagnostics CLI

**New file:** `backend/scripts/db_diagnostics.py`

Implement a Python CLI that:

1. Requires all of:
   ```text
   --environment production
   --confirm-readonly
   ```
   and refuses to run otherwise.
2. Reads `DIAGNOSTICS_DATABASE_URL` by default. It may use the application database URL only with an explicit `--allow-app-database-url` flag, which will be used solely for the user-requested immediate diagnostic run.
3. Opens a direct (non-pooled) psycopg2 connection; sets an identifying `application_name`; enters a read-only transaction; applies a 10-second statement timeout, 1-second lock timeout, and 15-second idle-in-transaction timeout.
4. Contains a closed set of query IDs rather than accepting arbitrary SQL:
   - `index-audit` — index definitions, sizes, validity, scan counts, and table statistics;
   - `course-catalog` — current optimized `/courses` SQL;
   - `course-detail` — current optimized `/courses/{id}` SQL;
   - `my-courses` — current optimized active-course rollup;
   - `classroom-stats` — current combined statistics SQL;
   - `due-review` — study-init FSRS queue query;
   - `lesson-items` — course/lesson questions query;
   - `study-item` — evaluation item-resolution query.
5. Selects a representative active learner/course/lesson inside the read-only session without printing the IDs. It should prefer the active course with the most item progress/review logs, then fall back to a published course/lesson. It must reject missing targets with a concise non-sensitive error.
6. Runs plan-only `EXPLAIN (FORMAT JSON, SETTINGS TRUE)` by default. `--analyze` opts into `EXPLAIN (ANALYZE, BUFFERS, SETTINGS TRUE, FORMAT JSON)` and executes each selected read query once.
7. Sanitizes all plan data before output: redact UUIDs, literals, long text, query parameter values, and any `Query Text` values. Emit only query ID, timing, plan tree, relation/index names, estimates/actual rows, block/temp I/O, settings, table/index statistics, and selected target type—not record content or identifiers.
8. Writes the full sanitized report to a temporary OS directory by default (outside the repository), prints only the report path plus a concise summary, and rolls back/closes every session.

### 2. Add diagnostics tests

**New file:** `backend/tests/test_db_diagnostics.py`

Test that the CLI:

- refuses missing production/read-only confirmations;
- chooses `DIAGNOSTICS_DATABASE_URL` over the app URL;
- requires explicit app-URL fallback;
- sets read-only settings and rolls back;
- rejects unsupported query IDs;
- redacts UUIDs/literals/query text from report objects;
- treats plan-only and analyze modes separately;
- never emits the configured URL or SQL parameters.

Use fake connection/cursor objects; no database connection in unit tests.

### 3. Execute the diagnostic run requested by the user

After code checks pass, run from `backend/`:

```bash
python scripts/db_diagnostics.py \
  --environment production \
  --confirm-readonly \
  --allow-app-database-url \
  --analyze \
  --queries index-audit,course-catalog,course-detail,my-courses,classroom-stats,due-review,lesson-items,study-item
```

The command will execute only read queries in a read-only transaction. Report the sanitized timing, scan type, estimate-vs-actual discrepancies, buffer reads, temporary-file use, and whether the expected indexes are used. If credentials, permissions, target selection, or timeouts prevent the run, report that exact constraint without exposing secrets and stop before any database change.

### 4. Index decision gate

Do not blindly create further indexes. From the live report:

- preserve primary-key/unique indexes even if their scan count is zero;
- add an index only if a high-frequency query has a poor plan, a selective missing predicate/order prefix, and expected write overhead is acceptable;
- if an index is justified on a large production table, create it via a separate operator-run autocommit `CREATE INDEX CONCURRENTLY` migration—never through the current transactional initializer.

Candidates to evaluate, not automatically create:

```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS language_items_course_lesson_question_idx
ON language_items (course_id, lesson_id, question_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS lesson_progress_user_course_idx
ON user_progress_of_lessons ((user_id::text), course_id)
INCLUDE (last_completed_lesson_id, viewed_lesson_id, practice_question_index);
```

The existing lessons primary key `(course_id, lesson_id)` must not be duplicated.

## Phase B — Instrument study start before changing its data contract

**Files:**
- `backend/services/study/init_flow_service.py`
- `backend/routers/study.py`
- `backend/services/utils/monitor.py` or a focused new timing helper
- `backend/tests/test_study_init.py`

1. Add opt-in structured timings for `/study/init` and `/study/practice_items`:
   - database query total/count;
   - lesson-cache hit/miss;
   - canonical lesson payload byte estimate;
   - URL hydration/signing duration and number of signed assets;
   - response-build duration;
   - practice-item query duration.
2. Return compact `Server-Timing` values only when an explicit performance environment flag is enabled. Do not expose SQL, user IDs, media object keys, or lesson contents in headers/logs.
3. Add unit tests verifying the metrics are emitted only when enabled and contain no sensitive identifiers.
4. Use the telemetry plus network response size to decide which of the following changes has measurable priority; capture a before/after baseline from a representative lesson.

## Phase C — Study init query, connection, cache, payload, and media improvements

### 1. Preserve behavior while reducing DB round trips

**Files:**
- `backend/services/study/init_flow_service.py`
- `backend/services/course_enrollment_service.py` (only if live plans justify indexes)
- `backend/tests/test_study_init.py`

1. Combine static course metadata, active enrollment check, and user lesson-progress retrieval into a single context query for `/study/init`.
   - Preserve normal no-lesson behavior: active enrollment is required before a non-browse learning flow.
   - Preserve explicit browse behavior only if product policy intentionally permits previewing an unenrolled lesson.
2. Refactor `/study/practice_items` so lesson progress and lesson items are retrieved in one statement, including a safe zero-item case. Preserve question ordering and current `practice_resume_index` clamping.
3. Add deterministic ties without changing primary sort semantics:
   - due review: `ORDER BY p.next_review ASC, q.item_id ASC`;
   - practice items: `ORDER BY question_id ASC, item_id ASC`.
4. Release the database connection immediately after all required rows are read—before JSON copying, response construction, and R2 signing.
5. Keep the existing `defer_practice=1` teaching-first behavior. Do not prefetch complete study flows from the course page.

### 2. Make lesson cache immutable, bounded, and useful

**File:** `backend/services/study/init_flow_service.py`

1. Cache only canonical lesson data without signed URLs or user-specific fields.
2. Deep-copy the canonical lesson before response hydration so sentence/full-audio dictionaries and video data cannot mutate cached nested data.
3. Add a bounded configurable TTL and cache age metadata; after TTL, reload from PostgreSQL.
4. Resolve the next lesson ID first, then consult the same `(course_id, lesson_id)` cache for sequential lesson progression, not only explicit lesson URLs.
5. Provide an explicit in-process invalidation helper for publishing paths where available. The TTL remains the cross-worker safety boundary.

### 3. Reduce initial response size without breaking the frontend

**Files:**
- `backend/services/study/init_flow_service.py`
- `frontend/src/pages/studyPage/teaching/index.jsx`
- `frontend/src/pages/studyPage/english/NewConceptTeachingSection.jsx`
- tests for the response contract

1. Remove the duplicated top-level `teaching_slide_deck` field from `lesson_content`; `TeachingSection` already reads the nested `video_render_plan.teaching_slide_deck` fallback.
2. Keep `course_content`, `teaching_materials` for New Concept English, nested deck, audio asset metadata, and fields required by existing teaching/practice UI.
3. Measure before removing any additional JSON fields. Do not split static lesson content into a separate endpoint until payload telemetry confirms it is a dominant cost; that larger API/cache redesign should be a follow-up instead of speculative scope.

### 4. Fix media URL lifecycle safely

**Files:**
- `backend/services/study/init_flow_service.py`
- `backend/routers/study.py`
- `frontend/src/pages/studyPage/teaching/hooks/useTeachingAudio.js`
- `frontend/src/pages/studyPage/practice/PracticeSection.jsx`

1. Keep current behavior until timing shows all-asset signing is material. If it is, introduce an authenticated course/lesson-scoped media URL renewal endpoint that validates that the requested audio reference belongs to the loaded lesson.
2. Keep a valid URL for the full lesson audio at init; lazy-renew sentence audio only when playback starts or retries after expiry.
3. Never serve a cache shared across users with presigned bearer URLs. For genuinely public assets, use immutable public CDN URLs and cache headers; for private assets, retain per-user authorization and a renewal strategy.
4. Add a single retry path when browser audio load fails due to an expired URL.

### 5. Remove learning-path runtime DDL

**Files:**
- `backend/services/study/lesson_progress_service.py`
- `backend/database/init_cloud_schema.py` or a dedicated migration script
- tests

1. Move lesson-progress columns (`practice_question_index`, `practice_question_updated_at`) into a controlled idempotent migration/init path.
2. Remove `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` from `content_viewed`, `practice_progress`, and lesson completion request paths.
3. Do not alter or backfill production tables from request handlers.

### 6. Authorization prerequisite for caching/media

Before splitting/cacheing user-specific study responses or adding a media renewal endpoint, move the shared JWT dependency from `backend/main.py` into a dependency module usable by both the main app and study router. Then:

- derive the actor from JWT `sub`;
- reject user-ID mismatches;
- decide and test whether browse previews are public or authenticated;
- do not expose practice items/answer keys for an unenrolled or unauthorized course;
- update the frontend to stop sending authoritative `user_id` for these private calls.

This must be completed before introducing shared/cached study delivery that could otherwise leak learning state or media.

## Verification

1. `python -m py_compile` all changed backend modules and diagnostics tests.
2. Run focused backend tests after installing backend requirements in the active interpreter; current local execution cannot import the FastAPI app because the system Python environment lacks `psycopg2` even though `psycopg2-binary` is declared by the project.
3. Exercise StudyPage manually for:
   - active learner with no due reviews;
   - active learner with due reviews;
   - direct/browse lesson;
   - New Concept English course;
   - lesson with full and sentence audio;
   - expired media URL retry;
   - no lesson/no item edge cases.
4. Compare before/after `Server-Timing`, response bytes, production query plans, and p50/p95 request durations. Only keep changes that preserve behavior and show a measurable result.

## Explicitly deferred
- Replacing synchronous psycopg2 with a full async database stack.
- Broad CDN/ETag static-lesson API redesign.
- Global conversion from `user_id::text` to native UUID comparisons.
- Full authorization migration for all remaining non-study endpoints.
