from __future__ import annotations

import json

try:
    from content_builder.core.llm_providers import BaseLLMProvider
    from content_builder.pipelines.new_concept_english.book_profiles import book1
except ImportError:
    from core.llm_providers import BaseLLMProvider
    from pipelines.new_concept_english.book_profiles import book1


class Task4GrammarPatternExtractor:
    """Extract notes, usage explanations, and grammar patterns for teaching."""

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider

    def _build_prompt(
        self,
        lesson_slice: book1.AppLessonSlice,
        anchor: dict,
        pattern_drills: list[dict],
        vocabulary: list[dict],
        support_language: str,
    ) -> str:
        source_odd, source_even = lesson_slice.source_lessons
        context = {
            "lesson_id": lesson_slice.lesson_slug,
            "source_lessons": list(lesson_slice.source_lessons),
            "anchor_title": anchor.get("title", ""),
            "anchor_lines": [
                {
                    "line_ref": line.get("line_ref"),
                    "speaker": line.get("speaker"),
                    "text": line.get("text"),
                    "translation": line.get("translation"),
                }
                for line in (anchor.get("lines") or [])
                if isinstance(line, dict)
            ],
            "pattern_drills": pattern_drills,
            "vocabulary_terms": [v.get("term") for v in vocabulary if isinstance(v, dict)],
        }
        return f"""
        你是一名面向中文母语者的英语语法讲解素材提取专家。请解析提供的 4 页 PDF，
        提取 Lesson {source_odd} 和 Lesson {source_even} 中真正适合教学讲解的 Notes on the text、
        核心句型、语法点和用法说明。只输出合法 JSON，不要 Markdown。

        已提取上下文：
        {json.dumps(context, ensure_ascii=False)}

        规则：
        1. notes_on_text 只提取教材注释或课文中必须解释的表达，不要泛泛总结。
        2. grammar_sections 要覆盖主课文和偶数课句型，尤其是可替换 pattern。
        3. explanation 使用简体中文，pattern/example 保留英文。
        4. examples 优先来自课文或偶数课练习，不要编造教材外长例句。
        5. lesson_flow 固定服务于后续视频：scene_setup、anchor_walkthrough、pattern_focus、vocabulary_in_pattern、guided_practice。

        输出结构：
        {{
          "lesson_flow": ["scene_setup", "anchor_walkthrough", "pattern_focus", "vocabulary_in_pattern", "guided_practice"],
          "notes_on_text": [
            {{
              "focus_text": "English expression",
              "translation": "中文",
              "explanation": "中文讲解",
              "source_lesson": {source_odd}
            }}
          ],
          "grammar_sections": [
            {{
              "title": "Grammar title",
              "explanation": "中文讲解",
              "patterns": [
                {{"pattern": "English pattern", "translation": "中文句型"}}
              ],
              "examples": [
                {{"text": "English example", "translation": "中文"}}
              ],
              "source_lesson": {source_even}
            }}
          ]
        }}
        """

    def run(
        self,
        lesson_slice: book1.AppLessonSlice,
        anchor: dict,
        pattern_drills: list[dict],
        vocabulary: list[dict],
        support_language: str = "zh",
        file_path: str | None = None,
        file_obj=None,
    ) -> dict:
        print("  ▶️ [NCE Task 4] 提取语法/课文注释讲解素材...")
        result = self.llm.generate_structured_json(
            self._build_prompt(lesson_slice, anchor, pattern_drills, vocabulary, support_language),
            file_path=file_path,
            file_obj=file_obj,
        )
        result = result if isinstance(result, dict) else {}
        teaching_materials = {
            "lesson_flow": result.get("lesson_flow") if isinstance(result.get("lesson_flow"), list) else [],
            "notes_on_text": result.get("notes_on_text") if isinstance(result.get("notes_on_text"), list) else [],
            "grammar_sections": result.get("grammar_sections") if isinstance(result.get("grammar_sections"), list) else [],
        }
        print(
            "  ✨ Task 4 完成，"
            f"notes {len(teaching_materials['notes_on_text'])} 条，"
            f"grammar {len(teaching_materials['grammar_sections'])} 条。"
        )
        return teaching_materials
