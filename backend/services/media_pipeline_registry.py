import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException


@dataclass(frozen=True)
class MediaPipeline:
    pipeline_id: str
    target_language: str
    artifact_relative_path: str

    def artifact_root(self, backend_dir: Path) -> Path:
        return backend_dir / self.artifact_relative_path


_MANIFEST_PATH = Path(__file__).resolve().parents[1] / "content_builder" / "core" / "pipeline_manifest.json"
_FALLBACK_PIPELINES = {
    "integrated_chinese": {
        "pipeline_id": "integrated_chinese",
        "target_language": "zh",
        "artifact_relative_path": "content_builder/zh/integrated_chinese/artifacts",
        "aliases": ["default", "zh_from_en", "integrated-chinese", "zh"],
    },
    "new_concept_english": {
        "pipeline_id": "new_concept_english",
        "target_language": "en",
        "artifact_relative_path": "content_builder/en/new_concept_english/artifacts",
        "aliases": ["new-concept-english", "nce", "en_from_zh", "en"],
    },
    "minna_no_nihongo": {
        "pipeline_id": "minna_no_nihongo",
        "target_language": "ja",
        "artifact_relative_path": "content_builder/ja/minna_no_nihongo/artifacts",
        "aliases": ["minna-no-nihongo", "mnn", "ja_from_zh", "ja"],
    },
}


@lru_cache(maxsize=1)
def _pipeline_manifest() -> dict[str, dict]:
    if _MANIFEST_PATH.exists():
        try:
            data = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
            by_id: dict[str, dict] = {}
            for item in data.get("pipelines", []):
                if isinstance(item, dict) and item.get("pipeline_id"):
                    by_id[str(item["pipeline_id"])] = item
            if by_id:
                return by_id
        except (OSError, json.JSONDecodeError):
            pass
    return _FALLBACK_PIPELINES


@lru_cache(maxsize=1)
def _pipeline_alias_map() -> dict[str, str]:
    aliases: dict[str, str] = {}
    for pipeline_id, item in _pipeline_manifest().items():
        aliases[pipeline_id] = pipeline_id
        raw_aliases = item.get("aliases") if isinstance(item, dict) else []
        for alias in raw_aliases if isinstance(raw_aliases, list) else []:
            aliases[str(alias).strip().lower()] = pipeline_id
    return aliases


@lru_cache(maxsize=1)
def _build_media_pipelines() -> dict[str, MediaPipeline]:
    pipelines: dict[str, MediaPipeline] = {}
    for pipeline_id, item in _pipeline_manifest().items():
        pipelines[pipeline_id] = MediaPipeline(
            pipeline_id=pipeline_id,
            target_language=str(item.get("target_language") or ""),
            artifact_relative_path=str(item.get("artifact_relative_path") or ""),
        )
    return pipelines


def get_media_pipeline(pipeline_id: str) -> MediaPipeline:
    raw_id = (pipeline_id or "").strip().lower()
    canonical_id = _pipeline_alias_map().get(raw_id, raw_id)
    pipeline = _build_media_pipelines().get(canonical_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail=f"Unknown media pipeline: {pipeline_id}")
    return pipeline
