import sys
import types
import unittest
from pathlib import Path


if "json_repair" not in sys.modules:
    json_repair_mod = types.ModuleType("json_repair")
    json_repair_mod.repair_json = lambda text, **kwargs: text  # noqa: ARG005
    sys.modules["json_repair"] = json_repair_mod


BACKEND_DIR = Path(__file__).resolve().parents[1]
CONTENT_BUILDER_DIR = BACKEND_DIR / "content_builder"

for path in (BACKEND_DIR, CONTENT_BUILDER_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.append(path_str)

from content_builder.core.pipeline import get_pipeline
from content_builder.en.new_concept_english.agent import NewConceptEnglishAgent
from .pipeline_parity_helpers import (
    assert_no_legacy_keys,
    assert_pipeline_registration,
    assert_render_plan_minimum,
    assert_schema_v2_payload,
)


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
        assert_pipeline_registration(
            self,
            pipeline_id="new_concept_english",
            target_language="en",
            default_output_lang="zh",
            aliases=("nce", "en_from_zh", "new-concept-english"),
        )

    def test_lesson001_agent_finalizes_schema_v2_outputs(self):
        agent = NewConceptEnglishAgent(provider=None, memory_dir=Path("artifacts/new_concept_english"))
        lesson_data = agent.generate_content("lesson001.pdf", lesson_id=1)

        assert_schema_v2_payload(
            self,
            lesson_data,
            pipeline_id="new_concept_english",
            target_language="en",
            support_language="zh",
        )
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

        render_plan = assert_render_plan_minimum(
            self,
            lesson_data,
            subtitle_keys=("subtitle_en", "subtitle_support"),
        )
        self.assertGreater(len(render_plan["segments"]), 0)

        assert_no_legacy_keys(self, lesson_data)


if __name__ == "__main__":
    unittest.main()

