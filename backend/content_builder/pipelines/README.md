# Content Pipeline Compatibility Shims

This directory now exists only for older imports such as
`content_builder.pipelines.integrated_chinese`.

Real implementations live in language-specific packages:

- `backend/content_builder_zh/integrated_chinese`
- `backend/content_builder_en/new_concept_english`

Shared registry, path, and LLM provider code lives in
`backend/content_builder_core`.

To register a new pipeline:

1. Create a language-specific package such as `content_builder_ja/minna_no_nihongo`.
2. Expose a `PIPELINE = ContentPipeline(...)`.
3. Add it to `content_builder_core.pipeline.available_pipelines()`.
