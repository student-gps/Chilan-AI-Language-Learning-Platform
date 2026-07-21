import sys
import types
import unittest
from pathlib import Path

from fastapi import HTTPException


if "json_repair" not in sys.modules:
    json_repair_mod = types.ModuleType("json_repair")
    json_repair_mod.repair_json = lambda text, **kwargs: text  # noqa: ARG005
    sys.modules["json_repair"] = json_repair_mod


BACKEND_DIR = Path(__file__).resolve().parents[1]
backend_path = str(BACKEND_DIR)
if backend_path not in sys.path:
    sys.path.append(backend_path)

from services.media_pipeline_registry import get_media_pipeline
from content_builder.core.pipeline import get_pipeline, pipeline_alias_map, pipeline_manifest


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

    def test_alias_map_matches_manifest_expectations(self):
        aliases = pipeline_alias_map()
        self.assertEqual(aliases["mnn"], "minna_no_nihongo")
        self.assertEqual(aliases["integrated-chinese"], "integrated_chinese")
        self.assertEqual(aliases["nce"], "new_concept_english")

    def test_media_and_content_pipeline_share_artifact_path(self):
        manifest = pipeline_manifest()
        for pipeline_id in ("integrated_chinese", "new_concept_english", "minna_no_nihongo"):
            with self.subTest(pipeline_id=pipeline_id):
                media_pipeline = get_media_pipeline(pipeline_id)
                content_pipeline = get_pipeline(pipeline_id)
                self.assertEqual(
                    media_pipeline.artifact_relative_path,
                    manifest[pipeline_id]["artifact_relative_path"],
                )
                self.assertEqual(
                    content_pipeline.artifact_relative_path,
                    manifest[pipeline_id]["artifact_relative_path"],
                )


if __name__ == "__main__":
    unittest.main()
