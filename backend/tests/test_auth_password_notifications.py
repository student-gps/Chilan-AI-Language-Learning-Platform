import unittest
from unittest.mock import patch

from .test_helpers import FakeConnection, SmokeTestCaseMixin, auth, get_password_hash, main


class AuthPasswordNotificationSmokeTests(SmokeTestCaseMixin, unittest.TestCase):
    def test_reset_password_sends_success_notification(self):
        updated_password_hashes = []

        def handler(query, params):
            if "SELECT code FROM verification_codes WHERE email = %s" in query:
                return {"fetchone": ("123456",)}
            if "UPDATE users SET password_hash = %s WHERE email = %s" in query:
                updated_password_hashes.append(params[0])
                return {}
            return {}

        fake_db = FakeConnection(handler)
        main.app.dependency_overrides[auth.get_db] = lambda: fake_db

        with patch.object(auth, "try_send_password_changed_email") as send_success:
            response = self.client.post(
                "/auth/reset-password",
                json={
                    "email": "student@example.com",
                    "code": "123456",
                    "new_password": "Passw0rd!",
                },
                headers={
                    "X-Chilan-Interface-Language": "jp",
                    "accept-language": "en-US,en;q=0.9",
                    "x-forwarded-for": "203.0.113.7",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/138.0 Safari/537.36",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertGreaterEqual(fake_db.commit_calls, 1)
        self.assertEqual(len(updated_password_hashes), 1)
        self.assertNotEqual(updated_password_hashes[0], "Passw0rd!")
        send_success.assert_called_once()
        call_args = send_success.call_args
        self.assertEqual(call_args.args[0], "student@example.com")
        self.assertEqual(call_args.kwargs["lang"], "ja")
        self.assertEqual(call_args.kwargs["change_source"], "reset")
        self.assertEqual(call_args.kwargs["login_context"]["device_info"], "Windows · Chrome")

    def test_change_password_sends_success_notification(self):
        current_hash = get_password_hash("OldPassw0rd!")
        updated_password_hashes = []

        def handler(query, params):
            if "SELECT password_hash, email FROM users WHERE user_id::text = %s" in query:
                return {"fetchone": (current_hash, "student@example.com")}
            if "UPDATE users SET password_hash = %s WHERE user_id::text = %s" in query:
                updated_password_hashes.append(params[0])
                return {}
            return {}

        fake_db = FakeConnection(handler)
        main.app.dependency_overrides[auth.get_db] = lambda: fake_db

        with patch.object(auth, "try_send_password_changed_email") as send_success:
            response = self.client.put(
                "/auth/change-password/11111111-1111-1111-1111-111111111111",
                json={
                    "current_password": "OldPassw0rd!",
                    "new_password": "NewPassw0rd!",
                },
                headers={
                    "X-Chilan-Interface-Language": "jp",
                    "accept-language": "en-US,en;q=0.9",
                    "x-forwarded-for": "203.0.113.7",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/138.0 Safari/537.36",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertGreaterEqual(fake_db.commit_calls, 1)
        self.assertEqual(len(updated_password_hashes), 1)
        self.assertNotEqual(updated_password_hashes[0], "NewPassw0rd!")
        send_success.assert_called_once()
        call_args = send_success.call_args
        self.assertEqual(call_args.args[0], "student@example.com")
        self.assertEqual(call_args.kwargs["lang"], "ja")
        self.assertEqual(call_args.kwargs["change_source"], "change")
        self.assertEqual(call_args.kwargs["login_context"]["device_info"], "Windows · Chrome")

    def test_change_password_still_succeeds_when_notification_email_fails(self):
        current_hash = get_password_hash("OldPassw0rd!")

        def handler(query, params):
            if "SELECT password_hash, email FROM users WHERE user_id::text = %s" in query:
                return {"fetchone": (current_hash, "student@example.com")}
            return {}

        fake_db = FakeConnection(handler)
        main.app.dependency_overrides[auth.get_db] = lambda: fake_db

        with patch.object(auth, "send_auth_email", side_effect=RuntimeError("mail down")):
            response = self.client.put(
                "/auth/change-password/11111111-1111-1111-1111-111111111111",
                json={
                    "current_password": "OldPassw0rd!",
                    "new_password": "NewPassw0rd!",
                },
                headers={
                    "X-Chilan-Interface-Language": "jp",
                    "accept-language": "en-US,en;q=0.9",
                    "x-forwarded-for": "203.0.113.7",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/138.0 Safari/537.36",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")


if __name__ == "__main__":
    unittest.main()
