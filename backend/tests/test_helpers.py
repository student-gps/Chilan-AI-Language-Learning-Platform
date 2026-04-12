import sys
import types
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

try:
    import google.generativeai as _unused_google_genai  # noqa: F401
except Exception:
    google_pkg = types.ModuleType("google")
    google_genai_mod = types.ModuleType("google.generativeai")

    def _embed_content(*args, **kwargs):  # noqa: ARG001, ARG002
        return {"embedding": [0.0]}

    google_genai_mod.configure = lambda *args, **kwargs: None  # noqa: E731
    google_genai_mod.embed_content = _embed_content
    google_pkg.generativeai = google_genai_mod
    sys.modules["google"] = google_pkg
    sys.modules["google.generativeai"] = google_genai_mod

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from database.utils import get_password_hash  # noqa: E402
from routers import auth, study  # noqa: E402


class FakeCursor:
    def __init__(self, handler, executed_queries):
        self.handler = handler
        self.executed_queries = executed_queries
        self.fetchone_value = None
        self.fetchall_value = []

    def execute(self, query, params=None):
        self.executed_queries.append((query, params))
        result = self.handler(query, params) or {}
        self.fetchone_value = result.get("fetchone")
        self.fetchall_value = result.get("fetchall", [])

    def fetchone(self):
        return self.fetchone_value

    def fetchall(self):
        return self.fetchall_value

    def close(self):
        return None


class FakeConnection:
    def __init__(self, handler):
        self.handler = handler
        self.executed_queries = []
        self.commit_calls = 0
        self.rollback_calls = 0
        self.closed = False

    def cursor(self, *args, **kwargs):  # noqa: ARG002
        return FakeCursor(self.handler, self.executed_queries)

    def commit(self):
        self.commit_calls += 1

    def rollback(self):
        self.rollback_calls += 1

    def close(self):
        self.closed = True


class FakeGoogleResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload


class FakeGoogleAsyncClient:
    def __init__(self, *args, **kwargs):  # noqa: ARG002
        self.response = FakeGoogleResponse(
            {
                "email": "google-user@example.com",
                "name": "Google Learner",
            }
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):  # noqa: ARG002
        return False

    async def get(self, url, headers=None):  # noqa: ARG002
        return self.response


class FakeEvaluatorService:
    def get_speech_eval_config(self, config):
        return config or {}

    def check_exact(self, user_answer, standard_answers):
        return user_answer in standard_answers


class FakeScheduler:
    def calc_next_review(self, stability, difficulty, level):  # noqa: ARG002
        return 1.8, 3.2, "2030-01-01T00:00:00+00:00"

    def check_mastery(self, history):
        return bool(history and history[-1] >= 4)


class SmokeTestCaseMixin:
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(main.app)

    def tearDown(self):
        main.app.dependency_overrides.clear()
