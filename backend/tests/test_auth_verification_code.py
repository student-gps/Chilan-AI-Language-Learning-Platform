import unittest
from datetime import datetime, timezone, timedelta

from .test_helpers import FakeConnection, SmokeTestCaseMixin, auth, main


class AuthVerificationCodeSmokeTests(SmokeTestCaseMixin, unittest.TestCase):
    def test_verify_accepts_fresh_code(self):
        created_at = datetime.now(timezone.utc) - timedelta(minutes=2)

        def handler(query, params):
            if "SELECT code, created_at FROM verification_codes WHERE email = %s" in query:
                return {"fetchone": ("123456", created_at)}
            return {}

        fake_db = FakeConnection(handler)
        main.app.dependency_overrides[auth.get_db] = lambda: fake_db

        response = self.client.post(
            "/auth/verify",
            json={"email": "student@example.com", "code": "123456"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertGreaterEqual(fake_db.commit_calls, 1)
        self.assertTrue(any("DELETE FROM verification_codes WHERE email = %s" in query for query, _ in fake_db.executed_queries))

    def test_verify_rejects_expired_code_and_cleans_it_up_in_japanese(self):
        created_at = datetime.now(timezone.utc) - timedelta(minutes=11)

        def handler(query, params):
            if "SELECT code, created_at FROM verification_codes WHERE email = %s" in query:
                return {"fetchone": ("123456", created_at)}
            return {}

        fake_db = FakeConnection(handler)
        main.app.dependency_overrides[auth.get_db] = lambda: fake_db

        response = self.client.post(
            "/auth/verify",
            json={"email": "student@example.com", "code": "123456"},
            headers={"X-Chilan-Interface-Language": "jp"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("有効期限", response.json()["detail"])
        self.assertEqual(fake_db.commit_calls, 1)
        self.assertTrue(any("DELETE FROM verification_codes WHERE email = %s" in query for query, _ in fake_db.executed_queries))

    def test_verify_rejects_invalid_code_in_french(self):
        created_at = datetime.now(timezone.utc) - timedelta(minutes=2)

        def handler(query, params):
            if "SELECT code, created_at FROM verification_codes WHERE email = %s" in query:
                return {"fetchone": ("654321", created_at)}
            return {}

        fake_db = FakeConnection(handler)
        main.app.dependency_overrides[auth.get_db] = lambda: fake_db

        response = self.client.post(
            "/auth/verify",
            json={"email": "student@example.com", "code": "123456"},
            headers={"X-Chilan-Interface-Language": "fr"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("invalide", response.json()["detail"].lower())
        self.assertEqual(fake_db.commit_calls, 0)


if __name__ == "__main__":
    unittest.main()
