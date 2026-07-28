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
            if "FROM login_logs" in query and "status = 'success'" in query:
                return {"fetchall": []}
            return {}

        fake_db = FakeConnection(handler)
        main.app.dependency_overrides[auth.get_db] = lambda: fake_db

        with patch.object(auth.httpx, "AsyncClient", FakeGoogleAsyncClient), \
             patch.object(auth, "try_send_unusual_login_email") as send_alert:
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
        self.assertGreaterEqual(fake_db.commit_calls, 1)
        send_alert.assert_not_called()

    def test_auth_google_alert_failure_does_not_break_login(self):
        new_user_id = "22222222-2222-2222-2222-222222222222"

        def handler(query, params):
            if "SELECT user_id FROM users WHERE email" in query:
                return {"fetchone": None}
            if "INSERT INTO users (username, email, password_hash, is_active)" in query:
                return {"fetchone": (new_user_id,)}
            if "FROM login_logs" in query and "status = 'success'" in query:
                return {
                    "fetchall": [
                        {
                            "ip_address": "198.51.100.3",
                            "device_info": "macOS · Safari",
                            "user_agent": "Mozilla/5.0 Safari/605.1.15",
                            "login_provider": "google",
                            "login_time": None,
                        }
                    ]
                }
            return {}

        fake_db = FakeConnection(handler)
        main.app.dependency_overrides[auth.get_db] = lambda: fake_db

        with patch.object(auth.httpx, "AsyncClient", FakeGoogleAsyncClient), \
             patch.object(auth, "send_auth_email", side_effect=RuntimeError("mail down")):
            response = self.client.post(
                "/auth/google",
                json={"access_token": "fake-google-access-token"},
                headers={
                    "x-forwarded-for": "203.0.113.7",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/138.0 Safari/537.36",
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["login_provider"], "google")


if __name__ == "__main__":
    unittest.main()
