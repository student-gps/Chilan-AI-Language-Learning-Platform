import sys
from pathlib import Path


CONTENT_BUILDER_DIR = Path(__file__).resolve().parents[2]
if str(CONTENT_BUILDER_DIR) not in sys.path:
    sys.path.append(str(CONTENT_BUILDER_DIR))

try:
    from content_builder.core.llm_providers import LLMFactory
    from content_builder.core.pipeline import ContentPipeline
    from content_builder.ja.minna_no_nihongo.agent import MinnaNoNihongoAgent
except ImportError:
    from content_builder.core.llm_providers import LLMFactory
    from content_builder.core.pipeline import ContentPipeline
    from content_builder.ja.minna_no_nihongo.agent import MinnaNoNihongoAgent


PIPELINE = ContentPipeline(
    pipeline_id="minna_no_nihongo",
    display_name="Minna no Nihongo",
    target_language="ja",
    source_language="zh",
    description=(
        "Japanese-learning pipeline for Minna no Nihongo. It assumes a stable "
        "lesson structure around sentence patterns, example sentences, dialogue, "
        "vocabulary, grammar notes, and practice drills."
    ),
    agent_factory=MinnaNoNihongoAgent,
    provider_factory=LLMFactory.create_provider,
    artifact_namespace="minna_no_nihongo",
    artifact_relative_path="content_builder/ja/minna_no_nihongo/artifacts",
    default_output_lang="zh",
)
