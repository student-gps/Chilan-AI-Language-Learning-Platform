import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
CONTENT_BUILDER_DIR = BACKEND_DIR / "content_builder"

for path in (BACKEND_DIR, CONTENT_BUILDER_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.append(path_str)

from content_builder.core.pipeline import get_pipeline
from content_builder.pipelines.new_concept_english.agent import NewConceptEnglishAgent


def _find_old_keys(value, path="$"):
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in {"cn", "py", "pinyin", "chinese"}:
                yield child_path
            yield from _find_old_keys(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _find_old_keys(child, f"{path}[{index}]")


class NewConceptPipelineOrchestrationTests(unittest.TestCase):
    def test_pipeline_is_registered(self):
        pipeline = get_pipeline("new_concept_english")
        self.assertEqual(pipeline.pipeline_id, "new_concept_english")
        self.assertEqual(pipeline.target_language, "en")
        self.assertEqual(pipeline.default_output_lang, "zh")

    def test_lesson001_agent_finalizes_schema_v2_outputs(self):
        agent = NewConceptEnglishAgent(provider=None, memory_dir=Path("artifacts/new_concept_english"))
        lesson_data = agent.generate_content("lesson001.pdf", lesson_id=1)

        self.assertIsNotNone(lesson_data)
        self.assertEqual(lesson_data["schema_version"], "2.0")
        self.assertEqual(lesson_data["pipeline_id"], "new_concept_english")
        self.assertEqual(lesson_data["target_language"], "en")
        self.assertEqual(lesson_data["support_language"], "zh")
        self.assertEqual(lesson_data["lesson_metadata"]["course_id"], 101)
        self.assertEqual(lesson_data["lesson_metadata"]["lesson_id"], 1)
        self.assertEqual(lesson_data["lesson_metadata"]["lesson_slug"], "lesson001")

        self.assertGreater(len(lesson_data["practice_items"]), 0)
        self.assertGreater(len(lesson_data["database_items"]), 0)
        question_types = {
            item["question_type"]
            for item in lesson_data["database_items"]
        }
        self.assertIn("PATTERN_DRILL", question_types)
        self.assertNotIn("SUPPORT_TO_TARGET", question_types)

        render_plan = lesson_data["video_render_plan"]["explanation"]
        self.assertGreater(len(render_plan["segments"]), 0)
        self.assertIn("subtitle_en", render_plan["segments"][0]["narration_track"])
        self.assertIn("subtitle_support", render_plan["segments"][0]["narration_track"])

        self.assertEqual(list(_find_old_keys(lesson_data)), [])


if __name__ == "__main__":
    unittest.main()
