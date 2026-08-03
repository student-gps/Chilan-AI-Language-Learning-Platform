import unittest
from datetime import timedelta

from .test_helpers import FakeConnection, SmokeTestCaseMixin, main
from database.utils import create_access_token


USER_A = "11111111-1111-1111-1111-111111111111"
USER_B = "22222222-2222-2222-2222-222222222222"


def auth_headers(user_id=USER_A):
    return {"Authorization": f"Bearer {create_access_token({'sub': user_id})}"}


class CourseNavigationAuthTests(SmokeTestCaseMixin, unittest.TestCase):
    def test_private_navigation_endpoints_require_a_bearer_token(self):
        responses = [
            self.client.get(f"/my-courses/{USER_A}"),
            self.client.get(f"/classroom/stats/{USER_A}"),
            self.client.post("/courses/enroll", json={"course_id": 1}),
            self.client.request("DELETE", "/courses/enroll", json={"course_id": 1}),
        ]

        for response in responses:
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.headers.get("www-authenticate"), "Bearer")

    def test_private_navigation_endpoints_reject_invalid_or_expired_tokens(self):
        expired_token = create_access_token({"sub": USER_A}, expires_delta=timedelta(seconds=-1))

        for headers in ({"Authorization": "Bearer invalid"}, {"Authorization": f"Bearer {expired_token}"}):
            response = self.client.get(f"/my-courses/{USER_A}", headers=headers)
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.headers.get("www-authenticate"), "Bearer")

    def test_private_paths_reject_a_different_token_subject_before_database_access(self):
        fake_db = FakeConnection(lambda query, params: {})
        main.app.dependency_overrides[main.get_db] = lambda: fake_db

        response = self.client.get(f"/my-courses/{USER_B}", headers=auth_headers(USER_A))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(fake_db.executed_queries, [])

    def test_enrollment_rejects_a_mismatched_legacy_user_id_before_database_access(self):
        fake_db = FakeConnection(lambda query, params: {})
        main.app.dependency_overrides[main.get_db] = lambda: fake_db

        response = self.client.post(
            "/courses/enroll",
            json={"course_id": 1, "user_id": USER_B},
            headers=auth_headers(USER_A),
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(fake_db.executed_queries, [])

    def test_enrollment_uses_the_authenticated_subject_when_user_id_is_omitted(self):
        def handler(query, params):
            if "SELECT status FROM user_courses" in query:
                return {"fetchone": ("active",)}
            return {}

        fake_db = FakeConnection(handler)
        main.app.dependency_overrides[main.get_db] = lambda: fake_db

        response = self.client.post(
            "/courses/enroll",
            json={"course_id": 1},
            headers=auth_headers(USER_A),
        )

        self.assertEqual(response.status_code, 200)
        status_query = next(params for query, params in fake_db.executed_queries if "SELECT status FROM user_courses" in query)
        self.assertEqual(status_query[0], USER_A)

    def test_public_catalog_and_lesson_endpoints_remain_anonymous(self):
        def handler(query, params):
            if "WITH lesson_counts AS" in query:
                return {"fetchall": [(1, "Course", "general", "zh", "en", 1, 2)]}
            if "LEFT JOIN LATERAL" in query and "WHERE c.course_id = %s" in query:
                return {"fetchone": (1, "Course", "general", "zh", "en", 1, 2)}
            if "FROM lessons WHERE course_id = %s" in query:
                return {"fetchall": [(101, "Lesson 101", "第一课")]}
            return {}

        fake_db = FakeConnection(handler)
        main.app.dependency_overrides[main.get_db] = lambda: fake_db

        catalog = self.client.get("/courses")
        course = self.client.get("/courses/1")
        lessons = self.client.get("/courses/1/lessons")

        self.assertEqual(catalog.status_code, 200)
        self.assertEqual(course.status_code, 200)
        self.assertEqual(lessons.status_code, 200)
        self.assertEqual(catalog.json()[0]["id"], 1)
        self.assertEqual(course.json()["id"], 1)
        self.assertEqual(lessons.json()[0]["lesson_id"], 101)

        catalog_query = fake_db.executed_queries[0][0]
        self.assertIn("WITH lesson_counts AS", catalog_query)
        self.assertIn("item_counts AS", catalog_query)
        self.assertNotIn("LEFT JOIN lessons       l", catalog_query)

    def test_my_courses_uses_independent_active_course_rollups(self):
        def handler(query, params):
            if "WITH active_courses AS" in query:
                return {
                    "fetchall": [
                        (1, "Course", "general", "zh", "en", 4, 10, 3, 1, 101, 102, 2, 102, "Lesson 102", "第二课")
                    ]
                }
            return {}

        fake_db = FakeConnection(handler)
        main.app.dependency_overrides[main.get_db] = lambda: fake_db

        response = self.client.get(f"/my-courses/{USER_A}", headers=auth_headers())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{
            "id": 1,
            "name": "Course",
            "category": "general",
            "target_language": "zh",
            "source_language": "en",
            "mastered": 4,
            "total_items": 10,
            "lesson_total": 3,
            "completed_lesson_count": 1,
            "last_completed_lesson_id": 101,
            "viewed_lesson_id": 102,
            "practice_question_index": 2,
            "next_lesson_id": 102,
            "next_lesson_title": "Lesson 102",
            "next_lesson_title_localized": "第二课",
        }])
        self.assertEqual(len(fake_db.executed_queries), 1)
        query, params = fake_db.executed_queries[0]
        self.assertIn("WITH active_courses AS", query)
        self.assertIn("item_progress AS", query)
        self.assertIn("lesson_rollup AS", query)
        self.assertEqual(params, (USER_A, "active", USER_A, USER_A, USER_A))

    def test_classroom_stats_uses_one_statement_and_preserves_metric_values(self):
        def handler(query, params):
            if "CROSS JOIN LATERAL" in query:
                return {"fetchone": (5, 3, 2)}
            return {}

        fake_db = FakeConnection(handler)
        main.app.dependency_overrides[main.get_db] = lambda: fake_db

        response = self.client.get(f"/classroom/stats/{USER_A}", headers=auth_headers())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "totalRemaining": 5,
            "totalReviewed": 3,
            "totalNewLearned": 2,
        })
        self.assertEqual(len(fake_db.executed_queries), 1)
        query, params = fake_db.executed_queries[0]
        self.assertEqual(query.count("CROSS JOIN LATERAL"), 3)
        self.assertIn("COUNT(DISTINCT rl.item_id)", query)
        self.assertIn("rl.state = 0", query)
        self.assertEqual(params, ("active", USER_A, "active", USER_A, "active", USER_A))


if __name__ == "__main__":
    unittest.main()
