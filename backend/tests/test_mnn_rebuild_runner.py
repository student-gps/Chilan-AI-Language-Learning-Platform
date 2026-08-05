from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


BACKEND_DIR = Path(__file__).resolve().parents[1]
RUNNER_PATH = BACKEND_DIR / "content_builder" / "ja" / "minna_no_nihongo" / "run_mnn_rebuild.py"
BATCH_PATH = BACKEND_DIR / "content_builder" / "ja" / "minna_no_nihongo" / "scripts" / "run_stage1_stage2_batch.py"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


RUNNER = _load_module("mnn_rebuild_runner_test", RUNNER_PATH)
BATCH = _load_module("mnn_batch_runner_test", BATCH_PATH)


class MnnRebuildRunnerTests(unittest.TestCase):
    def test_all_skip_tts_uses_full_course_range_and_batch_flags(self):
        captured = {}

        with patch.object(sys, "argv", ["run_mnn_rebuild.py", "--all", "--skip-tts", "--force"]), patch.object(
            RUNNER.subprocess,
            "run",
            side_effect=lambda command, check: captured.update({"command": command, "check": check}) or type("Result", (), {"returncode": 0})(),
        ):
            result = RUNNER.main()

        self.assertEqual(result, 0)
        command = captured["command"]
        self.assertIn("--start", command)
        self.assertEqual(command[command.index("--start") + 1], "1")
        self.assertEqual(command[command.index("--end") + 1], "74")
        self.assertIn("--skip-tts", command)
        self.assertIn("--force-stage1", command)
        self.assertIn("--force-slides", command)

    def test_skip_vocab_llm_forwards_flag_to_batch_runner(self):
        captured = {}

        with patch.object(sys, "argv", ["run_mnn_rebuild.py", "--all", "--skip-vocab-llm"]), patch.object(
            RUNNER.subprocess,
            "run",
            side_effect=lambda command, check: captured.update({"command": command, "check": check}) or type("Result", (), {"returncode": 0})(),
        ):
            RUNNER.main()

        self.assertIn("--skip-vocab-llm", captured["command"])

        args = type("Args", (), {
            "lang": "zh",
            "course_id": 303,
            "skip_tts": True,
            "skip_vocab_llm": True,
            "force_stage1": True,
            "force_narration": False,
            "force_slides": True,
            "refresh_render_plan": False,
            "only_slide": None,
        })()

        stage1 = BATCH._stage1_command(args, 1)
        stage2 = BATCH._stage2_command(args, 1)

        self.assertEqual(stage1[stage1.index("--course-id") + 1], "303")
        self.assertIn("--lesson-audio-metadata-only", stage1)
        self.assertIn("--skip-vocab-llm", stage1)
        self.assertIn("--skip-tts", stage2)
        self.assertIn("--force-slides", stage2)


if __name__ == "__main__":
    unittest.main()
