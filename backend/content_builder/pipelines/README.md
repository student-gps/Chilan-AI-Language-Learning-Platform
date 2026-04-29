# Content Pipelines

Each subdirectory owns one textbook/content family. A pipeline is allowed to
make strong assumptions about source PDF structure, teaching strategy, question
types, and media assets.

Use `integrated_chinese` as the current legacy-compatible pipeline. When adding
an English textbook, prefer a textbook-family name such as `new_concept_english`
or `cambridge_english` instead of a language-only name such as
`content_builder_en`.

The old root-level `content_agent.py` and `tasks/` modules are compatibility
wrappers. New pipeline code should live here instead of in those legacy paths.

To register a new pipeline:

1. Create `pipelines/<pipeline_id>/pipeline.py`.
2. Expose a `PIPELINE = ContentPipeline(...)`.
3. Add it to `core/pipeline.py::available_pipelines()`.
