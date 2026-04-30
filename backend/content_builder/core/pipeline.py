from dataclasses import dataclass
from pathlib import Path
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
    default_output_lang: str = "en"

    def artifact_root(self, paths: ContentBuilderPaths) -> Path:
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


def available_pipelines() -> dict[str, ContentPipeline]:
    try:
        from ..pipelines.integrated_chinese.pipeline import PIPELINE as integrated_chinese
        from ..pipelines.new_concept_english.pipeline import PIPELINE as new_concept_english
    except ImportError:
        from pipelines.integrated_chinese.pipeline import PIPELINE as integrated_chinese
        from pipelines.new_concept_english.pipeline import PIPELINE as new_concept_english

    return {
        integrated_chinese.pipeline_id: integrated_chinese,
        new_concept_english.pipeline_id: new_concept_english,
        "default": integrated_chinese,
        "zh_from_en": integrated_chinese,
        "integrated-chinese": integrated_chinese,
        "new-concept-english": new_concept_english,
        "nce": new_concept_english,
        "en_from_zh": new_concept_english,
    }


def get_pipeline(pipeline_id: str | None = None) -> ContentPipeline:
    pipeline_key = (pipeline_id or "default").strip().lower()
    pipelines = available_pipelines()
    try:
        return pipelines[pipeline_key]
    except KeyError as exc:
        supported = ", ".join(sorted(k for k in pipelines if k != "default"))
        raise ValueError(f"Unsupported content pipeline '{pipeline_id}'. Supported: {supported}") from exc
