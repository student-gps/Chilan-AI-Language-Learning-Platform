import unittest
from unittest.mock import patch

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
            if "FROM login_logs" in query and "status = 'success'" in query:
                return {"fetchall": []}
            return {}

        fake_db = FakeConnection(handler)
        main.app.dependency_overrides[auth.get_db] = lambda: fake_db

        with patch.object(auth, "try_send_unusual_login_email") as send_alert:
            response = self.client.post(
                "/auth/login",
                json={"email": "student@example.com", "password": "Passw0rd!"},
                headers={
                    "x-forwarded-for": "203.0.113.7",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/138.0 Safari/537.36",
                    "accept-language": "en-US,en;q=0.9",
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["email"], "student@example.com")
        self.assertEqual(body["login_provider"], "password")
        self.assertEqual(body["user_id"], user_id)
        self.assertIn("access_token", body)
        self.assertGreaterEqual(fake_db.commit_calls, 1)
        send_alert.assert_not_called()

    def test_auth_login_sends_unusual_login_alert_when_ip_and_device_are_new(self):
        user_id = "11111111-1111-1111-1111-111111111111"
        password_hash = get_password_hash("Passw0rd!")

        def handler(query, params):
            if "SELECT user_id, username, email, password_hash, is_active FROM users" in query:
                return {
                    "fetchone": (user_id, "Student GPS", "student@example.com", password_hash, True)
                }
            if "FROM login_logs" in query and "status = 'success'" in query:
                return {
                    "fetchall": [
                        {
                            "ip_address": "198.51.100.3",
                            "device_info": "macOS · Safari",
                            "user_agent": "Mozilla/5.0 Safari/605.1.15",
                            "login_provider": "password",
                            "login_time": None,
                        }
                    ]
                }
            return {}

        fake_db = FakeConnection(handler)
        main.app.dependency_overrides[auth.get_db] = lambda: fake_db

        with patch.object(auth, "try_send_unusual_login_email") as send_alert:
            response = self.client.post(
                "/auth/login",
                json={"email": "student@example.com", "password": "Passw0rd!"},
                headers={
                    "x-forwarded-for": "203.0.113.7",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/138.0 Safari/537.36",
                    "accept-language": "en-US,en;q=0.9",
                },
            )

        self.assertEqual(response.status_code, 200)
        send_alert.assert_called_once()
        call_args = send_alert.call_args
        self.assertEqual(call_args.args[0], "student@example.com")
        self.assertEqual(call_args.kwargs["provider"], "password")
        self.assertEqual(call_args.kwargs["lang"], "en")
        self.assertEqual(call_args.kwargs["login_context"]["ip_address"], "203.0.113.7")
        self.assertEqual(call_args.kwargs["login_context"]["device_info"], "Windows · Chrome")

    def test_auth_login_still_succeeds_when_unusual_login_email_send_fails(self):
        user_id = "11111111-1111-1111-1111-111111111111"
        password_hash = get_password_hash("Passw0rd!")

        def handler(query, params):
            if "SELECT user_id, username, email, password_hash, is_active FROM users" in query:
                return {
                    "fetchone": (user_id, "Student GPS", "student@example.com", password_hash, True)
                }
            if "FROM login_logs" in query and "status = 'success'" in query:
                return {
                    "fetchall": [
                        {
                            "ip_address": "198.51.100.3",
                            "device_info": "macOS · Safari",
                            "user_agent": "Mozilla/5.0 Safari/605.1.15",
                            "login_provider": "password",
                            "login_time": None,
                        }
                    ]
                }
            return {}

        fake_db = FakeConnection(handler)
        main.app.dependency_overrides[auth.get_db] = lambda: fake_db

        with patch.object(auth, "send_auth_email", side_effect=RuntimeError("mail down")):
            response = self.client.post(
                "/auth/login",
                json={"email": "student@example.com", "password": "Passw0rd!"},
                headers={
                    "x-forwarded-for": "203.0.113.7",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/138.0 Safari/537.36",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")


if __name__ == "__main__":
    unittest.main()
