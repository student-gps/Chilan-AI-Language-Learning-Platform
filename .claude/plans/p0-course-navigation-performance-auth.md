# P0: Classroom → Course Navigation Performance and Boundary Auth

## Goal
Improve the perceived and actual latency when a learner selects a course from Classroom, while closing the most immediate authorization gap on the course-navigation and enrollment APIs. Keep the course catalog and lesson-list preview endpoints public.

## Scope
- Cache-first and prefetch-driven transition from Classroom to CoursePage.
- Remove the CoursePage full-screen loading gate on the redundant course-detail request.
- Send the existing JWT with API requests.
- Add a narrow backend JWT dependency for `my-courses`, Classroom statistics, and enrollment mutations.
- Preserve direct-link/reload behavior and public course catalog access.

## Implementation

### 1. Cache-first course navigation

**Files:**
- `frontend/src/pages/Classroom.jsx`
- `frontend/src/pages/CoursePage.jsx`
- `frontend/src/App.jsx`
- `frontend/src/api/queries.js` (reuse existing query definitions/keys)

1. Add a shared `prefetchCourse(course)` callback in `Classroom`.
   - Resolve a complete course record from `allCourses` by ID; use the clicked course as a fallback.
   - Seed `queryKeys.course(course.id)` via `queryClient.setQueryData`.
   - Prefetch the lesson-list query with `queryClient.prefetchQuery(lessonsQuery(course.id))`.
   - Preload the lazy CoursePage module using a shared `preloadCoursePage()` export/factory from `App.jsx` (rather than a brittle page-relative import from Classroom).
2. Add `openCourse(course)` that calls prefetch first and navigates with `state: { course: selectedCourse }`.
3. Pass a new `onPrefetch` callback into `CourseCard`; invoke it for pointer intent (`onPointerEnter`, `onPointerDown`) so both hover and touch navigation benefit.
4. Replace the two direct `navigate('/course/...')` calls with `openCourse(course)`.
5. In `CoursePage`, supply course data to `courseQuery(courseId)` as `initialData`, in descending priority:
   - matching React Router state,
   - individual-course React Query cache,
   - matching public catalog cache.
   Preserve `initialDataUpdatedAt` where a cache entry is available so the established 10-minute freshness policy remains correct.
6. Keep the course query enabled for hard refresh/direct URLs, but remove it from the page-wide `loading` condition. The visible page should be gated only by a missing locally available course record; `myCourses` and lessons remain localized sections with their own loading state.
7. Do not prefetch `/study/init`: it is personalized, potentially payload-heavy, and outside this narrowly scoped optimization.

### 2. JWT attachment and narrow private-route protection

**Files:**
- `frontend/src/api/apiClient.js`
- `frontend/src/pages/Classroom.jsx`
- `frontend/src/pages/CoursePage.jsx`
- `backend/database/utils.py`
- `backend/main.py`

1. In the Axios request interceptor, read `getValidToken()` and attach `Authorization: Bearer <token>` when present, preserving the existing language-header behavior.
2. Remove `user_id` from new frontend enrollment/unenrollment mutation bodies; retain it only in client-local React Query keys.
3. In `backend/database/utils.py`, add a JWT decoder/subject extractor beside `create_access_token`, using the same secret, algorithm, signature validation, and expiration validation.
4. In `backend/main.py`, add a `HTTPBearer(auto_error=False)` dependency named for the authenticated subject. It must return a 401 response with `WWW-Authenticate: Bearer` for missing, malformed, expired, or invalid credentials.
5. Apply this guard only to:
   - `GET /my-courses/{user_id}`
   - `GET /classroom/stats/{user_id}`
   - `POST /courses/enroll`
   - `DELETE /courses/enroll`
6. Path user IDs must match JWT `sub` or return 403 before querying private data. Enrollment SQL must use the JWT subject, never the request body.
7. Keep `EnrollReq.user_id` optional only for a temporary compatibility transition: accept it if equal to the JWT subject; reject a mismatch with 403.
8. Keep `/courses`, `/courses/{course_id}`, and `/courses/{course_id}/lessons` public.

### 3. Tests and verification

**Files:**
- Add `backend/tests/test_course_navigation_auth.py`

1. Test 401 and `WWW-Authenticate: Bearer` for every newly protected endpoint with no token.
2. Test invalid/expired JWT rejection.
3. Test 403 user-ID mismatch for path requests and old enrollment payloads, verifying no mutation SQL happens.
4. Test valid JWT requests, including enrollment with no `user_id` and legacy matching `user_id`; assert SQL is parameterized using the JWT subject.
5. Test the public catalog/course/lesson endpoints stay anonymous-accessible.
6. Run:
   - `python -m unittest tests.test_course_navigation_auth`
   - `python -m unittest tests.test_auth_login tests.test_study_init`
   - `npm run lint`
   - `npm run build`
7. Browser acceptance verification:
   - Classroom click does not issue `GET /courses/:id` after catalog is cached.
   - Lessons request is prefetched or reuses a single in-flight call.
   - Course shell/title appears immediately; enrollment/progress remains localized while refreshing.
   - Direct course URLs still load correctly.
   - Authenticated private course calls succeed; missing-token private calls return 401 while catalog endpoints remain public.

## Deployment note
Deploy the frontend JWT-header update before enabling the backend guard, or deploy atomically. Otherwise an old cached frontend will receive 401 responses for newly protected endpoints.

## Explicitly deferred
- Full authorization conversion of study, overview, daily task, profile, and account endpoints.
- SQL rewrites, index migrations, `EXPLAIN ANALYZE` production profiling, async database conversion, lesson-list virtualization, and audio URL signing optimizations.
- Those will follow in order after this P0 patch is deployed and measured.
