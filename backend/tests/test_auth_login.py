import unittest

from .test_helpers import FakeConnection, SmokeTestCaseMixin, auth, get_password_hash, main


class AuthLoginSmokeTests(SmokeTestCaseMixin, unittest.TestCase):
    def test_auth_login_returns_token_and_user_info(self):
        user_id = "11111111-1111-1111-1111-111111111111"
        password_hash = get_password_hash("Passw0rd!")

        def handler(query, params):
            if "SELECT user_id, username, email, password_hash, is_active FROM users" in query:
                return {
                    "fetchone": (user_id, "Student GPS", "student@example.com", password_hash, True)
                }
            return {}

        fake_db = FakeConnection(handler)
        main.app.dependency_overrides[auth.get_db] = lambda: fake_db

        response = self.client.post(
            "/auth/login",
            json={"email": "student@example.com", "password": "Passw0rd!"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["email"], "student@example.com")
        self.assertEqual(body["login_provider"], "password")
        self.assertEqual(body["user_id"], user_id)
        self.assertIn("access_token", body)
        self.assertGreaterEqual(fake_db.commit_calls, 1)


if __name__ == "__main__":
    unittest.main()
