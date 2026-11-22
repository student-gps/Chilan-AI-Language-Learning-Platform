from __future__ import annotations

import traceback
from pathlib import Path

try:
    from content_builder.core.llm_providers import BaseLLMProvider
    from content_builder.ja.minna_no_nihongo.book_profiles import book1, lesson_profile as resolve_lesson_profile
    from content_builder.ja.minna_no_nihongo.tasks.content_extractor import (
        MinnaNoNihongoExtractor,
        build_placeholder_lesson_data,
    )
    from content_builder.ja.minna_no_nihongo.tasks.explanation_composer import MinnaNoNihongoExplanationComposer
    from content_builder.ja.minna_no_nihongo.tasks.explanation_writer import MinnaNoNihongoExplanationWriter
    from content_builder.ja.minna_no_nihongo.tasks.grammar_refiner import MinnaNoNihongoGrammarRefiner
    from content_builder.ja.minna_no_nihongo.tasks.lesson_audio import MinnaNoNihongoLessonAudioRenderer
    from content_builder.ja.minna_no_nihongo.tasks.lesson_normalizer import MinnaNoNihongoLessonNormalizer
    from content_builder.ja.minna_no_nihongo.tasks.practice_generator import MinnaNoNihongoPracticeGenerator
    from content_builder.ja.minna_no_nihongo.tasks.reading_auditor import MinnaNoNihongoReadingAuditor
    from content_builder.ja.minna_no_nihongo.tasks.schema_validator import MinnaNoNihongoSchemaValidator
    from content_builder.ja.minna_no_nihongo.tasks.speaker_resolver import MinnaNoNihongoSpeakerResolver
    from content_builder.ja.minna_no_nihongo.tasks.vocab_memory import MinnaNoNihongoVocabMemory
    from content_builder.zh.integrated_chinese.tasks.narration_audio import Task4DExplanationNarrator
except ImportError:
    from content_builder.core.llm_providers import BaseLLMProvider
    from content_builder.ja.minna_no_nihongo.book_profiles import book1, lesson_profile as resolve_lesson_profile
    from content_builder.ja.minna_no_nihongo.tasks.content_extractor import (
        MinnaNoNihongoExtractor,
        build_placeholder_lesson_data,
    )
    from content_builder.ja.minna_no_nihongo.tasks.explanation_composer import MinnaNoNihongoExplanationComposer
    from content_builder.ja.minna_no_nihongo.tasks.explanation_writer import MinnaNoNihongoExplanationWriter
    from content_builder.ja.minna_no_nihongo.tasks.grammar_refiner import MinnaNoNihongoGrammarRefiner
    from content_builder.ja.minna_no_nihongo.tasks.lesson_audio import MinnaNoNihongoLessonAudioRenderer
    from content_builder.ja.minna_no_nihongo.tasks.lesson_normalizer import MinnaNoNihongoLessonNormalizer
    from content_builder.ja.minna_no_nihongo.tasks.practice_generator import MinnaNoNihongoPracticeGenerator
    from content_builder.ja.minna_no_nihongo.tasks.reading_auditor import MinnaNoNihongoReadingAuditor
    from content_builder.ja.minna_no_nihongo.tasks.schema_validator import MinnaNoNihongoSchemaValidator
    from content_builder.ja.minna_no_nihongo.tasks.speaker_resolver import MinnaNoNihongoSpeakerResolver
    from content_builder.ja.minna_no_nihongo.tasks.vocab_memory import MinnaNoNihongoVocabMemory
    from content_builder.zh.integrated_chinese.tasks.narration_audio import Task4DExplanationNarrator


class MinnaNoNihongoAgent:
    """Stage orchestrator for Minna no Nihongo.

    Stage 1 is intentionally split into small tasks:
    extraction -> normalization/reading -> teaching flow -> practice/render plan -> validation.
    """

    def __init__(self, provider: BaseLLMProvider | None, memory_dir: Path, render_lesson_audio: bool = True):
        self.provider = provider
        self.memory_dir = Path(memory_dir)
        self.render_lesson_audio = bool(render_lesson_audio)
        self.extractor = MinnaNoNihongoExtractor(provider) if provider else None
        self.explanation_writer = MinnaNoNihongoExplanationWriter(provider) if provider else None
        self.explanation_composer = MinnaNoNihongoExplanationComposer()
        self.normalizer = MinnaNoNihongoLessonNormalizer()
        self.speaker_resolver = MinnaNoNihongoSpeakerResolver()
        self.grammar_refiner = MinnaNoNihongoGrammarRefiner()
        self.reading_auditor = MinnaNoNihongoReadingAuditor()
        self.practice_generator = MinnaNoNihongoPracticeGenerator()
        self.lesson_audio_renderer = MinnaNoNihongoLessonAudioRenderer()
        self.narration_renderer = Task4DExplanationNarrator()
        self.narration_renderer.duration_mode = "actual"
        self.narration_renderer.duration_buffer_seconds = 0.8
        self.vocab_memory = MinnaNoNihongoVocabMemory(memory_dir)
        self.validator = MinnaNoNihongoSchemaValidator()

    def generate_content(
        self,
        file_path: str,
        lesson_id: int,
        course_id: int | str = book1.COURSE_ID,
        support_language: str = "zh",
    ) -> dict | None:
        print(f"\n🚀 [MNN Stage 1] 开始内容生成: {Path(file_path).name} (Lesson: {lesson_id:03d})")
        lesson_pdf = Path(file_path)
        source_pdf = lesson_pdf

        try:
            if hasattr(self.provider, "reset_usage_log"):
                self.provider.reset_usage_log()

            if self.extractor is None:
                print("  ▶️ [MNN Task 1] 使用 placeholder 内容。")
                lesson_data = build_placeholder_lesson_data(
                    lesson_id=lesson_id,
                    source_pdf=source_pdf,
                    lesson_pdf=lesson_pdf,
                    course_id=course_id,
                    support_language=support_language,
                )
            else:
                shared_pdf_obj = None
                if hasattr(self.provider, "upload_pdf"):
                    print("  ▶️ [MNN PDF] 预加载教材 PDF，后续 LLM 子任务复用。")
                    shared_pdf_obj = self.provider.upload_pdf(str(lesson_pdf))
                print("  ▶️ [MNN Task 1] 抽取教材结构。")
                raw_lesson_data = self.extractor.run(
                    lesson_pdf=lesson_pdf,
                    source_pdf=source_pdf,
                    lesson_id=lesson_id,
                    support_language=support_language,
                    course_id=course_id,
                    file_obj=shared_pdf_obj,
                )
                self._print_content_counts("Task 1 raw", raw_lesson_data)
                print("  ▶️ [MNN Task 2] 审校并修正 dialogue speaker。")
                raw_lesson_data = self.speaker_resolver.run(
                    raw_lesson_data,
                    llm_provider=self.provider,
                    lesson_id=lesson_id,
                )
                self._print_diagnostic_summary(raw_lesson_data, "speaker_resolution")
                print("  ▶️ [MNN Task 3] 发现并修复 grammar_sections。")
                raw_lesson_data = self.grammar_refiner.run(
                    raw_lesson_data,
                    llm_provider=self.provider,
                    lesson_pdf=lesson_pdf,
                    lesson_file_obj=shared_pdf_obj,
                    lesson_id=lesson_id,
                    support_language=support_language,
                )
                self._print_diagnostic_summary(raw_lesson_data, "grammar_refinement")
                prior_token_vocabulary = self.vocab_memory.token_merge_vocabulary(lesson_id)
                if prior_token_vocabulary:
                    print(f"     📚 historical token lexicon: {len(prior_token_vocabulary)} entries")
                print("  ▶️ [MNN Task 4] 规范化内容并补齐 reading/tokens。")
                lesson_data = self.normalizer.run(
                    raw_lesson_data,
                    lesson_id=lesson_id,
                    source_pdf=source_pdf,
                    lesson_pdf=lesson_pdf,
                    support_language=support_language,
                    course_id=course_id,
                    token_merge_vocabulary=prior_token_vocabulary,
                )
                if isinstance(raw_lesson_data.get("pipeline_diagnostics"), dict):
                    lesson_data["pipeline_diagnostics"] = raw_lesson_data["pipeline_diagnostics"]
                self._print_content_counts("Task 4 normalized", lesson_data)
                print("  ▶️ [MNN Task 5] 审校 reading/tokens。")
                lesson_data = self.reading_auditor.run(
                    lesson_data,
                    llm_provider=self.provider,
                    lesson_id=lesson_id,
                    token_merge_vocabulary=prior_token_vocabulary,
                )
                self._print_diagnostic_summary(lesson_data, "reading_audit")

            print("  ▶️ [MNN Task 6] 标记词汇记忆与历史例句。")
            lesson_data = self.vocab_memory.annotate_lesson(lesson_data)
            lesson_data = self._apply_intermediate_vocabulary_policy(lesson_data)
            self._print_diagnostic_summary(lesson_data, "vocab_memory")
            lesson_data = self._direct_explanation_plan(lesson_data)
            lesson_data = self._finalize_outputs(lesson_data)
            if self.extractor is not None:
                memory_summary = self.vocab_memory.save_lesson_vocabulary(lesson_data)
                lesson_data.setdefault("pipeline_diagnostics", {}).setdefault("vocab_memory", {}).update(memory_summary)
                print(
                    "     💾 vocab memory saved="
                    f"{memory_summary.get('saved_count', 0)} -> {memory_summary.get('memory_file', '')}"
                )
            usage_summary = self.provider.get_usage_summary() if hasattr(self.provider, "get_usage_summary") else {}
            if usage_summary:
                lesson_data["llm_usage"] = usage_summary
            print("✅ MNN Stage 1 完成。")
            return lesson_data
        except Exception as exc:
            print(f"❌ MNN Stage 1 执行中断: {exc}")
            traceback.print_exc()
            return None

    def _apply_intermediate_vocabulary_policy(self, lesson_data: dict) -> dict:
        metadata = lesson_data.get("lesson_metadata") if isinstance(lesson_data.get("lesson_metadata"), dict) else {}
        lesson_id = metadata.get("lesson_id")
        try:
            profile = resolve_lesson_profile(int(lesson_id))
        except (TypeError, ValueError):
            return lesson_data
        if profile.pedagogy_profile != "intermediate_read_write_speak_listen_grammar":
            return lesson_data

        content = lesson_data.get("course_content") if isinstance(lesson_data.get("course_content"), dict) else {}
        vocabulary = content.get("vocabulary") if isinstance(content.get("vocabulary"), list) else []
        if not vocabulary:
            return lesson_data

        kept = []
        lexical_notes = [
            dict(item)
            for item in content.get("lexical_notes", [])
            if isinstance(item, dict)
        ] if isinstance(content.get("lexical_notes"), list) else []
        moved_review = 0

        for vocab in vocabulary:
            if not isinstance(vocab, dict):
                continue
            memory_status = (vocab.get("memory_status") or "").strip()
            if vocab.get("is_new_vocabulary") is False or memory_status in {"review", "new_meaning"}:
                note = self._lexical_note_from_vocab(vocab, reason="previously_seen")
                lexical_notes.append(note)
                moved_review += 1
                continue
            vocab["lesson_section"] = "core"
            vocab.setdefault("memory_context", {})
            if isinstance(vocab["memory_context"], dict):
                vocab["memory_context"]["intermediate_policy"] = "new_vocabulary_quizable_review_context_only"
            kept.append(vocab)

        content["vocabulary"] = kept
        content["lexical_notes"] = lexical_notes
        diagnostics = lesson_data.setdefault("pipeline_diagnostics", {}).setdefault("intermediate_vocabulary_policy", {})
        diagnostics.update({
            "enabled": True,
            "kept_learning_count": len(kept),
            "moved_review_count": moved_review,
            "lexical_notes_count": len(lexical_notes),
        })
        if moved_review:
            print(
                "     📚 intermediate vocab policy: "
                f"learning={len(kept)}, review_notes={moved_review}"
            )
        return lesson_data

    def _lexical_note_from_vocab(self, vocab: dict, *, reason: str) -> dict:
        note = dict(vocab)
        note["note_type"] = "lexical_note"
        note["learning_role"] = "context_only"
        note["quiz_eligible"] = False
        note["policy_reason"] = reason
        return note

    def _direct_explanation_plan(self, lesson_data: dict) -> dict:
        if self.explanation_writer is None:
            return lesson_data
        print("  ▶️ [MNN Task 6.5] 生成日语讲解导演脚本与旁白。")
        try:
            metadata = lesson_data.get("lesson_metadata") if isinstance(lesson_data.get("lesson_metadata"), dict) else {}
            course_content = lesson_data.get("course_content") if isinstance(lesson_data.get("course_content"), dict) else {}
            teaching_materials = (
                lesson_data.get("teaching_materials")
                if isinstance(lesson_data.get("teaching_materials"), dict)
                else {}
            )
            explanation = self.explanation_writer.run(metadata, course_content, teaching_materials)
            lesson_data["video_plan"] = {
                "explanation": explanation,
                "production_notes": {
                    "recommended_workflow": [
                        "compose LLM-directed Japanese explanation segments",
                        "render learner-language narration",
                        "render static slide deck",
                    ],
                    "remarks": "The LLM directs segment order and narration; composer owns supported templates.",
                },
            }
            lesson_data["video_render_plan"] = self.explanation_composer.run(
                metadata,
                course_content,
                explanation,
            )
            notes = (
                ((lesson_data.get("video_render_plan") or {}).get("explanation") or {}).get("renderer_notes")
                if isinstance((lesson_data.get("video_render_plan") or {}).get("explanation"), dict)
                else {}
            )
            plan_version = notes.get("plan_version") if isinstance(notes, dict) else ""
            segment_count = len(
                (((lesson_data.get("video_render_plan") or {}).get("explanation") or {}).get("segments") or [])
            )
            diagnostics = lesson_data.setdefault("pipeline_diagnostics", {}).setdefault("explanation_director", {})
            diagnostics.update({
                "llm_segments": len(explanation.get("segments") or []) if isinstance(explanation, dict) else 0,
                "render_segments": segment_count,
                "used_llm_director": plan_version == "mnn_llm_director_v1",
                "plan_version": plan_version,
            })
            print(f"     🎬 explanation director: llm={diagnostics['llm_segments']} render={segment_count}")
        except Exception as exc:
            lesson_data.setdefault("pipeline_diagnostics", {}).setdefault("explanation_director", {}).update({
                "used_llm_director": False,
                "error": str(exc),
            })
            print(f"     ⚠️ explanation director 失败，保留 deterministic render plan: {exc}")
        return lesson_data

    def _finalize_outputs(self, lesson_data: dict) -> dict:
        print("  ▶️ [MNN Task 7] 生成 database_items 并执行 schema 校验。")
        lesson_data["database_items"] = self.practice_generator.build_database_items(
            lesson_data,
            llm_provider=self.provider,
        )
        self._print_database_summary(lesson_data.get("database_items", []))
        print("  ▶️ [MNN Task 8] 生成课文逐句音频与 lesson_audio_assets。")
        metadata = lesson_data.get("lesson_metadata", {}) if isinstance(lesson_data.get("lesson_metadata"), dict) else {}
        lesson_id = metadata.get("lesson_id", "unknown")
        lesson_slug = f"lesson{int(lesson_id):03d}" if str(lesson_id).isdigit() else f"lesson{lesson_id}"
        audio_output_dir = self.memory_dir / "output_audio" / lesson_slug
        try:
            lesson_audio_assets = self.lesson_audio_renderer.render_sentence_audio_assets(
                lesson_data=lesson_data,
                output_dir=audio_output_dir,
                dry_run=not self.render_lesson_audio,
                existing_assets=lesson_data.get("lesson_audio_assets") if isinstance(lesson_data.get("lesson_audio_assets"), dict) else {},
                reuse_existing=True,
            )
        except Exception as exc:
            print(f"     ⚠️ 课文音频真实渲染失败，回退为 metadata_only: {exc}")
            lesson_data.setdefault("pipeline_diagnostics", {}).setdefault("lesson_audio", {})["error"] = str(exc)
            lesson_audio_assets = self.lesson_audio_renderer.render_sentence_audio_assets(
                lesson_data=lesson_data,
                output_dir=audio_output_dir,
                dry_run=True,
            )
        lesson_data["lesson_audio_assets"] = lesson_audio_assets.get("lesson_audio_assets", {})
        audio_items = lesson_data["lesson_audio_assets"].get("items", [])
        full_audio = lesson_data["lesson_audio_assets"].get("full_audio", {})
        print(
            "     🎧 lesson audio: "
            f"items={len(audio_items)} "
            f"ready={sum(1 for item in audio_items if item.get('status') == 'ready')} "
            f"full={full_audio.get('status', 'unknown')}"
        )
        return self.validator.validate(lesson_data)

    def render_narration(self, lesson_data: dict, lesson_id: int, lang: str = "zh") -> dict:
        """Stage 2 — render learner-language narration and write timings back."""
        print(f"\n🎙️ [MNN Stage 2] 开始旁白渲染: lesson{lesson_id:03d} [lang={lang}]")
        try:
            lang_suffix = f"_{lang}" if lang != "en" else ""
            lesson_slug = f"lesson{lesson_id:03d}"
            narration_audio_dir = self.memory_dir / "output_audio" / lang / f"{lesson_slug}_narration"
            explanation_render_plan = lesson_data.get("video_render_plan", {}).get("explanation", {})
            if isinstance(explanation_render_plan, dict):
                explanation_render_plan["lesson_id"] = f"{lesson_id:03d}"
            self._ensure_narration_subtitles(explanation_render_plan, lang)
            narration_result = self.narration_renderer.run(
                render_plan=explanation_render_plan,
                output_dir=narration_audio_dir,
                lang=lang,
            )
            lesson_data["explanation_narration_audio"] = narration_result

            if narration_result.get("status") == "ok":
                seg_count = narration_result.get("segment_count", 0)
                print(f"✨ 日语课程旁白音轨已生成，共 {seg_count} 段: {narration_result['audio_file']}")
                self._apply_narration_timings(lesson_data, narration_result)
            else:
                print(f"⚠️ 旁白生成跳过/失败: {narration_result.get('reason', '')}")
        except Exception as exc:
            print(f"⚠️ MNN Stage 2 旁白生成异常，已跳过: {exc}")
            lesson_data["explanation_narration_audio"] = {"status": "error", "reason": str(exc)}

        self._print_narration_cost_hint(lesson_data)
        print("✅ MNN Stage 2 旁白步骤完成。")
        return lesson_data

    def _ensure_narration_subtitles(self, explanation_render_plan: dict, lang: str) -> None:
        segments = explanation_render_plan.get("segments") if isinstance(explanation_render_plan, dict) else []
        if not isinstance(segments, list):
            return
        preferred_keys = [f"subtitle_{lang}", "script", "subtitle_zh", "subtitle_en"]
        for segment in segments:
            if not isinstance(segment, dict):
                continue
            track = segment.setdefault("narration_track", {})
            if not isinstance(track, dict):
                continue
            text = ""
            for key in preferred_keys:
                value = (track.get(key) or "").strip()
                if value:
                    text = value
                    break
            if text:
                track.setdefault("script", text)

    def _apply_narration_timings(self, lesson_data: dict, narration_result: dict) -> None:
        segment_timings = narration_result.get("segment_timings", {})
        segment_actual_durations = narration_result.get("segment_actual_durations", {})
        segment_sentences = narration_result.get("segment_sentences", {})
        plan_segments = (
            lesson_data.get("video_render_plan", {})
            .get("explanation", {})
            .get("segments", [])
        )
        if not isinstance(plan_segments, list):
            return
        for segment in plan_segments:
            if not isinstance(segment, dict):
                continue
            segment_key = str(segment.get("segment_id") or segment.get("segment_order", ""))
            if segment_key in segment_timings:
                segment["sentence_timings_seconds"] = segment_timings[segment_key]
            if segment_key in segment_actual_durations:
                segment["duration_seconds"] = segment_actual_durations[segment_key]
            if segment_key in segment_sentences:
                segment["sentence_texts"] = segment_sentences[segment_key]

        cursor = 0.0
        for segment in plan_segments:
            if not isinstance(segment, dict):
                continue
            segment["start_time_seconds"] = round(cursor, 3)
            cursor += float(segment.get("duration_seconds", 0) or 0)
            segment["end_time_seconds"] = round(cursor, 3)

        timeline = (
            lesson_data.get("video_render_plan", {})
            .get("explanation", {})
            .setdefault("timeline", {})
        )
        timeline["total_duration_seconds"] = round(cursor, 3)
        timeline["segment_count"] = len([segment for segment in plan_segments if isinstance(segment, dict)])

    def _print_narration_cost_hint(self, lesson_data: dict) -> None:
        narration_chars = 0
        segments = (
            lesson_data.get("video_render_plan", {})
            .get("explanation", {})
            .get("segments", [])
        )
        for segment in segments if isinstance(segments, list) else []:
            if not isinstance(segment, dict):
                continue
            track = segment.get("narration_track") if isinstance(segment.get("narration_track"), dict) else {}
            text = (track.get("script") or track.get("subtitle_zh") or track.get("subtitle_en") or "").strip()
            narration_chars += len(text)
        provider = getattr(self.narration_renderer, "provider", "unknown")
        model = getattr(self.narration_renderer, "model", "")
        print(f"💰 MNN Stage 2 旁白 TTS: {provider} ({model}) 约 {narration_chars:,} 字符")

    def _print_content_counts(self, label: str, lesson_data: dict) -> None:
        content = lesson_data.get("course_content") if isinstance(lesson_data.get("course_content"), dict) else {}
        dialogue = content.get("dialogue") if isinstance(content.get("dialogue"), dict) else {}
        print(
            f"     📊 {label}: "
            f"文型={len(content.get('sentence_patterns') or [])}, "
            f"例文={len(content.get('example_sentences') or [])}, "
            f"会話={len(dialogue.get('lines') or [])}, "
            f"vocab={len(content.get('vocabulary') or [])}, "
            f"display_only={len(content.get('display_only_vocabulary') or [])}, "
            f"grammar={len(content.get('grammar_sections') or [])}, "
            f"practice={len(lesson_data.get('practice_items') or [])}"
        )

    def _print_diagnostic_summary(self, lesson_data: dict, key: str) -> None:
        diagnostics = lesson_data.get("pipeline_diagnostics") if isinstance(lesson_data.get("pipeline_diagnostics"), dict) else {}
        payload = diagnostics.get(key) if isinstance(diagnostics.get(key), dict) else {}
        if not payload:
            print(f"     📊 {key}: no changes")
            return

        if key == "speaker_resolution":
            deterministic = len(payload.get("deterministic_corrections") or [])
            llm = len(payload.get("llm_corrections") or [])
            print(f"     📊 speaker: deterministic={deterministic}, llm={llm}")
        elif key == "grammar_refinement":
            print(
                "     📊 grammar: "
                f"titles={payload.get('title_count', 0)}, "
                f"sections={payload.get('section_count', 0)}, "
                f"llm={payload.get('used_llm', False)}"
            )
        elif key == "reading_audit":
            deterministic = len(payload.get("deterministic_corrections") or [])
            llm = len(payload.get("llm_corrections") or [])
            print(f"     📊 reading: deterministic={deterministic}, llm={llm}")
        elif key == "vocab_memory":
            print(
                "     📊 vocab memory: "
                f"new={payload.get('new_count', 0)}, "
                f"review={payload.get('review_count', 0)}, "
                f"new_meaning={payload.get('new_meaning_count', 0)}"
            )
        else:
            print(f"     📊 {key}: {payload}")

    def _print_database_summary(self, database_items: list[dict]) -> None:
        counts = {}
        for item in database_items or []:
            question_type = item.get("question_type") if isinstance(item, dict) else None
            if not question_type:
                continue
            counts[question_type] = counts.get(question_type, 0) + 1
        summary = ", ".join(f"{key}={counts[key]}" for key in sorted(counts)) or "none"
        print(f"     📊 database_items: total={len(database_items or [])} | {summary}")
