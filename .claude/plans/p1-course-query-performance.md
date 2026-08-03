# P1: Eliminate Course Query Fan-out and Classroom Statistics Round Trips

## Goal
Reduce database work when loading Classroom and CoursePage while preserving the exact current response schema and behavioral semantics.

## Scope
- Rewrite `GET /courses` and `GET /courses/{course_id}` so lesson and language-item counts are independently aggregated instead of materializing a `lessons × language_items` join.
- Rewrite `GET /my-courses/{user_id}` into independently aggregated active-course, item-progress, and lesson-progress relations.
- Combine `GET /classroom/stats/{user_id}` from three sequential `execute()` calls into one SQL statement.
- Add idempotent supporting indexes through the existing schema initialization convention.
- Add regression tests that lock in endpoint output semantics and query-count reductions.

## Pre-implementation production checks
Before deploying new indexes, collect real database evidence. Source code does not prove production index state or plans.

1. Record existing indexes and usage:
   ```sql
   SELECT schemaname, tablename, indexname, indexdef
   FROM pg_indexes
   WHERE tablename IN (
     'user_courses', 'lessons', 'language_items',
     'user_progress_of_lessons', 'user_progress_of_language_items', 'review_logs'
   )
   ORDER BY tablename, indexname;

   SELECT relname, indexrelname, idx_scan, idx_tup_read, idx_tup_fetch
   FROM pg_stat_user_indexes
   WHERE relname IN (
     'user_courses', 'lessons', 'language_items',
     'user_progress_of_lessons', 'user_progress_of_language_items', 'review_logs'
   )
   ORDER BY relname, indexrelname;
   ```
2. Capture `EXPLAIN (ANALYZE, BUFFERS, SETTINGS)` for old and new endpoint SQL using representative learners (including one with the maximum active courses and substantial progress/review history).
3. Verify invariants assumed by the optimized aggregates before replacing current defensive distinct-count logic:
   - one `user_courses` row per `(user_id, course_id)`;
   - one lesson-progress row per `(user_id, course_id)`;
   - one item-progress row per `(user_id, item_id)`.

## Implementation

### 1. Catalog queries without fact-table fan-out

**File:** `backend/main.py`

1. Replace `_COURSE_QUERY` with independent `lesson_counts` and `item_counts` aggregate CTEs joined to `courses`.
2. Ensure `GET /courses` returns all courses, ordered by `course_id`, with zero counts for courses that have no lessons or language items.
3. Use a single-course variant for `GET /courses/{course_id}` that only aggregates records for the target course (e.g., `LEFT JOIN LATERAL` counts), retaining the existing 404 behavior.
4. Keep `_serialize_course` and the response shape unchanged.

### 2. My-courses query with independently scoped rollups

**File:** `backend/main.py`

1. Start with an `active_courses` CTE filtered by `user_courses.user_id::text` and active status.
2. Add `item_progress` scoped to those active course IDs:
   - count every `language_items` row once as `total_item_count`;
   - count mastered rows from optional user item-progress data;
   - retain `COUNT(DISTINCT p.item_id)` unless the production uniqueness invariant is verified; switch to `COUNT(*)` only after that confirmation.
3. Add a `lesson_rollup` scoped to active course IDs that preserves the existing ID-threshold semantics:
   - total lessons per course;
   - completed lessons where `lesson_id <= last_completed_lesson_id`.
4. Retain the per-course `LATERAL` next-lesson lookup, backed by the existing `(course_id, lesson_id)` primary key, because it returns only one indexed row per active course.
5. Preserve all nullable/default fields, the `active`-only filter, and the absence of an explicit output order.

### 3. One statement for Classroom statistics

**File:** `backend/main.py`

1. Replace the three sequential cursor calls with one statement containing three independent scalar/lateral aggregates.
2. Return the same JSON keys and preserve each current metric’s meaning:
   - `totalRemaining`: all due progress rows in active courses;
   - `totalReviewed`: distinct reviewed item IDs today in active courses;
   - `totalNewLearned`: every review-log row with `state = 0` today in active courses.
3. Do not merge underlying sets before aggregation, which would create a progress × review-log fan-out and change counts.
4. Keep database evaluation of `CURRENT_TIMESTAMP`/`CURRENT_DATE`, preserving existing session timezone behavior.

### 4. Supporting indexes and migration path

**File:** `backend/services/course_enrollment_service.py`

1. Add an idempotent `ensure_course_query_indexes(cur)` helper and invoke it from the existing `ensure_user_courses_status(cur)` path.
2. Add the following non-concurrent indexes only after the production audit confirms they are missing and useful:
   ```sql
   CREATE INDEX IF NOT EXISTS progress_items_user_text_item_idx
   ON user_progress_of_language_items ((user_id::text), item_id)
   INCLUDE (is_mastered);

   CREATE INDEX IF NOT EXISTS review_logs_user_text_time_course_idx
   ON review_logs ((user_id::text), review_time, course_id)
   INCLUDE (item_id, state);

   CREATE INDEX IF NOT EXISTS review_logs_user_text_new_time_course_idx
   ON review_logs ((user_id::text), review_time, course_id)
   WHERE state = 0;
   ```
3. Do not add an index duplicating the `lessons(course_id, lesson_id)` primary-key index.
4. For large production tables, supply a separate operator-run migration script/command that creates the new indexes with `CONCURRENTLY` using autocommit. Do not run concurrent index DDL through `init_cloud_schema.py`, because that flow runs in a transaction.
5. Continue using the project’s existing `python database/init_cloud_schema.py` path for fresh/local schema initialization.

## Tests and validation

**Files:**
- Extend `backend/tests/test_course_navigation_auth.py` or add `backend/tests/test_classroom_query_endpoints.py`.
- Update tests only where SQL-shape fixtures currently assume old query text.

1. Catalog tests:
   - anonymous `/courses` and `/courses/{id}` preserve serialized fields, zero-count handling, ordering, and 404 behavior;
   - assert the executed SQL contains separate lesson and language-item aggregates and no simultaneous outer joins to both fact tables.
2. My-courses tests:
   - authenticated active enrollment returns all existing fields;
   - paused/completed enrollment is excluded;
   - missing progress produces zero fields;
   - no-item/no-lesson courses remain valid;
   - assert exactly one SQL statement runs for the request.
3. Classroom statistics tests:
   - use fake database results to assert the same three response keys and values;
   - assert exactly one cursor execution is issued;
   - test zeros are returned when no matching progress/log rows exist.
4. Run code checks:
   ```bash
   cd backend
   python -m py_compile main.py services/course_enrollment_service.py
   python -m unittest tests.test_classroom_query_endpoints tests.test_course_navigation_auth
   ```
5. Current local limitation to report accurately: the available Python environment lacks `psycopg2`, so application-level unit tests cannot import the FastAPI app until backend requirements are installed. Do not interpret that as a test failure in the SQL rewrite.
6. Production acceptance:
   - compare new vs. old response payloads for sampled users;
   - compare DB execution time, rows, buffer reads, and temp-file use from captured explain plans;
   - verify Classroom navigation network timing and database p95 after deployment.

## Explicitly deferred
- Converting all `user_id::text` predicates to native UUID parameter comparisons across the app.
- Moving database access to an async driver/thread pool.
- Complete authorization migration for every remaining private endpoint.
- Study-init, practice-item, R2 signing, and rendering optimizations.
