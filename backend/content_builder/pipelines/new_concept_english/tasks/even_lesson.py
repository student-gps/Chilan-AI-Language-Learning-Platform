from __future__ import annotations

import json

try:
    from content_builder.core.llm_providers import BaseLLMProvider
    from content_builder.pipelines.new_concept_english.book_profiles import book1
except ImportError:
    from core.llm_providers import BaseLLMProvider
    from pipelines.new_concept_english.book_profiles import book1


class Task2EvenLessonDrillExtractor:
    """Extract the even-numbered source lesson as pattern drills."""

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider

    def _build_prompt(self, lesson_slice: book1.AppLessonSlice, support_language: str) -> str:
        source_odd, source_even = lesson_slice.source_lessons
        context = {
            "book": 1,
            "lesson_id": lesson_slice.lesson_slug,
            "source_lessons": list(lesson_slice.source_lessons),
            "target_language": "en",
            "support_language": support_language,
        }
        return f"""
        你是一名新概念英语第一册偶数课解析专家。请解析提供的 4 页 PDF，
        重点提取原教材 Lesson {source_even} 的句型替换练习和书面练习。
        只输出合法 JSON，不要 Markdown。

        输入上下文：
        {json.dumps(context, ensure_ascii=False)}

        任务边界：
        - Lesson {source_odd} 是主课文，只作为理解句型来源。
        - Lesson {source_even} 是本任务重点，通常包含图片替换词、Pattern drill、Written exercise。

        提取规则：
        1. pattern_drills 至少包含一个核心句型；如果页面上是问答练习，要保留 response_patterns。
        2. pattern 中可替换位置统一写作 {{item}}，例如 "Is this your {{item}}?"。
        3. slots 来自偶数课图片/词汇表，每项包含 text、pronunciation、translation、image_index。
        4. generated_prompts 按图片顺序列出替换后的完整英文句子。
        5. writing_exercises 提取书面练习指令和可见句子；无法可靠提取则返回空数组。

        输出结构：
        {{
          "pattern_drills": [
            {{
              "source_lesson": {source_even},
              "pattern": "Pattern with {{item}}",
              "translation_pattern": "中文句型",
              "response_patterns": [
                {{"text": "Yes, ...", "translation": "中文"}}
              ],
              "slots": [
                {{"text": "word", "pronunciation": "/.../", "translation": "中文", "image_index": 1}}
              ],
              "generated_prompts": [
                {{"text": "Full English sentence.", "translation": "中文", "image_index": 1}}
              ]
            }}
          ],
          "writing_exercises": [
            {{
              "source_lesson": {source_even},
              "instruction": "English instruction",
              "translation": "中文说明",
              "sentences": ["English sentence"]
            }}
          ]
        }}
        """

    def run(
        self,
        lesson_slice: book1.AppLessonSlice,
        support_language: str = "zh",
        file_path: str | None = None,
        file_obj=None,
    ) -> dict:
        print("  ▶️ [NCE Task 2] 提取偶数课句型/替换练习...")
        result = self.llm.generate_structured_json(
            self._build_prompt(lesson_slice, support_language),
            file_path=file_path,
            file_obj=file_obj,
        )
        result = result if isinstance(result, dict) else {}
        pattern_drills = result.get("pattern_drills") if isinstance(result.get("pattern_drills"), list) else []
        writing_exercises = result.get("writing_exercises") if isinstance(result.get("writing_exercises"), list) else []
        print(f"  ✨ Task 2 完成，句型 {len(pattern_drills)} 组，书面练习 {len(writing_exercises)} 组。")
        return {
            "pattern_drills": pattern_drills,
            "writing_exercises": writing_exercises,
        }
