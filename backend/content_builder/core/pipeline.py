from dataclasses import dataclass
from pathlib import Path
import json
from dataclasses import replace
from functools import lru_cache
from typing import Callable, Protocol

from .paths import ContentBuilderPaths


class AgentFactory(Protocol):
    def __call__(self, provider, memory_dir: Path):
        ...


class ProviderFactory(Protocol):
    def __call__(self):
        ...


@dataclass(frozen=True)
class ContentPipeline:
    """A concrete textbook/content-generation pipeline.

    A pipeline owns teaching assumptions: textbook structure, prompt strategy,
    question types, and media strategy. Shared low-level services live in core.
    """

    pipeline_id: str
    display_name: str
    target_language: str
    source_language: str
    description: str
    agent_factory: AgentFactory
    provider_factory: ProviderFactory
    artifact_namespace: str | None = None
    artifact_relative_path: str | None = None
    default_output_lang: str = "en"

    def artifact_root(self, paths: ContentBuilderPaths) -> Path:
        if self.artifact_relative_path:
            return paths.backend_dir / self.artifact_relative_path
        if self.artifact_namespace:
            return paths.artifacts_dir / self.artifact_namespace
        return paths.artifacts_dir

    def raw_materials_dir(self, paths: ContentBuilderPaths) -> Path:
        return self.artifact_root(paths) / "raw_materials"

    def archive_pdfs_dir(self, paths: ContentBuilderPaths) -> Path:
        return self.artifact_root(paths) / "archive_pdfs"

    def output_json_dir(self, paths: ContentBuilderPaths, lang: str | None = None) -> Path:
        return self.artifact_root(paths) / "output_json" / (lang or self.default_output_lang)

    def synced_json_dir(self, paths: ContentBuilderPaths, lang: str | None = None) -> Path:
        return self.artifact_root(paths) / "synced_json" / (lang or self.default_output_lang)

    def output_audio_dir(self, paths: ContentBuilderPaths) -> Path:
        return self.artifact_root(paths) / "output_audio"

    def output_video_dir(self, paths: ContentBuilderPaths) -> Path:
        return self.artifact_root(paths) / "output_video"

    def create_provider(self):
        return self.provider_factory()

    def create_agent(self, provider, memory_dir: Path):
        return self.agent_factory(provider, memory_dir)


@lru_cache(maxsize=1)
def pipeline_manifest() -> dict[str, dict]:
    payload = json.loads(Path(__file__).with_name('pipeline_manifest.json').read_text(encoding='utf-8'))
    return {item['pipeline_id']: item for item in payload['pipelines']}


@lru_cache(maxsize=1)
def pipeline_alias_map() -> dict[str, str]:
    aliases = {}
    for pipeline_id, item in pipeline_manifest().items():
        for alias in [pipeline_id, *item.get('aliases', [])]:
            aliases[alias.strip().lower()] = pipeline_id
    return aliases


def available_pipelines() -> dict[str, ContentPipeline]:
    from content_builder.zh.integrated_chinese.pipeline import PIPELINE as integrated_chinese
    from content_builder.en.new_concept_english.pipeline import PIPELINE as new_concept_english
    from content_builder.ja.minna_no_nihongo.pipeline import PIPELINE as minna_no_nihongo

    implementations = {
        integrated_chinese.pipeline_id: integrated_chinese,
        new_concept_english.pipeline_id: new_concept_english,
        minna_no_nihongo.pipeline_id: minna_no_nihongo,
    }
    canonical = {key: replace(value, artifact_relative_path=pipeline_manifest()[key]['artifact_relative_path'])
                 for key, value in implementations.items()}
    return {alias: canonical[key] for alias, key in pipeline_alias_map().items()}


def get_pipeline(pipeline_id: str | None = None) -> ContentPipeline:
    pipeline_key = (pipeline_id or "default").strip().lower()
    pipelines = available_pipelines()
    try:
        return pipelines[pipeline_key]
    except KeyError as exc:
        supported = ", ".join(sorted(k for k in pipelines if k != "default"))
        raise ValueError(f"Unsupported content pipeline '{pipeline_id}'. Supported: {supported}") from exc
