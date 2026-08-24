import tempfile
import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from content_builder.zh.integrated_chinese.scripts import run_resumable_publish as publish
from content_builder.zh.integrated_chinese.scripts.run_resumable_enhanced_english import LessonState


class IntegratedChineseResumablePublishTests(unittest.TestCase):
    def test_source_path_prefers_new_output_over_synced_checkpoint(self):
        with tempfile.TemporaryDirectory(prefix="ic-publish-") as temp_dir:
            root = Path(temp_dir)
            output = root / "output"
            synced = root / "synced"
            output.mkdir()
            synced.mkdir()
            output_path = output / "lesson101_data_fr.json"
            synced_path = synced / "lesson101_data_fr.json"
            output_path.write_text("{}", encoding="utf-8")
            synced_path.write_text("{}", encoding="utf-8")

            selected = publish._source_path(output, synced, 101, "fr")

        self.assertEqual(selected, output_path)

    def test_publish_readiness_uses_final_slide_audio_not_whole_narration_intermediate(self):
        state = LessonState(
            lesson_id=101,
            json_path=Path("lesson101_data.json"),
            readable=True,
            enhanced=True,
            narration=False,
            slides=True,
        )

        ready, reason = publish._publish_readiness(state)

        self.assertTrue(ready)
        self.assertEqual(reason, "")

    def test_checkpoint_requires_matching_hash_and_course(self):
        entry = {
            "status": "complete",
            "source_sha256": "abc",
            "course_id": 2,
        }

        self.assertTrue(publish._checkpoint_matches(entry, "abc", 2))
        self.assertFalse(publish._checkpoint_matches(entry, "changed", 2))
        self.assertFalse(publish._checkpoint_matches(entry, "abc", 1))

    def test_asset_refs_deduplicate_shared_object_keys(self):
        data = {
            "teaching_slide_deck": {
                "slides": [
                    {
                        "id": "seg_001",
                        "image": {"local_path": "slide.webp", "object_key": "slides/one.webp"},
                        "audio": {"local_path": "slide.mp3", "object_key": "audio/shared.mp3"},
                    },
                    {
                        "id": "seg_002",
                        "image": {"local_path": "slide2.webp", "object_key": "slides/two.webp"},
                        "audio": {"local_path": "slide.mp3", "object_key": "audio/shared.mp3"},
                    },
                ]
            }
        }

        refs = publish._asset_refs(data)

        self.assertEqual({ref.object_key for ref in refs}, {"slides/one.webp", "slides/two.webp", "audio/shared.mp3"})


if __name__ == "__main__":
    unittest.main()
