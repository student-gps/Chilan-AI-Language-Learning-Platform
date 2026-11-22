import json
import re
import traceback
import os
from pathlib import Path

from content_builder.core.artifacts import code_digest, file_digest, fingerprint
from content_builder.core.checkpoints import CheckpointStore
from content_builder.zh.integrated_chinese.quality import audit_lesson, require_quality

try:
    from content_builder.core.llm_providers import BaseLLMProvider
    from content_builder.zh.integrated_chinese.tasks.content_extractor import Task1Extractor
    from content_builder.zh.integrated_chinese.tasks.notes_extractor import Task1BTextbookNotesExtractor
    from content_builder.zh.integrated_chinese.tasks.quiz_generator import Task2QuizGenerator
    from content_builder.zh.integrated_chinese.tasks.video_director import Task3LessonVideoPlanner
    from content_builder.zh.integrated_chinese.tasks.dialogue_audio import Task4BLessonAudioRenderer
    from content_builder.zh.integrated_chinese.tasks.render_planner import Task4CExplanationComposer
    from content_builder.zh.integrated_chinese.tasks.narration_audio import Task4DExplanationNarrator
except ImportError:
    from content_builder.core.llm_providers import BaseLLMProvider
    from content_builder.zh.integrated_chinese.tasks.content_extractor import Task1Extractor
    from content_builder.zh.integrated_chinese.tasks.notes_extractor import Task1BTextbookNotesExtractor
    from content_builder.zh.integrated_chinese.tasks.quiz_generator import Task2QuizGenerator
    from content_builder.zh.integrated_chinese.tasks.video_director import Task3LessonVideoPlanner
    from content_builder.zh.integrated_chinese.tasks.dialogue_audio import Task4BLessonAudioRenderer
    from content_builder.zh.integrated_chinese.tasks.render_planner import Task4CExplanationComposer
    from content_builder.zh.integrated_chinese.tasks.narration_audio import Task4DExplanationNarrator


def _normalize_dialogues(dialogues: list) -> list:
    """
    Ensure dialogues are in the flat {role, chinese, english} format that
    Task3 and Task2 expect.

    Handles the legacy format where each item is:
      {"lines": [{"role": ..., "english": ..., "words": [{"cn": ..., "py": ...}]}]}
    and converts it to:
      [{"role": ..., "chinese": "...", "pinyin": "...", "english": "..."}]
    """
    if not isinstance(dialogues, list):
        return []
    result = []
    for item in dialogues:
        if not isinstance(item, dict):
            continue
        if "lines" in item:
            # Legacy format — reconstruct chinese from words array
            for line in item.get("lines", []):
                if not isinstance(line, dict):
                    continue
                chinese = "".join(
                    w.get("cn", "") for w in line.get("words", [])
                    if isinstance(w, dict)
                )
                pinyin = " ".join(
                    w.get("py", "").strip()
                    for w in line.get("words", [])
                    if isinstance(w, dict) and (w.get("py") or "").strip()
                ).strip()
                result.append({
                    "role": line.get("role", ""),
                    "chinese": chinese,
                    "pinyin": pinyin,
                    "translation": line.get("translation", ""),
                    "tokens": line.get("words", []),
                })
        elif "chinese" in item:
            # Current format — preserve any existing pinyin if available.
            result.append({
                "role": item.get("role", ""),
                "chinese": item.get("chinese", ""),
                "pinyin": item.get("pinyin", ""),
                "translation": item.get("translation", ""),
                "tokens": item.get("tokens", []) or item.get("words", []),
            })
    return result


class ContentCreatorAgent:
    def __init__(self, provider: BaseLLMProvider, memory_dir: Path):
        self.provider = provider
        self.memory_dir = memory_dir
        self.task1 = Task1Extractor(provider)
        self.task1b = Task1BTextbookNotesExtractor(provider)
        self.task2 = Task2QuizGenerator(provider, memory_dir)
        self.task3 = Task3LessonVideoPlanner(provider)
        self.task4b = Task4BLessonAudioRenderer()
        self.task4c = Task4CExplanationComposer()
        self.task4d = Task4DExplanationNarrator()
        self.task4d.duration_mode = "actual"
        self.task4d.duration_buffer_seconds = 0.5

    def generate_content(self, file_path: str, lesson_id: int, course_id: int = 1, *,
                         checkpoint_dir: Path | None = None, render_lesson_audio: bool = True,
                         update_memory: bool = True, force: bool = False, raise_on_error: bool = False) -> dict | None:
        """
        Stage 1 — 语言无关内容生成（跑一次，所有语言版本共享）

        包含：
          - LLM 提取对话、笔记、词汇、题库、视频脚本、渲染计划
          - 中文课文逐句音频（Task 4B，与学习者母语无关）

        返回 lesson_data dict，失败返回 None。
        """
        print(f"\n🚀 [Stage 1] 开始内容生成: {Path(file_path).name} (Lesson ID: {lesson_id})")

        try:
            if hasattr(self.provider, "reset_usage_log"):
                self.provider.reset_usage_log()

            store = CheckpointStore(checkpoint_dir) if checkpoint_dir else None
            shared_file = None
            def pdf():
                nonlocal shared_file
                if shared_file is None:
                    shared_file = self.task1.llm.upload_pdf(file_path)
                return shared_file
            source_digest = file_digest(Path(file_path))
            task_files = {"extract_text": ["content_extractor.py"], "extract_notes": ["notes_extractor.py"],
                          "practice": ["quiz_generator.py"], "teaching": ["video_director.py", "_explanation_writer.py"]}
            llm_settings = fingerprint({key: value for key, value in os.environ.items() if key.startswith(("LLM_", "CONTENT_TASK", "PRACTICE_")) and not any(secret in key for secret in ("KEY", "SECRET", "TOKEN", "PASSWORD"))})
            common = {"source": source_digest, "lesson_id": lesson_id, "course_id": course_id, "settings": llm_settings,
                      "provider": type(self.provider).__name__, "model": getattr(self.provider, "model_id", "")}
            def cached(name, inputs, action):
                digest = code_digest([Path(__file__).parent / "tasks" / filename for filename in task_files[name]])
                def checked():
                    value = action()
                    valid = isinstance(value, dict) and bool(value)
                    if valid and name == "extract_text":
                        valid = bool((value.get("course_content") or {}).get("dialogues"))
                    elif valid and name == "practice":
                        valid = bool(value.get("vocabulary")) and bool(value.get("database_items"))
                    elif valid and name == "teaching":
                        valid = bool((value.get("explanation") or {}).get("segments"))
                    if not valid:
                        raise ValueError(f"{name} returned incomplete content")
                    return value
                return store.run(name, {**common, "code": digest, "inputs": inputs}, checked, force=force) if store else checked()

            # [Task 1] 提取对话与元数据
            base_data = cached("extract_text", {}, lambda: self.task1.run(
                lesson_id=lesson_id,
                course_id=course_id,
                file_path=None,
                file_obj=pdf()
            ))

            if not base_data:
                print("❌ Task 1 核心数据提取失败，终止后续管线。")
                return None

            # [Task 1B] 提取教材讲解素材（Language Notes / Grammar）
            teaching_material_result = cached("extract_notes", {}, lambda: self.task1b.run(
                lesson_id=lesson_id,
                course_id=course_id,
                file_path=None,
                file_obj=pdf()
            ))
            teaching_materials = (
                teaching_material_result.get("teaching_materials", {})
                if isinstance(teaching_material_result, dict)
                else {}
            )
            base_data["teaching_materials"] = teaching_materials

            # 归一化 dialogues 格式（兼容旧版逐字 words 结构）
            raw_dialogues = base_data.get("course_content", {}).get("dialogues", [])
            dialogues_flat = _normalize_dialogues(raw_dialogues)

            # [Task 2] 提取词汇（含历史记录）+ 提取语法 + 生成题库
            prior_memory = {word: [entry for entry in entries if int(entry.get("lesson_id") or 0) < lesson_id]
                            for word, entries in self.task2.global_vocab.items() if isinstance(entries, list)}
            task2_result = cached("practice", {"dialogues": raw_dialogues, "history": prior_memory}, lambda: self.task2.run(
                lesson_id=lesson_id,
                course_id=course_id,
                file_path=None,
                file_obj=pdf(),
                source_dialogues=dialogues_flat,
                raw_dialogues=raw_dialogues,
            ))

            vocab_data = []
            grammar_data = []
            if task2_result and isinstance(task2_result, dict):
                vocab_data = task2_result.get("vocabulary", [])
                base_data["course_content"]["vocabulary"] = vocab_data
                base_data["database_items"] = task2_result.get("database_items", [])
                grammar_data = task2_result.get("grammar_practice", [])
            else:
                print("⚠️ Task 2 返回数据异常，填充空列表。")
                base_data["course_content"]["vocabulary"] = []
                base_data["database_items"] = []

            # [Task 3] 生成教学视频脚本
            metadata = base_data.get("lesson_metadata", {})
            video_data = cached("teaching", {"metadata": metadata, "dialogues": dialogues_flat, "materials": teaching_materials, "vocab": vocab_data, "grammar": grammar_data}, lambda: self.task3.run(
                metadata=metadata,
                dialogues=dialogues_flat,
                teaching_materials=teaching_materials,
                vocabulary=vocab_data,
                grammar=grammar_data
            ))

            if video_data and isinstance(video_data, dict):
                base_data["video_plan"] = video_data
            else:
                base_data["video_plan"] = {
                    "lesson_video_plan": {},
                    "dramatization": {"global_config": {}, "scenes": []},
                    "explanation": {"global_config": {}, "segments": []},
                    "production_notes": {"recommended_workflow": [], "remarks": ""}
                }

            # [Task 4C] 生成讲解渲染计划
            try:
                explanation_render_plan = self.task4c.run(
                    metadata=metadata,
                    explanation=base_data.get("video_plan", {}).get("explanation", {}),
                )
                base_data["video_render_plan"] = {"explanation": explanation_render_plan}
                render_segment_count = len(
                    (((base_data.get("video_render_plan") or {}).get("explanation") or {}).get("segments") or [])
                )
                print(f"✨ 教学讲解模板视频计划已生成，共 {render_segment_count} 段。")
            except Exception as e:
                print(f"⚠️ Task 4C 讲解模板计划生成失败，已回退为空计划: {e}")
                base_data["video_render_plan"] = {
                    "explanation": {
                        "lesson_id": metadata.get("lesson_id"),
                        "course_id": metadata.get("course_id"),
                        "lesson_title": metadata.get("title", ""),
                        "target_audience": "English native speakers learning Chinese",
                        "video_style": {
                            "presenter_mode": "voice_over",
                            "teaching_style": "",
                            "visual_style": "",
                            "aspect_ratio": "16:9",
                            "safe_area": "title_safe",
                        },
                        "segments": [],
                        "timeline": {"total_duration_seconds": 0, "segment_count": 0},
                        "renderer_notes": {
                            "recommended_renderer": "template_video",
                            "recommended_stack": ["react_templates", "motion_graphics", "ffmpeg_or_remotion"],
                            "remarks": "Fallback empty explanation render plan.",
                        }
                    }
                }

            from content_builder.zh.integrated_chinese.tasks.schema_validator import normalize_stage1_output, IntegratedChineseStage1Validator
            base_data = normalize_stage1_output(base_data, lesson_id=lesson_id, course_id=course_id)
            IntegratedChineseStage1Validator().validate(base_data)
            base_data["workflow_version"] = "1.0"
            base_data["source_manifest"] = {"file": str(Path(file_path).resolve()), "sha256": source_digest}
            from content_builder.core.artifacts import atomic_write_json
            report = audit_lesson(base_data, artifact_root=self.memory_dir)
            atomic_write_json(self.memory_dir / "reports/en" / f"lesson{lesson_id}_content.json", report)
            if not report["ok"] and store:
                codes = {issue["code"] for issue in report["issues"] if issue["severity"] == "error"}
                for task_name, prefixes in {
                    "extract_text": {"empty_source", "line_support", "identity"},
                    "extract_notes": {"grammar_skeleton"},
                    "practice": {"empty_vocabulary", "vocabulary_shape", "vocabulary_example", "empty_practice", "question_type", "question_identity", "question_id", "answer", "listening_source"},
                    "teaching": {"empty_plan", "template", "segment_id", "empty_narration", "tts_language", "tts_pinyin", "teaching_coverage", "grammar_coverage", "note_coverage", "slide_density"},
                }.items():
                    if codes & prefixes:
                        store.invalidate(task_name)
            require_quality(report)

            # [Task 4B] 中文课文逐句音频（语言无关，所有母语版本共享）
            try:
                audio_output_dir = self.memory_dir / "output_audio" / f"lesson{lesson_id}"
                lesson_audio_assets = self.task4b.render_sentence_audio_assets(
                    lesson_data=base_data,
                    output_dir=audio_output_dir,
                    include_speakers=False,
                    enable_subtitle=False,
                    public_base_url="/media/audio",
                ) if render_lesson_audio else {"lesson_audio_assets": {"status": "pending", "items": []}}
                base_data["lesson_audio_assets"] = lesson_audio_assets.get("lesson_audio_assets", {})
                audio_count = len(base_data["lesson_audio_assets"].get("items", []))
                print(f"✨ 课文逐句音频已生成，共 {audio_count} 条。")
            except Exception as e:
                raise RuntimeError(f"Lesson audio failed: {e}") from e

            # 更新全局词汇记忆
            if vocab_data and update_memory:
                self.task2.save_memory(vocab_data, lesson_id)
                print(f"✨ 动态词典已更新，本课新增 {len(vocab_data)} 个词义记录。")

            # 花费汇总（LLM + 中文 TTS）
            usage_summary = self.provider.get_usage_summary() if hasattr(self.provider, "get_usage_summary") else {}
            base_data["llm_usage"] = usage_summary

            tencent_tts_chars = sum(
                len(item.get("source_text", ""))
                for item in base_data.get("lesson_audio_assets", {}).get("items", [])
            )
            tencent_cost_cny = tencent_tts_chars * 0.0002
            tencent_cost_usd = tencent_cost_cny / 7.2
            llm_cost_usd = usage_summary.get("estimated_cost_usd", 0.0) if usage_summary else 0.0

            print("=" * 55)
            print("💰 Stage 1 花费汇总")
            print(f"   LLM ({usage_summary.get('provider', 'N/A')})  "
                  f"调用 {usage_summary.get('calls', 0)} 次 | "
                  f"{usage_summary.get('total_tokens', 0):,} tokens | "
                  f"≈ ${llm_cost_usd:.4f}")
            print(f"   腾讯云 TTS  "
                  f"{tencent_tts_chars:,} 字符 | ≈ ¥{tencent_cost_cny:.3f} (≈ ${tencent_cost_usd:.4f})")
            print(f"   {'─' * 40}")
            print(f"   合计估算  ≈ ${llm_cost_usd + tencent_cost_usd:.4f}")
            print("=" * 55)
            print(f"✅ Stage 1 完成！")
            return base_data

        except Exception as e:
            print(f"❌ Stage 1 执行中断: {e}")
            traceback.print_exc()
            if raise_on_error:
                raise
            return None

    def render_narration(self, lesson_data: dict, lesson_id: int, lang: str = "en") -> dict:
        """
        Stage 2 — 母语旁白音轨渲染（每种学习者母语各跑一次）

        包含：
          - Task 4D：根据 video_render_plan 中的旁白文本生成 TTS 音轨
          - 将实际 TTS 时长写回 render plan（供 Remotion 视频渲染使用）

        直接修改并返回传入的 lesson_data。
        """
        print(f"\n🎙️ [Stage 2] 开始旁白渲染 (Lesson ID: {lesson_id})")

        try:
            lang_suffix = f"_{lang}" if lang != "en" else ""
            narration_audio_dir = self.memory_dir / "output_audio" / lang / f"lesson{lesson_id}_narration"
            explanation_render_plan = lesson_data.get("video_render_plan", {}).get("explanation", {})
            narration_result = self.task4d.run(
                render_plan=explanation_render_plan,
                output_dir=narration_audio_dir,
                lang=lang,
            )
            lesson_data["explanation_narration_audio"] = narration_result

            if narration_result.get("status") == "ok":
                seg_count = narration_result.get("segment_count", 0)
                print(f"✨ 旁白音轨已生成，共 {seg_count} 段（{narration_result['audio_file']}）。")

                # 将实际 TTS 时长写回 render plan
                segment_timings = narration_result.get("segment_timings", {})
                segment_actual_durations = narration_result.get("segment_actual_durations", {})
                segment_sentences = narration_result.get("segment_sentences", {})
                plan_segments = (
                    lesson_data.get("video_render_plan", {})
                    .get("explanation", {})
                    .get("segments", [])
                )
                for seg in plan_segments:
                    seg_key = str(seg.get("segment_id") or seg.get("segment_order", ""))
                    if seg_key in segment_timings:
                        seg["sentence_timings_seconds"] = segment_timings[seg_key]
                    if seg_key in segment_actual_durations:
                        seg["duration_seconds"] = segment_actual_durations[seg_key]
                    if seg_key in segment_sentences:
                        seg["sentence_texts"] = segment_sentences[seg_key]

                cursor = 0.0
                for seg in plan_segments:
                    seg["start_time_seconds"] = round(cursor, 3)
                    cursor += float(seg.get("duration_seconds", 0))

                timeline = (
                    lesson_data.get("video_render_plan", {})
                    .get("explanation", {})
                    .get("timeline", {})
                )
                timeline["total_duration_seconds"] = round(cursor, 3)
                timeline["segment_count"] = len(plan_segments)
            else:
                print(f"⚠️ 旁白生成跳过/失败: {narration_result.get('reason', '')}")

        except Exception as e:
            print(f"⚠️ Stage 2 旁白生成异常，已跳过: {e}")
            lesson_data["explanation_narration_audio"] = {"status": "error", "reason": str(e)}

        # 花费汇总（旁白 TTS）
        _zh_marker_re = re.compile(r'\[zh:([^\]]+)\]')
        narration_chars = 0
        for seg in (lesson_data.get("video_render_plan", {}).get("explanation", {}).get("segments", [])):
            text = (seg.get("narration_track") or {}).get("subtitle_en", "").strip()
            if text:
                tts_text = _zh_marker_re.sub(lambda m: m.group(1).strip() + ',', text)
                narration_chars += len(tts_text)

        tts_provider = getattr(self.task4d, "provider", "openai")
        tts_model = getattr(self.task4d, "model", "")
        if tts_provider == "ali":
            cost_usd = narration_chars * 0.000115 / 7.2
            print(f"💰 Stage 2 旁白 TTS: CosyVoice ({tts_model})  {narration_chars:,} 字符 | ≈ ¥{narration_chars * 0.000115:.3f} (≈ ${cost_usd:.4f})")
        else:
            cost_per_1k = 0.030 if tts_model == "tts-1-hd" else 0.015
            cost_usd = narration_chars / 1000.0 * cost_per_1k
            print(f"💰 Stage 2 旁白 TTS: OpenAI ({tts_model})  {narration_chars:,} 字符 | ≈ ${cost_usd:.4f}")

        print(f"✅ Stage 2 完成！")
        return lesson_data
