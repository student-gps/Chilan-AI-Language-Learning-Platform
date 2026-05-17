from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException


@dataclass(frozen=True)
class MediaPipeline:
    pipeline_id: str
    target_language: str
    artifact_relative_path: str

    def artifact_root(self, backend_dir: Path) -> Path:
        return backend_dir / self.artifact_relative_path


_PIPELINES = {
    "integrated_chinese": MediaPipeline(
        pipeline_id="integrated_chinese",
        target_language="zh",
        artifact_relative_path="content_builder/zh/integrated_chinese/artifacts",
    ),
    "new_concept_english": MediaPipeline(
        pipeline_id="new_concept_english",
        target_language="en",
        artifact_relative_path="content_builder/en/new_concept_english/artifacts",
    ),
    "minna_no_nihongo": MediaPipeline(
        pipeline_id="minna_no_nihongo",
        target_language="ja",
        artifact_relative_path="content_builder/ja/minna_no_nihongo/artifacts",
    ),
}


def get_media_pipeline(pipeline_id: str) -> MediaPipeline:
    pipeline = _PIPELINES.get(pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail=f"Unknown media pipeline: {pipeline_id}")
    return pipeline
