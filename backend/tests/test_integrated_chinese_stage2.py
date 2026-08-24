import json
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

# Minimal shims so importing the Stage 2 scripts does not require optional runtime deps.
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

if "json_repair" not in sys.modules:
    json_repair_mod = types.ModuleType("json_repair")
    json_repair_mod.repair_json = lambda text, **kwargs: text  # noqa: ARG005
    sys.modules["json_repair"] = json_repair_mod

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

if "edge_tts" not in sys.modules:
    sys.modules["edge_tts"] = types.ModuleType("edge_tts")

from content_builder.zh.integrated_chinese.scripts import build_teaching_slide_deck as deck_script  # noqa: E402
from content_builder.zh.integrated_chinese.scripts import render_narration as narration_script  # noqa: E402


class ChineseStage2RegressionTests(unittest.TestCase):
    def test_merge_legacy_duplicate_segments_merges_and_rebuilds_timeline(self):
        lesson_data = {
            "video_render_plan": {
                "explanation": {
                    "segments": [
                        {
                            "segment_id": 1,
                            "segment_order": 1,
                            "duration_seconds": 5,
                            "narration_track": {"subtitle_en": "Hello there."},
                            "visual_blocks": [
                                {
                                    "block_type": "hero_line",
                                    "content": {
                                        "focus_text": "你好",
                                        "focus_pinyin": "nǐ hǎo",
                                        "focus_gloss_en": "hello",
                                    },
                                }
                            ],
                        },
                        {
                            "segment_id": 1,
                            "segment_order": 1,
                            "duration_seconds": 7,
                            "narration_track": {"subtitle_en": "Hello there."},
                            "visual_blocks": [
                                {
                                    "block_type": "hero_line",
                                    "content": {
                                        "focus_text": "！",
                                        "focus_pinyin": "",
                                        "focus_gloss_en": "!",
                                    },
                                }
                            ],
                        },
                    ],
                    "timeline": {},
                }
            }
        }

        merged = narration_script._merge_legacy_duplicate_segments(lesson_data)

        self.assertEqual(merged, 1)
        segments = lesson_data["video_render_plan"]["explanation"]["segments"]
        self.assertEqual(len(segments), 1)
        hero = segments[0]["visual_blocks"][0]["content"]
        self.assertEqual(hero["focus_text"], "你好！")
        self.assertEqual(hero["focus_gloss_en"], "hello !")
        self.assertEqual(segments[0]["duration_seconds"], 7)
        self.assertEqual(segments[0]["start_time_seconds"], 0.0)
        self.assertEqual(segments[0]["end_time_seconds"], 7.0)
        self.assertEqual(
            lesson_data["video_render_plan"]["explanation"]["timeline"]["total_duration_seconds"],
            7.0,
        )

    def test_process_file_reuses_existing_narration_and_updates_json_before_building_deck(self):
        tmpdir = Path(self._make_tempdir())
        json_path = tmpdir / "lesson101_data.json"
        json_path.write_text(
            json.dumps(
                {
                    "video_render_plan": {
                        "explanation": {
                            "segments": [
                                {
                                    "segment_id": 1,
                                    "segment_order": 1,
                                    "duration_seconds": 4,
                                    "narration_track": {"subtitle_en": "Hello."},
                                }
                            ],
                            "timeline": {},
                        }
                    },
                    "explanation_narration_audio": {
                        "status": "pending",
                        "audio_file": "",
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        artifact_root = tmpdir / "artifacts"
        expected_narration = artifact_root / "output_audio" / "en" / "lesson101_narration" / "lesson101_narration.mp3"
        expected_narration.parent.mkdir(parents=True, exist_ok=True)
        expected_narration.write_bytes(b"ID3")

        class _FakeAgent:
            def __init__(self):
                self.calls = 0

            def render_narration(self, lesson_data, lesson_id, lang="en"):  # noqa: ARG002
                self.calls += 1
                lesson_data["explanation_narration_audio"] = {"status": "error"}

        fake_agent = _FakeAgent()

        captured = {}

        def fake_build_deck(path, pipeline_id, lang, force=False):
            captured["path"] = Path(path)
            captured["pipeline_id"] = pipeline_id
            captured["lang"] = lang
            captured["force"] = force
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            captured["payload"] = payload
            return {"slide_count": 1}

        with patch.object(narration_script, "ARTIFACTS_DIR", artifact_root), patch.object(
            narration_script, "build_deck", side_effect=fake_build_deck
        ):
            ok = narration_script.process_file(
                fake_agent,
                json_path,
                lang="en",
                pipeline_id="integrated_chinese",
                force_narration=False,
                force_slides=True,
            )

        self.assertTrue(ok)
        self.assertEqual(fake_agent.calls, 0)
        self.assertEqual(captured["pipeline_id"], "integrated_chinese")
        self.assertEqual(captured["lang"], "en")
        self.assertTrue(captured["force"])
        self.assertEqual(
            captured["payload"]["explanation_narration_audio"]["audio_file"],
            str(expected_narration),
        )
        self.assertEqual(captured["payload"]["video_render_plan"]["explanation"]["timeline"]["total_duration_seconds"], 4.0)

    def test_process_file_skips_deck_when_narration_fails(self):
        tmpdir = Path(self._make_tempdir())
        json_path = tmpdir / "lesson101_data.json"
        json_path.write_text(
            json.dumps(
                {
                    "video_render_plan": {
                        "explanation": {
                            "segments": [
                                {
                                    "segment_id": 1,
                                    "duration_seconds": 4,
                                    "narration_track": {"subtitle_en": "Hello."},
                                }
                            ],
                            "timeline": {},
                        }
                    }
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        class _FailingAgent:
            def render_narration(self, lesson_data, lesson_id, lang="en"):  # noqa: ARG002
                lesson_data["explanation_narration_audio"] = {"status": "error", "reason": "tts failed"}

        with patch.object(narration_script, "build_deck") as build_deck_mock:
            ok = narration_script.process_file(
                _FailingAgent(),
                json_path,
                lang="en",
                pipeline_id="integrated_chinese",
                force_narration=True,
                force_slides=False,
            )

        self.assertFalse(ok)
        build_deck_mock.assert_not_called()

    def test_build_deck_reuses_existing_webp_without_remotion(self):
        tmpdir = Path(self._make_tempdir())
        artifact_root = tmpdir / "artifacts"
        json_path = tmpdir / "lesson101_data.json"
        payload = {
            "lesson_metadata": {"lesson_id": 101, "title": "Lesson 101"},
            "video_render_plan": {
                "explanation": {
                    "segments": [
                        {
                            "segment_id": 1,
                            "segment_title": "Intro",
                            "duration_seconds": 4,
                            "start_time_seconds": 0,
                            "narration_track": {"subtitle_en": "Hello there."},
                            "visual_blocks": [],
                        }
                    ],
                    "timeline": {"total_duration_seconds": 4, "segment_count": 1},
                }
            },
            "explanation_narration_audio": {
                "status": "ok",
                "audio_file": str(artifact_root / "output_audio" / "en" / "lesson101_narration" / "lesson101_narration.mp3"),
            },
        }
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        slide_dir = artifact_root / "output_slides" / "en" / "lesson101"
        slide_dir.mkdir(parents=True, exist_ok=True)
        (slide_dir / "slide_001.webp").write_bytes(b"WEBP")
        narration_dir = artifact_root / "output_audio" / "en" / "lesson101_narration"
        narration_dir.mkdir(parents=True, exist_ok=True)
        (narration_dir / "lesson101_narration.mp3").write_bytes(b"ID3")
        (narration_dir / "lesson101_slide_001.mp3").write_bytes(b"ID3-SLIDE")

        class _FakePipeline:
            pipeline_id = "integrated_chinese"
            target_language = "zh"

            def artifact_root(self, paths):  # noqa: ARG002
                return artifact_root

        with patch.object(deck_script, "default_paths", return_value=types.SimpleNamespace(backend_dir=tmpdir, project_root=tmpdir)), patch.object(
            deck_script, "get_pipeline", return_value=_FakePipeline()
        ), patch.object(deck_script, "load_dotenv", return_value=None), patch.object(
            deck_script, "_render_remotion_slides"
        ) as render_mock, patch.object(deck_script, "_convert_pngs_to_webp") as convert_mock, patch.object(
            deck_script, "_split_narration_audio", side_effect=lambda **kwargs: narration_dir / "lesson101_slide_001.mp3"
        ):
            deck = deck_script.build_deck(json_path, "integrated_chinese", "en", force=False, renderer="remotion")

        render_mock.assert_not_called()
        convert_mock.assert_not_called()
        self.assertEqual(deck["slide_count"], 1)
        self.assertEqual(deck["render_version"], deck_script.SLIDE_RENDER_VERSION)
        self.assertEqual(deck["slides"][0]["image"]["local_path"].endswith("slide_001.webp"), True)
        self.assertEqual(deck["slides"][0]["image"]["object_key"], "zh/slides/en/lesson101/slide_001.webp")
        persisted = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(persisted["teaching_slide_deck"]["slide_count"], 1)
        self.assertEqual(
            persisted["teaching_slide_deck"]["render_version"],
            deck_script.SLIDE_RENDER_VERSION,
        )

    def test_refresh_deck_images_preserves_slide_audio_and_cues(self):
        tmpdir = Path(self._make_tempdir())
        artifact_root = tmpdir / "artifacts"
        slide_dir = artifact_root / "output_slides" / "en" / "lesson101"
        audio_dir = artifact_root / "output_audio" / "en" / "lesson101_narration"
        slide_dir.mkdir(parents=True)
        audio_dir.mkdir(parents=True)
        old_image = slide_dir / "slide_001.webp"
        slide_audio = audio_dir / "lesson101_slide_001.mp3"
        old_image.write_bytes(b"old-captioned-image")
        slide_audio.write_bytes(b"existing-slide-audio")
        json_path = artifact_root / "output_json" / "en" / "lesson101_data.json"
        json_path.parent.mkdir(parents=True)
        original_audio = {
            "local_path": str(slide_audio),
            "object_key": "zh/audio/narration/en/lesson101/lesson101_slide_001.mp3",
            "media_path": "/media/teaching-audio/integrated_chinese/en/101/lesson101_slide_001.mp3",
            "media_url": "existing-audio-url",
            "start_ms": 0,
            "end_ms": 4000,
        }
        original_cues = [{"start_ms": 0, "end_ms": 4000, "text": "Existing cue."}]
        payload = {
            "lesson_metadata": {"lesson_id": 101, "title": "Lesson 101"},
            "video_render_plan": {
                "explanation": {
                    "segments": [{"segment_id": 1, "segment_title": "Greeting", "duration_seconds": 4}]
                }
            },
            "teaching_slide_deck": {
                "version": "1.0",
                "render_version": "1-caption-baked-into-image",
                "lang": "en",
                "slide_count": 1,
                "slides": [
                    {
                        "id": "seg_001",
                        "segment_id": 1,
                        "title": "Greeting",
                        "duration_ms": 4000,
                        "image": {"local_path": str(old_image)},
                        "audio": original_audio,
                        "caption_cues": original_cues,
                    }
                ],
            },
        }
        json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

        class _FakePipeline:
            pipeline_id = "integrated_chinese"
            target_language = "zh"

            def artifact_root(self, paths):  # noqa: ARG002
                return artifact_root

        def fake_render(**kwargs):
            (slide_dir / "slide_001.png").write_bytes(b"new-png")
            return slide_dir, ".png"

        def fake_convert(rendered_dir, indexes):
            self.assertEqual(indexes, [1])
            (rendered_dir / "slide_001.png").unlink()
            (rendered_dir / "slide_001.webp").write_bytes(b"new-un-captioned-image")
            return True

        with patch.object(
            deck_script,
            "default_paths",
            return_value=types.SimpleNamespace(backend_dir=tmpdir, project_root=tmpdir),
        ), patch.object(deck_script, "get_pipeline", return_value=_FakePipeline()), patch.object(
            deck_script, "load_dotenv", return_value=None
        ), patch.object(deck_script, "_render_remotion_slides", side_effect=fake_render), patch.object(
            deck_script, "_convert_pngs_to_webp", side_effect=fake_convert
        ):
            deck = deck_script.refresh_deck_images(
                json_path,
                "integrated_chinese",
                "en",
                force=True,
            )

        self.assertEqual(deck["render_version"], deck_script.SLIDE_RENDER_VERSION)
        self.assertEqual(deck["slides"][0]["audio"], original_audio)
        self.assertEqual(deck["slides"][0]["caption_cues"], original_cues)
        self.assertEqual(old_image.read_bytes(), b"new-un-captioned-image")
        persisted = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(persisted["teaching_slide_deck"]["render_version"], deck_script.SLIDE_RENDER_VERSION)

    def test_build_deck_falls_back_to_svg_when_remotion_fails(self):
        tmpdir = Path(self._make_tempdir())
        artifact_root = tmpdir / "artifacts"
        json_path = tmpdir / "lesson101_data.json"
        payload = {
            "lesson_metadata": {"lesson_id": 101, "title": "Lesson 101"},
            "video_render_plan": {
                "explanation": {
                    "segments": [
                        {
                            "segment_id": 1,
                            "segment_title": "Intro",
                            "duration_seconds": 4,
                            "start_time_seconds": 0,
                            "narration_track": {"subtitle_en": "Hello there."},
                            "visual_blocks": [],
                        }
                    ],
                    "timeline": {"total_duration_seconds": 4, "segment_count": 1},
                }
            },
            "explanation_narration_audio": {
                "status": "ok",
                "audio_file": str(artifact_root / "output_audio" / "en" / "lesson101_narration" / "lesson101_narration.mp3"),
            },
        }
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        narration_dir = artifact_root / "output_audio" / "en" / "lesson101_narration"
        narration_dir.mkdir(parents=True, exist_ok=True)
        (narration_dir / "lesson101_narration.mp3").write_bytes(b"ID3")
        (narration_dir / "lesson101_slide_001.mp3").write_bytes(b"ID3-SLIDE")

        class _FakePipeline:
            pipeline_id = "integrated_chinese"
            target_language = "zh"

            def artifact_root(self, paths):  # noqa: ARG002
                return artifact_root

        with patch.object(deck_script, "default_paths", return_value=types.SimpleNamespace(backend_dir=tmpdir, project_root=tmpdir)), patch.object(
            deck_script, "get_pipeline", return_value=_FakePipeline()
        ), patch.object(deck_script, "load_dotenv", return_value=None), patch.object(
            deck_script, "_render_remotion_slides", side_effect=RuntimeError("remotion failed")
        ), patch.object(deck_script, "_split_narration_audio", side_effect=lambda **kwargs: narration_dir / "lesson101_slide_001.mp3"):
            deck = deck_script.build_deck(json_path, "integrated_chinese", "en", force=True, renderer="remotion")

        self.assertEqual(deck["slide_count"], 1)
        image_path = Path(deck["slides"][0]["image"]["local_path"])
        self.assertEqual(image_path.suffix, ".svg")
        self.assertTrue(image_path.exists())
        persisted = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(persisted["teaching_slide_deck"]["slides"][0]["image"]["local_path"], str(image_path))

    def test_build_deck_only_slide_keeps_selected_slide_and_cleans_stale_assets(self):
        tmpdir = Path(self._make_tempdir())
        artifact_root = tmpdir / "artifacts"
        json_path = tmpdir / "lesson101_data.json"
        payload = {
            "lesson_metadata": {"lesson_id": 101, "title": "Lesson 101"},
            "video_render_plan": {
                "explanation": {
                    "segments": [
                        {
                            "segment_id": 1,
                            "segment_title": "Intro",
                            "duration_seconds": 4,
                            "start_time_seconds": 0,
                            "narration_track": {"subtitle_en": "Hello there."},
                            "visual_blocks": [],
                        },
                        {
                            "segment_id": 2,
                            "segment_title": "Second",
                            "duration_seconds": 5,
                            "start_time_seconds": 4,
                            "narration_track": {"subtitle_en": "Second slide."},
                            "visual_blocks": [],
                        },
                    ],
                    "timeline": {"total_duration_seconds": 9, "segment_count": 2},
                }
            },
            "explanation_narration_audio": {
                "status": "ok",
                "audio_file": str(artifact_root / "output_audio" / "en" / "lesson101_narration" / "lesson101_narration.mp3"),
            },
        }
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        slide_dir = artifact_root / "output_slides" / "en" / "lesson101"
        slide_dir.mkdir(parents=True, exist_ok=True)
        (slide_dir / "slide_001.webp").write_bytes(b"OLD1")
        (slide_dir / "slide_002.webp").write_bytes(b"KEEP2")
        (slide_dir / "slide_003.webp").write_bytes(b"OLD3")

        narration_dir = artifact_root / "output_audio" / "en" / "lesson101_narration"
        narration_dir.mkdir(parents=True, exist_ok=True)
        (narration_dir / "lesson101_narration.mp3").write_bytes(b"ID3")
        (narration_dir / "lesson101_slide_001.mp3").write_bytes(b"OLDA1")
        (narration_dir / "lesson101_slide_002.mp3").write_bytes(b"KEEPA2")
        (narration_dir / "lesson101_slide_003.mp3").write_bytes(b"OLDA3")

        class _FakePipeline:
            pipeline_id = "integrated_chinese"
            target_language = "zh"

            def artifact_root(self, paths):  # noqa: ARG002
                return artifact_root

        rendered_calls = []

        def fake_render_remotion_slides(**kwargs):
            rendered_calls.append(kwargs)
            (slide_dir / "slide_002.png").write_bytes(b"PNG2")
            return slide_dir, ".png"

        def fake_convert_pngs_to_webp(target_dir, indexes):
            for index in indexes:
                png = target_dir / f"slide_{index:03d}.png"
                if png.exists():
                    png.unlink()
                    (target_dir / f"slide_{index:03d}.webp").write_bytes(f"WEBP{index}".encode("utf-8"))

        with patch.object(deck_script, "default_paths", return_value=types.SimpleNamespace(backend_dir=tmpdir, project_root=tmpdir)), patch.object(
            deck_script, "get_pipeline", return_value=_FakePipeline()
        ), patch.object(deck_script, "load_dotenv", return_value=None), patch.object(
            deck_script, "_render_remotion_slides", side_effect=fake_render_remotion_slides
        ), patch.object(deck_script, "_convert_pngs_to_webp", side_effect=fake_convert_pngs_to_webp), patch.object(
            deck_script, "_split_narration_audio", side_effect=lambda **kwargs: narration_dir / f"lesson101_slide_{kwargs['slide_index']:03d}.mp3"
        ):
            deck = deck_script.build_deck(
                json_path,
                "integrated_chinese",
                "en",
                force=True,
                renderer="remotion",
                only_slide=2,
            )

        self.assertEqual(deck["slide_count"], 1)
        self.assertEqual(deck["slides"][0]["segment_id"], 2)
        self.assertEqual(rendered_calls[0]["only_slide"], 2)
        self.assertFalse((slide_dir / "slide_001.webp").exists())
        self.assertTrue((slide_dir / "slide_002.webp").exists())
        self.assertFalse((slide_dir / "slide_003.webp").exists())
        self.assertFalse((narration_dir / "lesson101_slide_001.mp3").exists())
        self.assertTrue((narration_dir / "lesson101_slide_002.mp3").exists())
        self.assertFalse((narration_dir / "lesson101_slide_003.mp3").exists())
        persisted = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(persisted["teaching_slide_deck"]["slide_count"], 1)
        self.assertEqual(persisted["teaching_slide_deck"]["slides"][0]["segment_id"], 2)

    def _make_tempdir(self) -> str:
        import tempfile

        return tempfile.mkdtemp(prefix="zh-stage2-")


if __name__ == "__main__":
    unittest.main()
