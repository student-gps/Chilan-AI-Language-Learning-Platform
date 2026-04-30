import sys
from pathlib import Path


CONTENT_BUILDER_DIR = Path(__file__).resolve().parents[2]
if str(CONTENT_BUILDER_DIR) not in sys.path:
    sys.path.append(str(CONTENT_BUILDER_DIR))

try:
    from content_builder.core.llm_providers import LLMFactory
    from content_builder.core.pipeline import ContentPipeline
    from content_builder.pipelines.new_concept_english.agent import NewConceptEnglishAgent
except ImportError:
    from core.llm_providers import LLMFactory
    from core.pipeline import ContentPipeline
    from pipelines.new_concept_english.agent import NewConceptEnglishAgent


PIPELINE = ContentPipeline(
    pipeline_id="new_concept_english",
    display_name="New Concept English",
    target_language="en",
    source_language="zh",
    description=(
        "English-learning pipeline for New Concept English Book 1. "
        "It pairs odd source lessons as anchor text with even source lessons as "
        "pattern drills, then generates vocabulary, examples, grammar notes, "
        "practice items, and explanation render plans."
    ),
    agent_factory=NewConceptEnglishAgent,
    provider_factory=LLMFactory.create_provider,
    artifact_namespace="new_concept_english",
    default_output_lang="zh",
)
