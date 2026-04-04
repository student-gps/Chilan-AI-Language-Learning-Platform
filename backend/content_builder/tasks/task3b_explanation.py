import json
from llm_providers import BaseLLMProvider


class Task3ExplanationGenerator:
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider

    def _build_prompt(self, metadata: dict, dialogues: list, teaching_materials: dict, vocabulary: list, grammar: list, batch_mode: str) -> str:
        context = {
            "metadata": metadata,
            "dialogues": dialogues,
            "teaching_materials": teaching_materials,
            "key_vocabulary": vocabulary[:12],
            "grammar_points": grammar[:8],
            "batch_mode": batch_mode,
        }
        content_str = json.dumps(context, ensure_ascii=False)

        if batch_mode == "foundation":
            batch_guidance = """
        【本轮生成目标】
        - 只生成前半段讲解内容。
        - 重点覆盖：逐句讲解(line_walkthrough) 与核心新词讲解(vocabulary_focus)。
        - 不要生成 grammar_focus。
        - 不要生成 recap。
        - 建议生成 3-5 个 segments。
            """
        else:
            batch_guidance = """
        【本轮生成目标】
        - 只生成后半段讲解内容。
        - 重点覆盖：语法讲解(grammar_focus) 与总结回顾(recap)。
        - 不要重复前半段已经讲过的逐句基础解释。
        - 必须包含 1 个 recap。
        - 建议生成 2-4 个 segments。
            """

        return f"""
        你是一位专业的中文教学视频老师。你的任务不是设计剧情，而是根据课文内容生成一段结构清晰、适合后续模板动画与配音合成的【教学讲解脚本】。
        只输出合法 JSON，不要包含任何 Markdown。

        课程内容：
        {content_str}

        {batch_guidance}

        【任务目标】
        1. 将本课拆分为 4-9 个讲解片段，按“逐句讲解 + 新词讲解 + 语法讲解 + 总结回顾”的顺序组织。
        2. 讲解对象是以英文为母语的中文学习者，英文讲解必须清晰自然、教学性强。
        3. 要先一句一句过课文内容，遇到新词或语法点时必须专门讲解。
        4. teaching_materials 中的 language_notes 和 grammar_sections 是本次讲解的重要依据，必须优先参考，不要只依赖对话正文自行推断。
        5. grammar_points 可作为补充素材，但教材原有的 grammar_sections 优先级更高。
        6. vocabulary 用于识别和组织高亮新词。
        7. 每个片段都要适合后续做成教学卡片视频，而不是影视剧情。
        8. 只保留一条英文主字幕/主讲解文本，不要输出中文整段讲稿。
        9. 中文内容只保留在重点词、重点句和屏幕展示字段里。
        10. on_screen_text.main_title 必须固定为本课课文标题。
        11. highlight_words 用于本段涉及的新词；grammar_points 用于本段涉及的新语法。

        【输出要求】
        1. global_config 中给出统一讲解风格，并明确 target audience。
        2. segments 中每条都必须说明其对应课文的哪一句或哪几句。
        3. narration 只保留 subtitle_en 一个字段。
        4. 不要输出 subtitle_tracks。
        5. estimated_duration_seconds 只是建议值，不是硬约束。
        6. 不要重复情景演绎内容，要强调解释和教学。

        【segment_type 可选值】
        "line_walkthrough", "vocabulary_focus", "grammar_focus", "usage_focus", "recap"

        【输出结构】
        {{
          "global_config": {{
            "teaching_style": "讲解风格描述",
            "target_audience": "English native speakers learning Chinese",
            "presenter_mode": "voice_over",
            "visual_style": "适合教学卡片和字幕动效的风格",
            "lesson_main_title": "本课课文标题"
          }},
          "segments": [
            {{
              "segment_id": 1,
              "segment_type": "line_walkthrough",
              "source_line_refs": [1],
              "segment_title": "片段标题",
              "teaching_goal": "这一段想教会学生什么",
              "narration": {{
                "subtitle_en": "English teaching script with key Chinese phrases embedded when needed"
              }},
              "on_screen_text": {{
                "main_title": "本课课文标题",
                "focus_text": "当前讲解句子或词语",
                "focus_pinyin": "拼音",
                "focus_gloss_en": "英文释义",
                "notes": "辅助说明"
              }},
              "highlight_words": [
                {{
                  "word": "新词",
                  "pinyin": "pinyin",
                  "english": "English meaning",
                  "explanation_en": "English explanation"
                }}
              ],
              "grammar_points": [
                {{
                  "pattern": "句型或语法点",
                  "explanation_en": "English explanation"
                }}
              ],
              "visual_notes": "后续制作教学卡片时的视觉提示",
              "estimated_duration_seconds": 12
            }}
          ]
        }}
        """

    def _request_batch(self, metadata: dict, dialogues: list, teaching_materials: dict, vocabulary: list, grammar: list, batch_mode: str) -> dict:
        prompt = self._build_prompt(metadata, dialogues, teaching_materials, vocabulary, grammar, batch_mode)
        result = self.llm.generate_structured_json(
            prompt,
            file_path=None,
            file_obj=None
        )
        return result if isinstance(result, dict) else {"global_config": {}, "segments": []}

    def _normalize_segment(self, segment: dict, fallback_id: int, lesson_title: str) -> dict:
        if not isinstance(segment, dict):
            segment = {}

        narration = segment.get("narration") if isinstance(segment.get("narration"), dict) else {}
        on_screen_text = segment.get("on_screen_text") if isinstance(segment.get("on_screen_text"), dict) else {}

        return {
            "segment_id": segment.get("segment_id", fallback_id),
            "segment_type": (segment.get("segment_type") or "line_walkthrough").strip() or "line_walkthrough",
            "source_line_refs": segment.get("source_line_refs", []) if isinstance(segment.get("source_line_refs"), list) else [],
            "segment_title": (segment.get("segment_title") or "").strip(),
            "teaching_goal": (segment.get("teaching_goal") or "").strip(),
            "narration": {
                "subtitle_en": ((narration.get("subtitle_en") or narration.get("en")) or "").strip()
            },
            "on_screen_text": {
                "main_title": (on_screen_text.get("main_title") or lesson_title).strip() or lesson_title,
                "focus_text": ((on_screen_text.get("focus_text") or on_screen_text.get("focus_hanzi")) or "").strip(),
                "focus_pinyin": (on_screen_text.get("focus_pinyin") or "").strip(),
                "focus_gloss_en": ((on_screen_text.get("focus_gloss_en") or on_screen_text.get("focus_english")) or "").strip(),
                "notes": (on_screen_text.get("notes") or "").strip(),
            },
            "highlight_words": segment.get("highlight_words", []) if isinstance(segment.get("highlight_words"), list) else [],
            "grammar_points": segment.get("grammar_points", []) if isinstance(segment.get("grammar_points"), list) else [],
            "visual_notes": (segment.get("visual_notes") or "").strip(),
            "estimated_duration_seconds": segment.get("estimated_duration_seconds", 12),
        }

    def run(self, metadata: dict, dialogues: list, teaching_materials: dict = None, vocabulary: list = None, grammar: list = None):
        print("  ▶️ [Task 3B] 正在生成课文教学讲解脚本...")

        teaching_materials = teaching_materials if isinstance(teaching_materials, dict) else {}
        vocabulary = vocabulary if vocabulary else []
        grammar = grammar if grammar else []

        foundation_result = self._request_batch(
            metadata=metadata,
            dialogues=dialogues or [],
            teaching_materials=teaching_materials,
            vocabulary=vocabulary,
            grammar=grammar,
            batch_mode="foundation",
        )
        advanced_result = self._request_batch(
            metadata=metadata,
            dialogues=dialogues or [],
            teaching_materials=teaching_materials,
            vocabulary=vocabulary,
            grammar=grammar,
            batch_mode="advanced",
        )

        lesson_title = metadata.get("title", "") if isinstance(metadata, dict) else ""
        foundation_global = foundation_result.get("global_config") if isinstance(foundation_result.get("global_config"), dict) else {}
        advanced_global = advanced_result.get("global_config") if isinstance(advanced_result.get("global_config"), dict) else {}
        merged_segments = []
        merged_segments.extend(foundation_result.get("segments", []) if isinstance(foundation_result.get("segments"), list) else [])
        merged_segments.extend(advanced_result.get("segments", []) if isinstance(advanced_result.get("segments"), list) else [])

        if merged_segments:
            normalized_result = {
                "global_config": {
                    "teaching_style": (foundation_global.get("teaching_style") or advanced_global.get("teaching_style") or "").strip(),
                    "target_audience": (foundation_global.get("target_audience") or advanced_global.get("target_audience") or "English native speakers learning Chinese").strip(),
                    "presenter_mode": (foundation_global.get("presenter_mode") or advanced_global.get("presenter_mode") or "voice_over").strip(),
                    "visual_style": (foundation_global.get("visual_style") or advanced_global.get("visual_style") or "").strip(),
                    "lesson_main_title": (foundation_global.get("lesson_main_title") or advanced_global.get("lesson_main_title") or lesson_title).strip() or lesson_title,
                },
                "segments": [
                    {
                        **self._normalize_segment(segment, index, lesson_title),
                        "segment_id": index
                    }
                    for index, segment in enumerate(merged_segments, start=1)
                ]
            }
            segments_count = len(normalized_result.get("segments", []))
            print(f"  ✨ 教学讲解脚本完成，共生成 {segments_count} 个讲解片段。")
            return normalized_result

        return {
            "global_config": {
                "teaching_style": "",
                "target_audience": "English native speakers learning Chinese",
                "presenter_mode": "voice_over",
                "visual_style": "",
                "lesson_main_title": metadata.get("title", "")
            },
            "segments": []
        }
