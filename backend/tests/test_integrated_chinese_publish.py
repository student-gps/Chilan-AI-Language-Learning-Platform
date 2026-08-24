import contextlib
import io
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
for path in (BACKEND_DIR, BACKEND_DIR / "content_builder"):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.append(path_str)

# Minimal shims for optional runtime deps so the publish wrapper can be imported.
if "google" not in sys.modules:
    google_pkg = types.ModuleType("google")
    google_pkg.__path__ = []
    sys.modules["google"] = google_pkg

if "google.genai" not in sys.modules:
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
    sys.modules["google.genai"] = google_genai_mod

if "google.generativeai" not in sys.modules:
    google_generativeai_mod = types.ModuleType("google.generativeai")
    google_generativeai_mod.configure = lambda *args, **kwargs: None
    google_generativeai_mod.embed_content = lambda *args, **kwargs: {"embedding": [0.0]}
    sys.modules["google.generativeai"] = google_generativeai_mod

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

if "jwt" not in sys.modules:
    jwt_mod = types.ModuleType("jwt")
    jwt_mod.PyJWKClient = object
    sys.modules["jwt"] = jwt_mod

if "psycopg2" not in sys.modules:
    psycopg2_pkg = types.ModuleType("psycopg2")
    psycopg2_extras = types.ModuleType("psycopg2.extras")
    psycopg2_pool = types.ModuleType("psycopg2.pool")
    psycopg2_extras.RealDictCursor = object
    psycopg2_pkg.connect = lambda *args, **kwargs: None

    class _FakeThreadedConnectionPool:
        def __init__(self, *args, **kwargs):  # noqa: ARG002
            pass

        def getconn(self):
            return None

        def putconn(self, conn):  # noqa: ARG002
            return None

    psycopg2_pool.ThreadedConnectionPool = _FakeThreadedConnectionPool
    psycopg2_pkg.extras = psycopg2_extras
    psycopg2_pkg.pool = psycopg2_pool
    sys.modules["psycopg2"] = psycopg2_pkg
    sys.modules["psycopg2.extras"] = psycopg2_extras
    sys.modules["psycopg2.pool"] = psycopg2_pool

if "json_repair" not in sys.modules:
    json_repair_mod = types.ModuleType("json_repair")
    json_repair_mod.repair_json = lambda text, **kwargs: text  # noqa: ARG005
    sys.modules["json_repair"] = json_repair_mod

if "edge_tts" not in sys.modules:
    sys.modules["edge_tts"] = types.ModuleType("edge_tts")

from content_builder.zh.integrated_chinese.scripts import run_language_pipeline as publish_script  # noqa: E402


class _FakePipeline:
    pipeline_id = "integrated_chinese"
    display_name = "Integrated Chinese"

    def __init__(self, root: Path):
        self.root = root

    def output_json_dir(self, paths, lang: str):  # noqa: ARG002
        return self.root / "output_json" / lang

    def synced_json_dir(self, paths, lang: str):  # noqa: ARG002
        return self.root / "synced_json" / lang


class IntegratedChinesePublishScriptTests(unittest.TestCase):
    def test_expected_outputs_prefers_output_json_and_respects_reuse_synced(self):
        tmpdir = Path(self._make_tempdir())
        artifact_root = tmpdir / "artifacts"
        out_dir = artifact_root / "output_json" / "fr"
        synced_dir = artifact_root / "synced_json" / "fr"
        out_dir.mkdir(parents=True, exist_ok=True)
        synced_dir.mkdir(parents=True, exist_ok=True)
        output_file = out_dir / "lesson101_data_fr.json"
        synced_file = synced_dir / "lesson102_data_fr.json"
        output_file.write_text("{}", encoding="utf-8")
        synced_file.write_text("{}", encoding="utf-8")

        args = types.SimpleNamespace(
            pipeline="integrated_chinese",
            lang="fr",
            lesson=None,
            files=[],
            reuse_localized_json=True,
        )

        with patch.object(publish_script, "default_paths", return_value=types.SimpleNamespace()), patch.object(
            publish_script, "get_pipeline", return_value=_FakePipeline(artifact_root)
        ):
            outputs = publish_script._expected_outputs(args)

        self.assertEqual(outputs, [output_file, synced_file])

    def test_expected_outputs_uses_synced_when_reuse_localized_json_enabled_for_specific_lesson(self):
        tmpdir = Path(self._make_tempdir())
        artifact_root = tmpdir / "artifacts"
        synced_dir = artifact_root / "synced_json" / "fr"
        synced_dir.mkdir(parents=True, exist_ok=True)
        synced_file = synced_dir / "lesson101_data_fr.json"
        synced_file.write_text("{}", encoding="utf-8")

        args = types.SimpleNamespace(
            pipeline="integrated_chinese",
            lang="fr",
            lesson="101",
            files=[],
            reuse_localized_json=True,
        )

        with patch.object(publish_script, "default_paths", return_value=types.SimpleNamespace()), patch.object(
            publish_script, "get_pipeline", return_value=_FakePipeline(artifact_root)
        ):
            outputs = publish_script._expected_outputs(args)

        self.assertEqual(outputs, [synced_file])

    def test_validate_outputs_passes_for_valid_localized_payload(self):
        tmpdir = Path(self._make_tempdir())
        image_path = tmpdir / "slide_001.webp"
        audio_path = tmpdir / "lesson101_slide_001.mp3"
        narration_path = tmpdir / "lesson101_narration_fr.mp3"
        image_path.write_bytes(b"WEBP")
        audio_path.write_bytes(b"ID3")
        narration_path.write_bytes(b"ID3")
        json_path = tmpdir / "lesson101_data_fr.json"
        json_path.write_text(
            publish_script.json.dumps(
                {
                    "explanation_narration_audio": {
                        "status": "ok",
                        "audio_file": str(narration_path),
                    },
                    "video_render_plan": {
                        "explanation": {
                            "segments": [
                                {
                                    "sentence_texts": ["Bonjour."],
                                    "sentence_timings_seconds": [0.0],
                                }
                            ]
                        }
                    },
                    "teaching_slide_deck": {
                        "render_version": publish_script.SLIDE_RENDER_VERSION,
                        "lang": "fr",
                        "slide_count": 1,
                        "slides": [
                            {
                                "image": {"local_path": str(image_path)},
                                "audio": {"local_path": str(audio_path)},
                            }
                        ],
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        publish_script._validate_outputs([json_path], "fr")

        payload = publish_script.json.loads(json_path.read_text(encoding="utf-8"))
        payload["teaching_slide_deck"]["render_version"] = "1-caption-baked-into-image"
        json_path.write_text(publish_script.json.dumps(payload), encoding="utf-8")
        errors = publish_script._validate_file(json_path, "fr")
        self.assertTrue(any("teaching_slide_deck.render_version" in error for error in errors))

    def test_validate_outputs_raises_on_missing_narration_audio(self):
        tmpdir = Path(self._make_tempdir())
        json_path = tmpdir / "lesson101_data_fr.json"
        json_path.write_text(
            publish_script.json.dumps(
                {
                    "explanation_narration_audio": {
                        "status": "ok",
                        "audio_file": str(tmpdir / "missing.mp3"),
                    },
                    "video_render_plan": {"explanation": {"segments": []}},
                    "teaching_slide_deck": {"lang": "fr", "slide_count": 0, "slides": []},
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        with self.assertRaises(SystemExit) as ctx:
            publish_script._validate_outputs([json_path], "fr")
        self.assertEqual(ctx.exception.code, 1)

    def test_run_step_dry_run_does_not_call_subprocess(self):
        with patch.object(publish_script.subprocess, "run") as run_mock:
            publish_script._run_step("dry-run", ["python", "dummy.py"], dry_run=True)
        run_mock.assert_not_called()

    def test_run_step_raises_on_nonzero_exit(self):
        with patch.object(
            publish_script.subprocess,
            "run",
            return_value=types.SimpleNamespace(returncode=3),
        ):
            with self.assertRaises(SystemExit) as ctx:
                publish_script._run_step("failing-step", ["python", "dummy.py"], dry_run=False)
        self.assertIn("failing-step failed with exit code 3", str(ctx.exception))

    def test_main_reuse_localized_json_skips_localize_and_stops_before_sync(self):
        tmpdir = Path(self._make_tempdir())
        target = tmpdir / "lesson101_data_fr.json"
        target.write_text("{}", encoding="utf-8")

        argv = [
            "run_language_pipeline.py",
            "--lang",
            "fr",
            "--reuse-localized-json",
            "--reuse-narration",
            "--reuse-slides",
            "--skip-sync",
        ]

        run_calls = []
        validate_calls = []

        def fake_run_step(label, command, dry_run=False):
            run_calls.append((label, list(command), dry_run))

        with patch.object(sys, "argv", argv), patch.object(publish_script, "_ensure_tts_env", return_value=None), patch.object(
            publish_script, "_expected_outputs", return_value=[target]
        ), patch.object(publish_script, "_run_step", side_effect=fake_run_step), patch.object(
            publish_script, "_validate_outputs", side_effect=lambda files, lang: validate_calls.append((list(files), lang))
        ):
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                publish_script.main()

        output = buffer.getvalue()
        self.assertIn("Skipping localize.py", output)
        self.assertIn("Stopped before DB sync because --skip-sync was set.", output)
        self.assertEqual(len(run_calls), 1)
        self.assertEqual(run_calls[0][0], "Stage 2: render narration and slide deck")
        self.assertIn("--pipeline", run_calls[0][1])
        self.assertEqual(validate_calls, [([target], "fr")])

    def _make_tempdir(self) -> str:
        import tempfile

        return tempfile.mkdtemp(prefix="zh-publish-")


if __name__ == "__main__":
    unittest.main()
