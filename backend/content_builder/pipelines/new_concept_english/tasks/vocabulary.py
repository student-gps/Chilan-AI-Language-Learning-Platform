from __future__ import annotations

import json
import re

try:
    from content_builder.core.llm_providers import BaseLLMProvider
    from content_builder.pipelines.new_concept_english.book_profiles import book1
    from content_builder.pipelines.new_concept_english.tasks.content_extractor import _normalize_vocabulary
except ImportError:
    from core.llm_providers import BaseLLMProvider
    from pipelines.new_concept_english.book_profiles import book1
    from pipelines.new_concept_english.tasks.content_extractor import _normalize_vocabulary


class Task3VocabularyExtractor:
    """Extract vocabulary from both the odd text lesson and the even drill lesson."""

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
        你是一名英语教材词汇提取专家。请解析提供的 New Concept English 第一册 4 页 PDF，
        提取 Lesson {source_odd} 和 Lesson {source_even} 的 New words and expressions。
        只输出合法 JSON，不要 Markdown。

        输入上下文：
        {json.dumps(context, ensure_ascii=False)}

        规则：
        1. 必须同时提取两个 source lessons 的词汇。
        2. Lesson {source_odd} 的词 role="dialogue_word"。
        3. Lesson {source_even} 的词 role="pattern_slot"。
        4. 字段固定为 term、pronunciation、part_of_speech、translation、source_lesson、role、image_index、example_sentence。
        5. example_sentence 如果教材里有现成例句就提取；没有则先留空对象，不要编造。
        6. translation 使用简体中文，part_of_speech 使用简短英文词性。
        7. 不要提取页码、栏目标题、练习编号。

        输出结构：
        {{
          "vocabulary": [
            {{
              "term": "word",
              "pronunciation": "/.../",
              "part_of_speech": "noun",
              "translation": "中文释义",
              "source_lesson": {source_odd},
              "role": "dialogue_word",
              "image_index": 1,
              "example_sentence": {{"text": "", "translation": "", "line_ref": 1}}
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
    ) -> list[dict]:
        print("  ▶️ [NCE Task 3.1] 提取奇偶两课词汇...")
        result = self.llm.generate_structured_json(
            self._build_prompt(lesson_slice, support_language),
            file_path=file_path,
            file_obj=file_obj,
        )
        raw_vocabulary = result.get("vocabulary", []) if isinstance(result, dict) else []
        vocabulary = _normalize_vocabulary(raw_vocabulary, lesson_slice.source_lessons)
        print(f"  ✨ Task 3.1 完成，词汇 {len(vocabulary)} 条。")
        return vocabulary


class Task3BExampleBackfiller:
    """Backfill vocabulary examples from extracted anchor lines and even-lesson drills."""

    _WORD_BOUNDARY = r"(?<![A-Za-z]){term}(?![A-Za-z])"

    def run(self, vocabulary: list[dict], anchor: dict, pattern_drills: list[dict]) -> list[dict]:
        print("  ▶️ [NCE Task 3.2] 回填词汇例句...")
        lines = anchor.get("lines") if isinstance(anchor.get("lines"), list) else []
        filled = []
        backfilled_count = 0

        for item in vocabulary or []:
            if not isinstance(item, dict):
                continue
            normalized = dict(item)
            example = normalized.get("example_sentence") if isinstance(normalized.get("example_sentence"), dict) else {}
            if not (example.get("text") or "").strip():
                example = self._find_anchor_example(normalized, lines) or self._find_drill_example(normalized, pattern_drills) or {}
                if example:
                    backfilled_count += 1
            normalized["example_sentence"] = example
            filled.append(normalized)

        print(f"  ✨ Task 3.2 完成，回填例句 {backfilled_count} 条。")
        return filled

    def _find_anchor_example(self, vocab_item: dict, lines: list[dict]) -> dict | None:
        term = (vocab_item.get("term") or "").strip()
        if not term:
            return None
        pattern = re.compile(self._WORD_BOUNDARY.format(term=re.escape(term)), re.IGNORECASE)
        for line in lines:
            if not isinstance(line, dict):
                continue
            text = (line.get("text") or "").strip()
            if text and pattern.search(text):
                return {
                    "text": text,
                    "translation": (line.get("translation") or "").strip(),
                    "line_ref": line.get("line_ref"),
                    "source": "anchor",
                }
        return None

    def _find_drill_example(self, vocab_item: dict, pattern_drills: list[dict]) -> dict | None:
        term = (vocab_item.get("term") or "").strip()
        if not term:
            return None
        for drill in pattern_drills or []:
            if not isinstance(drill, dict):
                continue
            for prompt in drill.get("generated_prompts") or []:
                if not isinstance(prompt, dict):
                    continue
                text = (prompt.get("text") or "").strip()
                pattern = re.compile(self._WORD_BOUNDARY.format(term=re.escape(term)), re.IGNORECASE)
                if text and pattern.search(text):
                    return {
                        "text": text,
                        "translation": (prompt.get("translation") or "").strip(),
                        "source": "pattern_drill",
                        **({"image_index": prompt.get("image_index")} if prompt.get("image_index") is not None else {}),
                    }
        return None
