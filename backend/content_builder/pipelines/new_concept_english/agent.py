from __future__ import annotations

import re
import traceback
from pathlib import Path

try:
    from content_builder.core.llm_providers import BaseLLMProvider
    from content_builder.pipelines.integrated_chinese.tasks.narration_audio import Task4DExplanationNarrator
    from content_builder.pipelines.new_concept_english.book_profiles import book1
    from content_builder.pipelines.new_concept_english.tasks.content_extractor import (
        _normalize_pattern_drills,
        _normalize_tokens,
        build_lesson001_data,
        normalize_lesson_data,
    )
    from content_builder.pipelines.new_concept_english.tasks.even_lesson import Task2EvenLessonDrillExtractor
    from content_builder.pipelines.new_concept_english.tasks.grammar_extractor import Task4GrammarPatternExtractor
    from content_builder.pipelines.new_concept_english.tasks.lesson_structure import Task1AnchorTextExtractor
    from content_builder.pipelines.new_concept_english.tasks.practice_generator import Task5PracticeGenerator
    from content_builder.pipelines.new_concept_english.tasks.schema_validator import NewConceptEnglishSchemaValidator
    from content_builder.pipelines.new_concept_english.tasks.source_pdf import find_book_pdf
    from content_builder.pipelines.new_concept_english.tasks.video_plan import (
        Task6LessonVideoPlanner,
        Task7RenderPlanComposer,
    )
    from content_builder.pipelines.new_concept_english.tasks.vocabulary import (
        Task3BExampleBackfiller,
        Task3VocabularyExtractor,
    )
except ImportError:
    from core.llm_providers import BaseLLMProvider
    from pipelines.integrated_chinese.tasks.narration_audio import Task4DExplanationNarrator
    from pipelines.new_concept_english.book_profiles import book1
    from pipelines.new_concept_english.tasks.content_extractor import (
        _normalize_pattern_drills,
        _normalize_tokens,
        build_lesson001_data,
        normalize_lesson_data,
    )
    from pipelines.new_concept_english.tasks.even_lesson import Task2EvenLessonDrillExtractor
    from pipelines.new_concept_english.tasks.grammar_extractor import Task4GrammarPatternExtractor
    from pipelines.new_concept_english.tasks.lesson_structure import Task1AnchorTextExtractor
    from pipelines.new_concept_english.tasks.practice_generator import Task5PracticeGenerator
    from pipelines.new_concept_english.tasks.schema_validator import NewConceptEnglishSchemaValidator
    from pipelines.new_concept_english.tasks.source_pdf import find_book_pdf
    from pipelines.new_concept_english.tasks.video_plan import (
        Task6LessonVideoPlanner,
        Task7RenderPlanComposer,
    )
    from pipelines.new_concept_english.tasks.vocabulary import (
        Task3BExampleBackfiller,
        Task3VocabularyExtractor,
    )


class NewConceptEnglishAgent:
    """Stage orchestrator for New Concept English Book 1.

    The pipeline mirrors the proven Integrated Chinese flow:
    anchor extraction -> teaching materials -> vocabulary/examples -> practice ->
    video plan -> render plan -> schema validation.
    """

    def __init__(self, provider: BaseLLMProvider | None, memory_dir: Path):
        self.provider = provider
        self.memory_dir = Path(memory_dir)
        self.task1 = Task1AnchorTextExtractor(provider) if provider else None
        self.task2 = Task2EvenLessonDrillExtractor(provider) if provider else None
        self.task3 = Task3VocabularyExtractor(provider) if provider else None
        self.task3b = Task3BExampleBackfiller()
        self.task4 = Task4GrammarPatternExtractor(provider) if provider else None
        self.task5 = Task5PracticeGenerator()
        self.task6 = Task6LessonVideoPlanner()
        self.task7 = Task7RenderPlanComposer()
        self.validator = NewConceptEnglishSchemaValidator()
        self.task4d = Task4DExplanationNarrator()

    def generate_content(
        self,
        file_path: str,
        lesson_id: int,
        course_id: int | str = book1.COURSE_ID,
        support_language: str = "zh",
    ) -> dict | None:
        print(f"\n🚀 [NCE Stage 1] 开始内容生成: {Path(file_path).name} (App Lesson: {lesson_id:03d})")

        lesson_pdf = Path(file_path)
        lesson_slice = book1.app_lesson_slice(lesson_id)
        source_pdf = self._find_source_pdf(lesson_pdf)

        try:
            if hasattr(self.provider, "reset_usage_log"):
                self.provider.reset_usage_log()

            if lesson_slice.lesson_slug == "lesson001":
                lesson_data = build_lesson001_data(
                    source_pdf=source_pdf,
                    lesson_pdf=lesson_pdf,
                    course_id=course_id,
                )
                lesson_data = self._finalize_outputs(lesson_data)
                print("✅ NCE Stage 1 完成（lesson001 golden set）。")
                return lesson_data

            if self.provider is None:
                raise ValueError("LLM provider is required for lessons after lesson001.")

            shared_file = self.provider.upload_pdf(str(lesson_pdf))

            structure = self.task1.run(
                lesson_slice=lesson_slice,
                support_language=support_language,
                file_obj=shared_file,
            )
            metadata = structure.get("lesson_metadata", {})
            anchor = (structure.get("course_content") or {}).get("anchor", {})

            even_lesson = self.task2.run(
                lesson_slice=lesson_slice,
                support_language=support_language,
                file_obj=shared_file,
            )

            vocabulary = self.task3.run(
                lesson_slice=lesson_slice,
                support_language=support_language,
                file_obj=shared_file,
            )

            even_vocab = [
                item for item in vocabulary
                if item.get("source_lesson") == lesson_slice.source_lessons[1]
            ]
            pattern_drills = _normalize_pattern_drills(
                even_lesson.get("pattern_drills", []),
                fallback_vocabulary=even_vocab,
                source_lesson=lesson_slice.source_lessons[1],
            )
            vocabulary = self.task3b.run(vocabulary, anchor, pattern_drills)
            anchor["lines"] = _normalize_tokens(anchor.get("lines", []), vocabulary)

            teaching_materials = self.task4.run(
                lesson_slice=lesson_slice,
                anchor=anchor,
                pattern_drills=pattern_drills,
                vocabulary=vocabulary,
                support_language=support_language,
                file_obj=shared_file,
            )

            raw_data = {
                "schema_version": "2.0",
                "pipeline_id": "new_concept_english",
                "target_language": "en",
                "support_language": support_language,
                "lesson_metadata": {
                    "course_id": int(course_id) if str(course_id).isdigit() else course_id,
                    "course_slug": book1.COURSE_SLUG,
                    "lesson_id": lesson_slice.app_lesson_index,
                    "lesson_slug": lesson_slice.lesson_slug,
                    "title": metadata.get("title", ""),
                    "title_localized": metadata.get("title_localized", ""),
                    "content_type": metadata.get("content_type", "dialogue_pattern"),
                    "source": {
                        "textbook": "New Concept English",
                        "book": 1,
                        "source_lessons": list(lesson_slice.source_lessons),
                        "source_pdf": str(source_pdf),
                        "lesson_pdf": str(lesson_pdf),
                        "pdf_pages": list(lesson_slice.pdf_pages),
                    },
                },
                "course_content": {
                    "anchor": anchor,
                    "vocabulary": vocabulary,
                    "pattern_drills": pattern_drills,
                    "writing_exercises": even_lesson.get("writing_exercises", []),
                },
                "teaching_materials": teaching_materials,
                "practice_items": [],
            }

            lesson_data = normalize_lesson_data(
                raw_data,
                lesson_slice=lesson_slice,
                source_pdf=source_pdf,
                lesson_pdf=lesson_pdf,
                support_language=support_language,
                course_id=course_id,
            )
            lesson_data = self._finalize_outputs(lesson_data)

            usage_summary = self.provider.get_usage_summary() if hasattr(self.provider, "get_usage_summary") else {}
            if usage_summary:
                lesson_data["llm_usage"] = usage_summary

            print("✅ NCE Stage 1 完成。")
            return lesson_data

        except Exception as exc:
            print(f"❌ NCE Stage 1 执行中断: {exc}")
            traceback.print_exc()
            return None

    def render_narration(self, lesson_data: dict, lesson_id: int, lang: str = "zh") -> dict:
        print(f"\n🎙️ [NCE Stage 2] 开始旁白渲染 (Lesson ID: {lesson_id}, lang={lang})")
        output_dir = self.memory_dir / "output_audio" / f"lesson{lesson_id}_narration_{lang}"
        render_plan = (lesson_data.get("video_render_plan") or {}).get("explanation", {})
        try:
            narration_result = self.task4d.run(
                render_plan=render_plan,
                output_dir=output_dir,
                lang=lang,
            )
            lesson_data["explanation_narration_audio"] = narration_result
        except Exception as exc:
            lesson_data["explanation_narration_audio"] = {"status": "error", "reason": str(exc)}
            print(f"⚠️ NCE Stage 2 旁白生成异常，已跳过: {exc}")
        return lesson_data

    def _finalize_outputs(self, lesson_data: dict) -> dict:
        practice = self.task5.run(
            lesson_id=lesson_data.get("lesson_metadata", {}).get("lesson_id", ""),
            course_id=lesson_data.get("lesson_metadata", {}).get("course_id", book1.COURSE_ID),
            anchor=lesson_data.get("course_content", {}).get("anchor", {}),
            pattern_drills=lesson_data.get("course_content", {}).get("pattern_drills", []),
            vocabulary=lesson_data.get("course_content", {}).get("vocabulary", []),
        )
        if not lesson_data.get("practice_items"):
            lesson_data["practice_items"] = practice["practice_items"]
        else:
            lesson_data["practice_items"] = self._canonicalize_practice_items(lesson_data["practice_items"])
        lesson_data["database_items"] = self._database_items_from_practice(
            lesson_data.get("practice_items", []),
            lesson_id=lesson_data.get("lesson_metadata", {}).get("lesson_id", ""),
            course_id=lesson_data.get("lesson_metadata", {}).get("course_id", book1.COURSE_ID),
        )

        if not self._has_narrated_explanation_plan(lesson_data):
            video_outputs = self.task6.run(lesson_data)
            lesson_data.update(video_outputs)
        else:
            lesson_data["video_plan"] = self._video_plan_from_existing_explanation(lesson_data)

        lesson_data["video_render_plan"] = self.task7.run(lesson_data)
        return self.validator.validate(lesson_data)

    def _canonicalize_practice_items(self, practice_items: list) -> list[dict]:
        normalized = []
        for item in practice_items or []:
            if not isinstance(item, dict):
                continue
            normalized_item = dict(item)
            normalized_item["question_type"] = self._canonical_question_type(normalized_item.get("question_type"))
            normalized.append(normalized_item)
        return normalized

    def _database_items_from_practice(self, practice_items: list, lesson_id: str, course_id: str) -> list[dict]:
        database_items = []
        for index, item in enumerate(practice_items or [], start=1):
            if not isinstance(item, dict):
                continue
            question_type = self._canonical_question_type(item.get("question_type"))
            database_items.append({
                "lesson_id": lesson_id,
                "course_id": course_id,
                "question_id": index,
                "question_type": question_type,
                "original_text": item.get("prompt"),
                "standard_answers": item.get("standard_answers", []),
                "context_examples": [],
                "metadata": item.get("metadata", {}) | {"context": item.get("context", {})},
            })
        return database_items

    def _canonical_question_type(self, question_type: str | None) -> str | None:
        if question_type == "SUPPORT_TO_TARGET":
            return "PATTERN_DRILL"
        return question_type

    def _video_plan_from_existing_explanation(self, lesson_data: dict) -> dict:
        metadata = lesson_data.get("lesson_metadata", {})
        return {
            "lesson_video_plan": {
                "lesson_id": metadata.get("lesson_id"),
                "course_id": metadata.get("course_id"),
                "lesson_title": metadata.get("title", ""),
                "target_audience": "Chinese speakers learning English",
                "primary_language": "en",
                "support_language": lesson_data.get("support_language", "zh"),
                "subtitle_options": {"target_text": True, "support_translation": True},
            },
            "dramatization": {"global_config": {}, "scenes": []},
            "explanation": {
                "global_config": {
                    "target_audience": "Chinese speakers learning English",
                    "presenter_mode": "voice_over",
                    "teaching_style": "clear, structured, practice-first",
                    "visual_style": "textbook-focused motion graphics",
                },
                "segments": lesson_data.get("explanation_plan", {}).get("segments", []),
            },
            "production_notes": {
                "recommended_workflow": [
                    "render anchor text",
                    "render vocabulary cards",
                    "render pattern drill",
                    "render guided practice",
                ],
                "remarks": "Built from an existing explanation_plan.",
            },
        }

    def _has_narrated_explanation_plan(self, lesson_data: dict) -> bool:
        segments = (lesson_data.get("explanation_plan") or {}).get("segments")
        if not isinstance(segments, list) or not segments:
            return False
        for segment in segments:
            if not isinstance(segment, dict):
                continue
            narration = (
                segment.get("narration")
                or segment.get("narration_zh")
                or ((segment.get("narration_track") or {}).get("subtitle_en") if isinstance(segment.get("narration_track"), dict) else "")
            )
            if isinstance(narration, str) and narration.strip():
                return True
        return False

    def _find_source_pdf(self, lesson_pdf: Path) -> Path:
        try:
            raw_materials_dir = lesson_pdf.parent.parent if lesson_pdf.parent.name == "book1" else self.memory_dir / "raw_materials"
            return find_book_pdf(raw_materials_dir, book_number=1)
        except Exception:
            return lesson_pdf


def parse_app_lesson_index(value: str | int) -> int:
    text = str(value).strip().lower()
    if text.startswith("lesson"):
        text = text.removeprefix("lesson")
    numbers = re.findall(r"\d+", text)
    if not numbers:
        raise ValueError(f"Cannot parse app lesson index from {value!r}")
    return int(numbers[0])
