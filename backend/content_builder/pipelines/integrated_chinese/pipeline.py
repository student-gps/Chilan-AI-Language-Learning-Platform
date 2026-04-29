import sys
from pathlib import Path


CONTENT_BUILDER_DIR = Path(__file__).resolve().parents[2]
if str(CONTENT_BUILDER_DIR) not in sys.path:
    sys.path.append(str(CONTENT_BUILDER_DIR))

try:
    from content_builder.pipelines.integrated_chinese.agent import ContentCreatorAgent
    from content_builder.core.llm_providers import LLMFactory
    from content_builder.core.pipeline import ContentPipeline
except ImportError:
    from pipelines.integrated_chinese.agent import ContentCreatorAgent
    from core.llm_providers import LLMFactory
    from core.pipeline import ContentPipeline


PIPELINE = ContentPipeline(
    pipeline_id="integrated_chinese",
    display_name="Integrated Chinese",
    target_language="zh",
    source_language="en",
    description=(
        "Current Chinese-learning pipeline tailored to Integrated Chinese-style "
        "PDFs, pinyin, Chinese dialogue audio, and CN/EN practice types."
    ),
    agent_factory=ContentCreatorAgent,
    provider_factory=LLMFactory.create_provider,
    artifact_namespace=None,
    default_output_lang="en",
)
