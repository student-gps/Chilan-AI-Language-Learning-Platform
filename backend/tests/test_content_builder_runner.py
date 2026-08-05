from __future__ import annotations

import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
import sys

if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from services.maintenance.content_builder_runner import build_content_builder_request, preview_content_builder


class ContentBuilderRunnerTests(unittest.TestCase):
    def test_slides_only_uses_audio_free_deck_command(self):
        request = build_content_builder_request(
            pipeline="minna_no_nihongo",
            lang="zh",
            lesson_start=1,
            lesson_end=1,
            run_stage1=False,
            run_stage2=True,
            stage2_mode="slides_only",
        )

        command = preview_content_builder(request)["commands"][0]["argv"]

        self.assertIn("--without-audio", command)
        self.assertNotIn("--skip-tts", command)


if __name__ == "__main__":
    unittest.main()
