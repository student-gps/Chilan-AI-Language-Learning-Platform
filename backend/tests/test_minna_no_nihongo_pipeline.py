from pathlib import Path
import sys
import unittest


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from content_builder.core.pipeline import get_pipeline
from content_builder.ja.minna_no_nihongo.agent import MinnaNoNihongoAgent


class MinnaNoNihongoPipelineTest(unittest.TestCase):
    def test_pipeline_registry_aliases(self):
        pipeline = get_pipeline("minna_no_nihongo")
        self.assertEqual(pipeline.pipeline_id, "minna_no_nihongo")
        self.assertEqual(pipeline.target_language, "ja")
        self.assertIs(get_pipeline("mnn"), pipeline)

    def test_placeholder_payload_validates(self):
        agent = MinnaNoNihongoAgent(provider=None, memory_dir=Path("tmp"))
        payload = agent.generate_content("lesson001.pdf", lesson_id=1)
        self.assertEqual(payload["pipeline_id"], "minna_no_nihongo")
        self.assertEqual(payload["target_language"], "ja")
        self.assertTrue(payload["course_content"]["sentence_patterns"])
        self.assertTrue(payload["database_items"])


if __name__ == "__main__":
    unittest.main()

