import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


# Minimal dependency shims so importing backend.main does not require the full
# backend runtime stack in this smoke-test environment.
if "psycopg2" not in sys.modules:
    psycopg2_pkg = types.ModuleType("psycopg2")

    class _FakeCursor:
        def execute(self, *args, **kwargs):  # noqa: ARG002
            return None

        def fetchone(self):
            return None

        def fetchall(self):
            return []

        def close(self):
            return None

    class _FakeConnection:
        closed = False

        def cursor(self, *args, **kwargs):  # noqa: ARG002
            return _FakeCursor()

        def commit(self):
            return None

        def rollback(self):
            return None

        def close(self):
            self.closed = True

    psycopg2_pkg.connect = lambda *args, **kwargs: _FakeConnection()
    psycopg2_extras = types.ModuleType("psycopg2.extras")
    psycopg2_extras.RealDictCursor = object
    psycopg2_pool = types.ModuleType("psycopg2.pool")

    class _FakeThreadedConnectionPool:
        def __init__(self, *args, **kwargs):  # noqa: ARG002
            pass

        def getconn(self):
            return _FakeConnection()

        def putconn(self, conn):  # noqa: ARG002
            return None

    psycopg2_pool.ThreadedConnectionPool = _FakeThreadedConnectionPool
    psycopg2_pkg.extras = psycopg2_extras
    psycopg2_pkg.pool = psycopg2_pool
    sys.modules["psycopg2"] = psycopg2_pkg
    sys.modules["psycopg2.extras"] = psycopg2_extras
    sys.modules["psycopg2.pool"] = psycopg2_pool

if "jwt" not in sys.modules:
    jwt_mod = types.ModuleType("jwt")
    jwt_mod.PyJWKClient = object
    sys.modules["jwt"] = jwt_mod

if "google" not in sys.modules:
    google_pkg = types.ModuleType("google")
    google_pkg.__path__ = []
    google_genai_mod = types.ModuleType("google.genai")
    google_genai_types_mod = types.ModuleType("google.genai.types")

    class _FakeGenerateContentConfig:
        def __init__(self, *args, **kwargs):  # noqa: ARG002
            pass

    class _FakeGenAIClient:
        def __init__(self, *args, **kwargs):  # noqa: ARG002
            self.models = types.SimpleNamespace(
                generate_content_stream=lambda *a, **k: [],
                embed_content=lambda *a, **k: types.SimpleNamespace(
                    embeddings=[types.SimpleNamespace(values=[0.0])]
                ),
            )

    google_genai_mod.Client = _FakeGenAIClient
    google_genai_mod.types = google_genai_types_mod
    google_genai_types_mod.GenerateContentConfig = _FakeGenerateContentConfig
    google_pkg.genai = google_genai_mod
    sys.modules["google"] = google_pkg
    sys.modules["google.genai"] = google_genai_mod
    sys.modules["google.generativeai"] = types.ModuleType("google.generativeai")

if "openai" not in sys.modules:
    openai_mod = types.ModuleType("openai")

    class _FakeOpenAI:
        def __init__(self, *args, **kwargs):  # noqa: ARG002
            self.audio = types.SimpleNamespace(
                transcriptions=types.SimpleNamespace(
                    create=lambda **kw: types.SimpleNamespace(text="test transcript")
                )
            )

    openai_mod.OpenAI = _FakeOpenAI
    sys.modules["openai"] = openai_mod

if "edge_tts" not in sys.modules:
    sys.modules["edge_tts"] = types.ModuleType("edge_tts")

from .test_helpers import SmokeTestCaseMixin, main  # noqa: E402


class _FakeMediaPipeline:
    def __init__(self, pipeline_id: str, root: Path, target_language: str, display_name: str):
        self.pipeline_id = pipeline_id
        self._root = root
        self.target_language = target_language
        self.display_name = display_name

    def artifact_root(self, backend_dir: Path) -> Path:  # noqa: ARG002
        return self._root


class MediaArtifactRoutesSmokeTests(SmokeTestCaseMixin, unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(self._make_tempdir())
        self.backend_root = self.tempdir / "backend"
        self.backend_root.mkdir(parents=True, exist_ok=True)
        self.zh_root = self.backend_root / "content_builder" / "zh" / "integrated_chinese" / "artifacts"
        self.ja_root = self.backend_root / "content_builder" / "ja" / "minna_no_nihongo" / "artifacts"

        self.fake_pipelines = {
            "integrated_chinese": _FakeMediaPipeline(
                "integrated_chinese", self.zh_root, "zh", "Integrated Chinese"
            ),
            "minna_no_nihongo": _FakeMediaPipeline(
                "minna_no_nihongo", self.ja_root, "ja", "Minna no Nihongo"
            ),
        }

        def fake_media_pipeline(pipeline_id: str):
            pipeline = self.fake_pipelines.get(pipeline_id)
            if pipeline:
                return pipeline
            raise main.HTTPException(status_code=404, detail=f"Unknown media pipeline: {pipeline_id}")

        self._backend_dir_patcher = patch.object(main, "_BACKEND_DIR", self.backend_root)
        self._storage_patcher = patch.object(main, "_pinyin_storage", None)
        self._media_pipeline_patcher = patch.object(main, "get_media_pipeline", side_effect=fake_media_pipeline)
        self._media_pipeline_list_patcher = patch.object(
            main, "list_media_pipelines", return_value=tuple(self.fake_pipelines.values())
        )
        self._backend_dir_patcher.start()
        self._storage_patcher.start()
        self._media_pipeline_patcher.start()
        self._media_pipeline_list_patcher.start()

    def tearDown(self):
        self._media_pipeline_list_patcher.stop()
        self._media_pipeline_patcher.stop()
        self._storage_patcher.stop()
        self._backend_dir_patcher.stop()
        self._cleanup_tempdir(self.tempdir)
        super().tearDown()

    def _make_tempdir(self) -> str:
        import tempfile
        return tempfile.mkdtemp(prefix="media-routes-")

    def _cleanup_tempdir(self, path: Path) -> None:
        import shutil
        shutil.rmtree(path, ignore_errors=True)

    def _write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(main.json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _write_bytes(self, path: Path, payload: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)

    def test_dev_lesson_artifact_preview_returns_chinese_top_level_deck(self):
        self._write_json(
            self.zh_root / "output_json" / "en" / "lesson101_data.json",
            {
                "lesson_metadata": {"lesson_id": 101, "title": "Lesson 101"},
                "teaching_slide_deck": {
                    "lang": "en",
                    "slide_count": 1,
                    "slides": [{"image": {"local_path": "slide_001.webp"}}],
                },
            },
        )

        response = self.client.get(
            "/dev/lesson-artifact-preview",
            params={"pipeline_id": "integrated_chinese", "lang": "en", "lesson_id": "101"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["pipeline_id"], "integrated_chinese")
        self.assertEqual(body["lang"], "en")
        self.assertEqual(body["lesson_id"], 101)
        self.assertEqual(body["lesson_slug"], "lesson101")
        self.assertEqual(body["teaching_slide_deck"]["lang"], "en")
        self.assertEqual(body["teaching_slide_deck"]["slide_count"], 1)
        self.assertEqual(
            body["artifact_path"].replace("\\", "/"),
            "content_builder/zh/integrated_chinese/artifacts/output_json/en/lesson101_data.json",
        )

    def test_dev_lesson_artifact_options_lists_generated_combinations(self):
        self._write_json(
            self.zh_root / "output_json" / "en" / "lesson101_data.json",
            {"lesson_metadata": {"lesson_id": 101}},
        )
        self._write_json(
            self.zh_root / "synced_json" / "en" / "lesson102_data.json",
            {"lesson_metadata": {"lesson_id": 102}},
        )
        self._write_json(
            self.ja_root / "output_json" / "zh" / "lesson001_data.json",
            {"lesson_metadata": {"lesson_id": 1}},
        )

        response = self.client.get("/dev/lesson-artifact-options")

        self.assertEqual(response.status_code, 200)
        pipelines = {item["pipeline_id"]: item for item in response.json()["pipelines"]}
        self.assertEqual(
            pipelines["integrated_chinese"]["languages"],
            [{"lang": "en", "lessons": ["101", "102"]}],
        )
        self.assertEqual(
            pipelines["minna_no_nihongo"]["languages"],
            [{"lang": "zh", "lessons": ["001"]}],
        )

    def test_dev_lesson_artifact_preview_returns_japanese_nested_explanation_deck(self):
        self._write_json(
            self.ja_root / "synced_json" / "zh" / "lesson001_data.json",
            {
                "lesson_metadata": {"lesson_id": 1, "title": "第1課"},
                "video_render_plan": {
                    "explanation": {
                        "teaching_slide_deck": {
                            "lang": "zh",
                            "slide_count": 1,
                            "slides": [{"image": {"local_path": "slide_001.png"}}],
                        }
                    }
                },
            },
        )

        response = self.client.get(
            "/dev/lesson-artifact-preview",
            params={"pipeline_id": "minna_no_nihongo", "lang": "zh", "lesson_id": "001"},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["pipeline_id"], "minna_no_nihongo")
        self.assertEqual(body["lang"], "zh")
        self.assertEqual(body["lesson_id"], 1)
        self.assertEqual(body["lesson_slug"], "lesson001")
        self.assertEqual(body["teaching_slide_deck"]["lang"], "zh")
        self.assertEqual(body["teaching_slide_deck"]["slide_count"], 1)
        self.assertEqual(
            body["artifact_path"].replace("\\", "/"),
            "content_builder/ja/minna_no_nihongo/artifacts/synced_json/zh/lesson001_data.json",
        )

    def test_dev_lesson_artifact_preview_returns_404_with_searched_paths(self):
        response = self.client.get(
            "/dev/lesson-artifact-preview",
            params={"pipeline_id": "integrated_chinese", "lang": "en", "lesson_id": "999"},
        )

        self.assertEqual(response.status_code, 404)
        detail = response.json()["detail"]
        self.assertEqual(detail["message"], "Lesson artifact not found")
        self.assertTrue(any("lesson999_data.json" in path for path in detail["searched"]))

    def test_get_teaching_slide_serves_local_chinese_png(self):
        expected = b"PNGDATA"
        self._write_bytes(
            self.zh_root / "output_slides" / "en" / "lesson101" / "slide_001.png",
            expected,
        )

        response = self.client.get("/media/teaching-slide/integrated_chinese/en/101/slide_001.png")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, expected)
        self.assertIn("image/png", response.headers.get("content-type", ""))

    def test_get_teaching_slide_serves_local_japanese_webp(self):
        expected = b"WEBP-JAPANESE"
        self._write_bytes(
            self.ja_root / "output_slides" / "zh" / "lesson001" / "slide_001.webp",
            expected,
        )

        response = self.client.get("/media/teaching-slide/minna_no_nihongo/zh/001/slide_001.webp")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, expected)
        self.assertIn("image/webp", response.headers.get("content-type", ""))

        expected = b"<svg xmlns='http://www.w3.org/2000/svg'></svg>"
        self._write_bytes(
            self.ja_root / "output_slides" / "zh" / "lesson001" / "slide_001.svg",
            expected,
        )

        response = self.client.get("/media/teaching-slide/minna_no_nihongo/zh/001/slide_001.svg")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, expected)
        self.assertIn("image/svg+xml", response.headers.get("content-type", ""))

    def test_get_teaching_audio_serves_local_chinese_new_style_mp3(self):
        expected = b"ID3-CHINESE"
        self._write_bytes(
            self.zh_root / "output_audio" / "en" / "lesson101_narration" / "lesson101_slide_001.mp3",
            expected,
        )

        response = self.client.get(
            "/media/teaching-audio/integrated_chinese/en/101/lesson101_slide_001.mp3"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, expected)
        self.assertIn("audio/mpeg", response.headers.get("content-type", ""))

    def test_get_teaching_audio_serves_local_japanese_legacy_style_mp3(self):
        expected = b"ID3-JAPANESE"
        self._write_bytes(
            self.ja_root / "output_audio" / "lesson001_narration_zh" / "lesson001_slide_001_zh.mp3",
            expected,
        )

        response = self.client.get(
            "/media/teaching-audio/minna_no_nihongo/zh/001/lesson001_slide_001_zh.mp3"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, expected)
        self.assertIn("audio/mpeg", response.headers.get("content-type", ""))

    def test_get_teaching_audio_returns_404_when_local_file_missing_and_storage_unavailable(self):
        response = self.client.get(
            "/media/teaching-audio/integrated_chinese/en/101/lesson101_slide_999.mp3"
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn("not found locally and storage not configured", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
