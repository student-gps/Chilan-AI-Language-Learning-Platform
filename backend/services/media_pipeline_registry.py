from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException

from content_builder.core.pipeline import pipeline_alias_map, pipeline_manifest


@dataclass(frozen=True)
class MediaPipeline:
    pipeline_id: str
    target_language: str
    artifact_relative_path: str

    def artifact_root(self, backend_dir: Path) -> Path:
        return backend_dir / self.artifact_relative_path




def _build_media_pipelines() -> dict[str, MediaPipeline]:
    pipelines: dict[str, MediaPipeline] = {}
    for pipeline_id, item in pipeline_manifest().items():
        pipelines[pipeline_id] = MediaPipeline(
            pipeline_id=pipeline_id,
            target_language=str(item.get("target_language") or ""),
            artifact_relative_path=str(item.get("artifact_relative_path") or ""),
        )
    return pipelines


_PIPELINES = _build_media_pipelines()


def get_media_pipeline(pipeline_id: str) -> MediaPipeline:
    canonical_id = pipeline_alias_map().get((pipeline_id or "").strip().lower(), (pipeline_id or "").strip().lower())
    pipeline = _PIPELINES.get(canonical_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail=f"Unknown media pipeline: {pipeline_id}")
    return pipeline
