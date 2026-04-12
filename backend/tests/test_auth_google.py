import unittest
from unittest.mock import patch

from .test_helpers import FakeConnection, FakeGoogleAsyncClient, SmokeTestCaseMixin, auth, main


class AuthGoogleSmokeTests(SmokeTestCaseMixin, unittest.TestCase):
    def test_auth_google_creates_or_logs_in_google_user(self):
        new_user_id = "22222222-2222-2222-2222-222222222222"

        def handler(query, params):
            if "SELECT user_id FROM users WHERE email" in query:
                return {"fetchone": None}
            if "INSERT INTO users (username, email, password_hash, is_active)" in query:
                return {"fetchone": (new_user_id,)}
            return {}

        fake_db = FakeConnection(handler)
        main.app.dependency_overrides[auth.get_db] = lambda: fake_db

        with patch.object(auth.httpx, "AsyncClient", FakeGoogleAsyncClient):
            response = self.client.post(
                "/auth/google",
                json={"access_token": "fake-google-access-token"},
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["login_provider"], "google")
        self.assertEqual(body["email"], "google-user@example.com")
        self.assertEqual(body["user_id"], new_user_id)
        self.assertIn("access_token", body)
        self.assertGreaterEqual(fake_db.commit_calls, 2)


if __name__ == "__main__":
    unittest.main()
