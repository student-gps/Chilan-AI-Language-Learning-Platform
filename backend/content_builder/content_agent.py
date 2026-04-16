import json
import re
import traceback
from pathlib import Path
from llm_providers import BaseLLMProvider
from tasks.content_extractor import Task1Extractor
from tasks.notes_extractor import Task1BTextbookNotesExtractor
from tasks.quiz_generator import Task2QuizGenerator
from tasks.video_director import Task3LessonVideoPlanner
from tasks.dialogue_audio import Task4BLessonAudioRenderer
from tasks.render_planner import Task4CExplanationComposer
from tasks.narration_audio import Task4DExplanationNarrator


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
                    "english": line.get("english", ""),
                    "words": line.get("words", []),
                })
        elif "chinese" in item:
            # Current format — preserve any existing pinyin if available.
            result.append({
                "role": item.get("role", ""),
                "chinese": item.get("chinese", ""),
                "pinyin": item.get("pinyin", ""),
                "english": item.get("english", ""),
                "words": item.get("words", []) or item.get("tokens", []),
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

    def generate_content(self, file_path: str, lesson_id: int, course_id: int = 1) -> dict | None:
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

            # 一次上传 PDF，全程复用
            shared_file = self.task1.llm.upload_pdf(file_path)

            # [Task 1] 提取对话与元数据
            base_data = self.task1.run(
                lesson_id=lesson_id,
                course_id=course_id,
                file_path=None,
                file_obj=shared_file
            )

            if not base_data:
                print("❌ Task 1 核心数据提取失败，终止后续管线。")
                return None

            # [Task 1B] 提取教材讲解素材（Language Notes / Grammar）
            teaching_material_result = self.task1b.run(
                lesson_id=lesson_id,
                course_id=course_id,
                file_path=None,
                file_obj=shared_file
            )
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
            lp_sections = teaching_materials.get("language_practice_sections", []) if isinstance(teaching_materials, dict) else []
            task2_result = self.task2.run(
                lesson_id=lesson_id,
                course_id=course_id,
                file_path=None,
                file_obj=shared_file,
                source_dialogues=dialogues_flat,
                raw_dialogues=raw_dialogues,
                language_practice_sections=lp_sections,
            )

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
            video_data = self.task3.run(
                metadata=metadata,
                dialogues=dialogues_flat,
                teaching_materials=teaching_materials,
                vocabulary=vocab_data,
                grammar=grammar_data
            )

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

            # [Task 4B] 中文课文逐句音频（语言无关，所有母语版本共享）
            try:
                audio_output_dir = self.memory_dir / "output_audio" / f"lesson{lesson_id}"
                lesson_audio_assets = self.task4b.render_sentence_audio_assets(
                    lesson_data=base_data,
                    output_dir=audio_output_dir,
                    include_speakers=False,
                    enable_subtitle=False,
                    public_base_url="/media/audio",
                )
                base_data["lesson_audio_assets"] = lesson_audio_assets.get("lesson_audio_assets", {})
                audio_count = len(base_data["lesson_audio_assets"].get("items", []))
                print(f"✨ 课文逐句音频已生成，共 {audio_count} 条。")
            except Exception as e:
                print(f"⚠️ Task 4B 音频生成失败，已跳过本课音频资产: {e}")
                base_data["lesson_audio_assets"] = {
                    "provider": "tencent_tts",
                    "mode": "sentence_audio",
                    "default_voice_type": getattr(self.task4b, "voice_type", None),
                    "role_voice_map": getattr(self.task4b, "role_voice_map", {}),
                    "codec": "mp3",
                    "sample_rate": 16000,
                    "include_speakers": False,
                    "storage_backend": "local",
                    "sentence_gap_ms": getattr(self.task4b, "sentence_gap_ms", 300),
                    "full_audio": {"status": "missing", "audio_url": "", "object_key": "", "local_audio_file": "", "codec": "mp3"},
                    "items": []
                }

            # 更新全局词汇记忆
            if vocab_data:
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
            return None

    def render_narration(self, lesson_data: dict, lesson_id: int) -> dict:
        """
        Stage 2 — 母语旁白音轨渲染（每种学习者母语各跑一次）

        包含：
          - Task 4D：根据 video_render_plan 中的旁白文本生成 TTS 音轨
          - 将实际 TTS 时长写回 render plan（供 Remotion 视频渲染使用）

        直接修改并返回传入的 lesson_data。
        """
        print(f"\n🎙️ [Stage 2] 开始旁白渲染 (Lesson ID: {lesson_id})")

        try:
            narration_audio_dir = self.memory_dir / "output_audio" / f"lesson{lesson_id}_narration"
            explanation_render_plan = lesson_data.get("video_render_plan", {}).get("explanation", {})
            narration_result = self.task4d.run(
                render_plan=explanation_render_plan,
                output_dir=narration_audio_dir,
            )
            lesson_data["explanation_narration_audio"] = narration_result

            if narration_result.get("status") == "ok":
                seg_count = narration_result.get("segment_count", 0)
                print(f"✨ 旁白音轨已生成，共 {seg_count} 段（{narration_result['audio_file']}）。")

                # 将实际 TTS 时长写回 render plan
                segment_timings = narration_result.get("segment_timings", {})
                segment_actual_durations = narration_result.get("segment_actual_durations", {})
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
