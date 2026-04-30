from __future__ import annotations

import json

try:
    from content_builder.core.llm_providers import BaseLLMProvider
    from content_builder.pipelines.new_concept_english.book_profiles import book1
    from content_builder.pipelines.new_concept_english.tasks.content_extractor import _normalize_tokens
except ImportError:
    from core.llm_providers import BaseLLMProvider
    from pipelines.new_concept_english.book_profiles import book1
    from pipelines.new_concept_english.tasks.content_extractor import _normalize_tokens


class Task1AnchorTextExtractor:
    """Extract the odd-numbered source lesson as the app lesson anchor text."""

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider

    def _build_prompt(self, lesson_slice: book1.AppLessonSlice, support_language: str) -> str:
        source_odd, source_even = lesson_slice.source_lessons
        context = {
            "book": 1,
            "lesson_id": lesson_slice.lesson_slug,
            "source_lessons": list(lesson_slice.source_lessons),
            "pdf_pages": list(lesson_slice.pdf_pages),
            "target_language": "en",
            "support_language": support_language,
        }
        return f"""
        你是一名教材课文提取专家。请解析提供的 New Concept English 第一册 4 页 PDF，
        只提取原教材 Lesson {source_odd} 的主课文/对话，输出合法 JSON，不要 Markdown。

        输入上下文：
        {json.dumps(context, ensure_ascii=False)}

        页面结构：
        - 前 2 页：Lesson {source_odd}，包含主课文/对话、New words and expressions、Notes on the text、参考译文。
        - 后 2 页：Lesson {source_even}，是配套句型/替换练习；本任务只用于理解上下文，不要把它提取为 anchor。

        提取规则：
        1. lesson_metadata.title 使用 Lesson {source_odd} 的英文标题。
        2. lesson_metadata.title_localized 使用自然简体中文标题。
        3. content_type 只能是 dialogue、passage、dialogue_pattern、passage_pattern。
        4. anchor.type 如果是人物轮流说话则用 dialogue；如果是短文叙述则用 passage。
        5. anchor.lines 按原文顺序提取英文。每行包含 line_ref、speaker、text、translation。
        6. translation 优先使用教材参考译文；如果参考译文没有逐句对应，请给出自然简体中文译文。
        7. dialogue 课若教材没有明确角色名，可使用 Speaker A / Speaker B；passage 用 Narrator。
        8. 严禁提取目录、页眉、页脚、页码、练习编号等噪声。

        输出结构：
        {{
          "lesson_metadata": {{
            "title": "English title",
            "title_localized": "中文标题",
            "content_type": "dialogue_pattern"
          }},
          "course_content": {{
            "anchor": {{
              "type": "dialogue",
              "source_lesson": {source_odd},
              "title": "English title",
              "listening_question": {{"text": "", "translation": "", "answer": ""}},
              "lines": [
                {{
                  "line_ref": 1,
                  "speaker": "Speaker A",
                  "text": "English line",
                  "translation": "中文翻译"
                }}
              ]
            }}
          }}
        }}
        """

    def run(
        self,
        lesson_slice: book1.AppLessonSlice,
        support_language: str = "zh",
        file_path: str | None = None,
        file_obj=None,
    ) -> dict:
        print("  ▶️ [NCE Task 1] 提取奇数课主课文/对话...")
        result = self.llm.generate_structured_json(
            self._build_prompt(lesson_slice, support_language),
            file_path=file_path,
            file_obj=file_obj,
        )
        result = result if isinstance(result, dict) else {}
        metadata = result.get("lesson_metadata") if isinstance(result.get("lesson_metadata"), dict) else {}
        course_content = result.get("course_content") if isinstance(result.get("course_content"), dict) else {}
        anchor = course_content.get("anchor") if isinstance(course_content.get("anchor"), dict) else {}

        anchor["lines"] = _normalize_tokens(
            anchor.get("lines") if isinstance(anchor.get("lines"), list) else [],
            vocabulary=[],
        )
        anchor["type"] = (anchor.get("type") or "dialogue").strip()
        anchor["source_lesson"] = int(anchor.get("source_lesson") or lesson_slice.source_lessons[0])
        anchor["title"] = (anchor.get("title") or metadata.get("title") or lesson_slice.lesson_slug).strip()
        if not isinstance(anchor.get("listening_question"), dict):
            anchor["listening_question"] = {"text": "", "translation": "", "answer": ""}

        print(f"  ✨ Task 1 完成，课文行数 {len(anchor['lines'])}。")
        return {
            "lesson_metadata": {
                "title": (metadata.get("title") or anchor.get("title") or lesson_slice.lesson_slug).strip(),
                "title_localized": (metadata.get("title_localized") or "").strip(),
                "content_type": (metadata.get("content_type") or "dialogue_pattern").strip(),
            },
            "course_content": {"anchor": anchor},
        }
