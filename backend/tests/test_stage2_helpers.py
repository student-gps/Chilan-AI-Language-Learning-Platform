import sys
import types
import unittest
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
for path in (BACKEND_DIR, BACKEND_DIR / "content_builder"):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.append(path_str)

from content_builder.core.slide_asset_helpers import cleanup_stale_slide_assets, detect_image_suffix
from content_builder.core.stage2_helpers import (
    apply_reused_narration,
    expected_narration_path,
    normalize_explanation_timeline,
    recorded_audio_matches,
)


class Stage2HelpersTests(unittest.TestCase):
    def test_expected_narration_path_uses_zero_padded_lesson_slug(self):
        root = Path("artifacts")
        path = expected_narration_path(root, 1, "zh")
        self.assertEqual(
            path,
            Path("artifacts/output_audio/zh/lesson001_narration/lesson001_narration_zh.mp3"),
        )

    def test_recorded_audio_matches_requires_existing_file_and_ok_status(self):
        tmpdir = Path(self._make_tempdir())
        audio_path = tmpdir / "lesson001_narration.mp3"
        audio_path.write_bytes(b"ID3")

        self.assertTrue(recorded_audio_matches({"status": "ok", "audio_file": str(audio_path)}, audio_path))
        self.assertFalse(recorded_audio_matches({"status": "error", "audio_file": str(audio_path)}, audio_path))
        self.assertFalse(recorded_audio_matches({"status": "ok", "audio_file": str(tmpdir / 'missing.mp3')}, audio_path))

    def test_apply_reused_narration_updates_status_and_audio_file(self):
        lesson_data = {"explanation_narration_audio": {"status": "pending", "audio_file": ""}}
        target = Path("artifacts/output_audio/en/lesson101_narration/lesson101_narration.mp3")

        apply_reused_narration(lesson_data, target)

        self.assertEqual(lesson_data["explanation_narration_audio"]["status"], "ok")
        self.assertEqual(lesson_data["explanation_narration_audio"]["audio_file"], str(target))

    def test_normalize_explanation_timeline_sets_order_and_total(self):
        lesson_data = {
            "video_render_plan": {
                "explanation": {
                    "segments": [
                        {"duration_seconds": 4},
                        {"estimated_duration_seconds": 5},
                    ]
                }
            }
        }

        normalize_explanation_timeline(lesson_data)

        segments = lesson_data["video_render_plan"]["explanation"]["segments"]
        self.assertEqual(segments[0]["segment_order"], 1)
        self.assertEqual(segments[0]["start_time_seconds"], 0.0)
        self.assertEqual(segments[0]["end_time_seconds"], 4.0)
        self.assertEqual(segments[1]["segment_order"], 2)
        self.assertEqual(segments[1]["start_time_seconds"], 4.0)
        self.assertEqual(segments[1]["end_time_seconds"], 9.0)
        self.assertEqual(
            lesson_data["video_render_plan"]["explanation"]["timeline"]["total_duration_seconds"],
            9.0,
        )
        self.assertEqual(
            lesson_data["video_render_plan"]["explanation"]["timeline"]["segment_count"],
            2,
        )

    def test_detect_image_suffix_prefers_webp_when_requested(self):
        tmpdir = Path(self._make_tempdir())
        (tmpdir / "slide_001.webp").write_bytes(b"WEBP")
        (tmpdir / "slide_002.webp").write_bytes(b"WEBP")
        self.assertEqual(detect_image_suffix(tmpdir, [1, 2], prefer_webp=True), ".webp")

    def test_cleanup_stale_slide_assets_removes_extra_images_and_audio(self):
        tmpdir = Path(self._make_tempdir())
        slide_dir = tmpdir / "slides"
        audio_dir = tmpdir / "audio"
        slide_dir.mkdir(parents=True, exist_ok=True)
        audio_dir.mkdir(parents=True, exist_ok=True)
        (slide_dir / "slide_001.png").write_bytes(b"PNG")
        (slide_dir / "slide_002.png").write_bytes(b"PNG")
        (slide_dir / "slide_003.svg").write_bytes(b"SVG")
        (audio_dir / "lesson101_slide_001.mp3").write_bytes(b"ID3")
        (audio_dir / "lesson101_slide_002.mp3").write_bytes(b"ID3")
        (audio_dir / "lesson101_slide_003.mp3").write_bytes(b"ID3")

        cleanup_stale_slide_assets(
            slide_dir=slide_dir,
            audio_dir=audio_dir,
            lesson_digits="101",
            lang="en",
            slide_indexes=[2],
            image_suffixes=(".png", ".svg"),
        )

        self.assertFalse((slide_dir / "slide_001.png").exists())
        self.assertTrue((slide_dir / "slide_002.png").exists())
        self.assertFalse((slide_dir / "slide_003.svg").exists())
        self.assertFalse((audio_dir / "lesson101_slide_001.mp3").exists())
        self.assertTrue((audio_dir / "lesson101_slide_002.mp3").exists())
        self.assertFalse((audio_dir / "lesson101_slide_003.mp3").exists())

    def _make_tempdir(self) -> str:
        import tempfile

        return tempfile.mkdtemp(prefix="stage2-helpers-")


if __name__ == "__main__":
    unittest.main()
