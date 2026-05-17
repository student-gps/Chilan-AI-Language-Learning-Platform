import sys
import unittest
from pathlib import Path

from fastapi import HTTPException


BACKEND_DIR = Path(__file__).resolve().parents[1]
backend_path = str(BACKEND_DIR)
if backend_path not in sys.path:
    sys.path.append(backend_path)

from services.media_pipeline_registry import get_media_pipeline


class MediaPipelineRegistryTest(unittest.TestCase):
    def test_integrated_chinese_media_pipeline(self):
        pipeline = get_media_pipeline("integrated_chinese")

        self.assertEqual(pipeline.target_language, "zh")
        self.assertEqual(
            pipeline.artifact_root(Path("backend")),
            Path("backend/content_builder/zh/integrated_chinese/artifacts"),
        )

    def test_new_concept_english_media_pipeline(self):
        pipeline = get_media_pipeline("new_concept_english")

        self.assertEqual(pipeline.target_language, "en")
        self.assertEqual(
            pipeline.artifact_root(Path("backend")),
            Path("backend/content_builder/en/new_concept_english/artifacts"),
        )

    def test_minna_no_nihongo_media_pipeline(self):
        pipeline = get_media_pipeline("minna_no_nihongo")

        self.assertEqual(pipeline.target_language, "ja")
        self.assertEqual(
            pipeline.artifact_root(Path("backend")),
            Path("backend/content_builder/ja/minna_no_nihongo/artifacts"),
        )

    def test_unknown_pipeline_raises_404(self):
        with self.assertRaises(HTTPException) as ctx:
            get_media_pipeline("missing")

        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
