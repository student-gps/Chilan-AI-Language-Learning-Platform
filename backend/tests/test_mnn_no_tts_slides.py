from __future__ import annotations

import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
for path in (BACKEND_DIR, BACKEND_DIR / "content_builder"):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.append(path_str)

from content_builder.ja.minna_no_nihongo.scripts import build_teaching_slide_deck as deck_script
from content_builder.ja.minna_no_nihongo.scripts import render_narration as narration_script


class _FakePipeline:
    pipeline_id = "minna_no_nihongo"
    target_language = "ja"

    def __init__(self, artifact_root: Path):
        self._artifact_root = artifact_root

    def artifact_root(self, paths):  # noqa: ARG002
        return self._artifact_root


class MnnNoTtsSlidesTests(unittest.TestCase):
    def test_build_deck_without_audio_writes_captioned_deck_and_removes_old_audio(self):
        tmpdir = Path(tempfile.mkdtemp(prefix="mnn-no-tts-"))
        artifact_root = tmpdir / "artifacts"
        json_path = tmpdir / "lesson001_data.json"
        json_path.write_text(json.dumps({
            "lesson_metadata": {"lesson_id": 1, "title": "第1课"},
            "video_render_plan": {
                "explanation": {
                    "segments": [{
                        "segment_id": 1,
                        "segment_title": "句型",
                        "duration_seconds": 6,
                        "narration_track": {"subtitle_zh": "这是第一句。 这是第二句。"},
                        "visual_blocks": [],
                    }]
                }
            },
        }, ensure_ascii=False), encoding="utf-8")

        slide_dir = artifact_root / "output_slides" / "zh" / "lesson001"
        narration_dir = artifact_root / "output_audio" / "zh" / "lesson001_narration"
        narration_dir.mkdir(parents=True, exist_ok=True)
        (narration_dir / "lesson001_slide_001_zh.mp3").write_bytes(b"OLD")

        with patch.object(deck_script, "default_paths", return_value=types.SimpleNamespace(backend_dir=tmpdir, project_root=tmpdir)), patch.object(
            deck_script, "get_pipeline", return_value=_FakePipeline(artifact_root)
        ), patch.object(deck_script, "load_dotenv", return_value=None), patch.object(
            deck_script, "_split_narration_audio"
        ) as split_mock:
            deck = deck_script.build_deck(
                json_path,
                pipeline_id="minna_no_nihongo",
                lang="zh",
                force=True,
                renderer="svg",
                include_audio=False,
            )

        split_mock.assert_not_called()
        self.assertEqual(deck["audio_mode"], "none")
        self.assertTrue(deck["captions_required"])
        self.assertNotIn("audio", deck["slides"][0])
        self.assertEqual(len(deck["slides"][0]["caption_cues"]), 2)
        image_content = Path(deck["slides"][0]["image"]["local_path"]).read_text(encoding="utf-8")
        self.assertIn("这是第一句", image_content)
        self.assertFalse((narration_dir / "lesson001_slide_001_zh.mp3").exists())

        persisted = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(persisted["teaching_slide_deck"]["audio_mode"], "none")
        self.assertNotIn("audio", persisted["teaching_slide_deck"]["slides"][0])

    def test_existing_png_deck_converts_to_webp_without_remotion(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow is required for WebP conversion")

        tmpdir = Path(tempfile.mkdtemp(prefix="mnn-webp-"))
        artifact_root = tmpdir / "artifacts"
        json_path = tmpdir / "lesson001_data.json"
        json_path.write_text(json.dumps({
            "lesson_metadata": {"lesson_id": 1, "title": "第1课"},
            "video_render_plan": {"explanation": {"segments": [{
                "segment_id": 1,
                "duration_seconds": 5,
                "narration_track": {"subtitle_zh": "讲解字幕。"},
                "visual_blocks": [],
            }]}},
        }, ensure_ascii=False), encoding="utf-8")
        slide_dir = artifact_root / "output_slides" / "zh" / "lesson001"
        slide_dir.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (12, 12), color=(12, 80, 160)).save(slide_dir / "slide_001.png", "PNG")

        with patch.object(deck_script, "default_paths", return_value=types.SimpleNamespace(backend_dir=tmpdir, project_root=tmpdir)), patch.object(
            deck_script, "get_pipeline", return_value=_FakePipeline(artifact_root)
        ), patch.object(deck_script, "load_dotenv", return_value=None), patch.object(
            deck_script, "detect_image_suffix", wraps=deck_script.detect_image_suffix
        ) as suffix_mock, patch.object(
            deck_script, "_render_remotion_slides"
        ) as render_mock, patch.object(
            deck_script, "_convert_pngs_to_webp", wraps=deck_script._convert_pngs_to_webp
        ) as convert_mock:
            deck = deck_script.build_deck(
                json_path,
                pipeline_id="minna_no_nihongo",
                lang="zh",
                force=False,
                renderer="remotion",
                include_audio=False,
            )

        render_mock.assert_not_called()
        self.assertEqual(suffix_mock.call_args_list[0].args, (slide_dir, [1]))
        self.assertEqual(suffix_mock.call_args_list[0].kwargs, {"prefer_webp": True})
        convert_mock.assert_called_once_with(slide_dir, [1])
        self.assertTrue((slide_dir / "slide_001.webp").exists(), list(slide_dir.glob("*")))
        self.assertFalse((slide_dir / "slide_001.png").exists())
        self.assertTrue(deck["slides"][0]["image"]["local_path"].endswith(".webp"))
        self.assertTrue(deck["slides"][0]["image"]["object_key"].endswith(".webp"))
        self.assertTrue(deck["slides"][0]["image"]["media_path"].endswith(".webp"))

        tmpdir = Path(tempfile.mkdtemp(prefix="mnn-no-tts-"))
        artifact_root = tmpdir / "artifacts"
        json_path = tmpdir / "lesson001_data.json"
        json_path.write_text(json.dumps({
            "lesson_metadata": {"lesson_id": 1},
            "video_render_plan": {"explanation": {"segments": [{"duration_seconds": 6, "visual_blocks": []}]}},
        }), encoding="utf-8")

        with patch.object(deck_script, "default_paths", return_value=types.SimpleNamespace(backend_dir=tmpdir, project_root=tmpdir)), patch.object(
            deck_script, "get_pipeline", return_value=_FakePipeline(artifact_root)
        ), patch.object(deck_script, "load_dotenv", return_value=None):
            with self.assertRaisesRegex(ValueError, "no narration text"):
                deck_script.build_deck(json_path, renderer="svg", include_audio=False)

    def test_render_narration_skip_tts_never_calls_narrator(self):
        tmpdir = Path(tempfile.mkdtemp(prefix="mnn-no-tts-"))
        json_path = tmpdir / "lesson001_data.json"
        json_path.write_text(json.dumps({
            "video_render_plan": {
                "explanation": {
                    "segments": [{
                        "segment_id": 1,
                        "duration_seconds": 4,
                        "narration_track": {"subtitle_zh": "字幕。"},
                    }]
                }
            }
        }, ensure_ascii=False), encoding="utf-8")

        class _FailIfCalled:
            def render_narration(self, *args, **kwargs):  # noqa: ARG002
                raise AssertionError("TTS narrator must not run")

        captured = {}

        def fake_build_deck(path, **kwargs):
            captured["path"] = path
            captured.update(kwargs)
            return {"slide_count": 1, "audio_mode": "none"}

        with patch.object(narration_script, "build_deck", side_effect=fake_build_deck):
            ok = narration_script.process_file(
                _FailIfCalled(),
                json_path,
                lang="zh",
                pipeline_id="minna_no_nihongo",
                force_slides=True,
                skip_tts=True,
            )

        self.assertTrue(ok)
        self.assertFalse(captured["include_audio"])
        persisted = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertEqual(persisted["explanation_narration_audio"], {"status": "skipped", "reason": "tts_disabled"})


if __name__ == "__main__":
    unittest.main()
