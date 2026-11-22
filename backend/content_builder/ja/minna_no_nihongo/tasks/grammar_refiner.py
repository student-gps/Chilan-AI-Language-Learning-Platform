from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

try:
    from content_builder.core.llm_providers import BaseLLMProvider
    from content_builder.ja.minna_no_nihongo.book_profiles import lesson_profile as resolve_lesson_profile
except ImportError:
    from content_builder.core.llm_providers import BaseLLMProvider
    from content_builder.ja.minna_no_nihongo.book_profiles import lesson_profile as resolve_lesson_profile


class MinnaNoNihongoGrammarRefiner:
    """Discover and repair grammar sections as a separate Stage 1 task."""

    def run(
        self,
        lesson_data: dict,
        llm_provider: BaseLLMProvider | None = None,
        lesson_pdf: Path | None = None,
        lesson_file_obj=None,
        lesson_id: int | None = None,
        support_language: str = "zh",
    ) -> dict:
        refined = deepcopy(lesson_data if isinstance(lesson_data, dict) else {})
        current_sections = self._normalize_sections(self._grammar_sections(refined))
        print(f"     📊 [MNN Task 3.0] 当前 raw grammar_sections: {len(current_sections)} 条。")

        discovered_titles = []
        can_use_pdf_context = llm_provider is not None and (lesson_pdf is not None or lesson_file_obj is not None)
        if can_use_pdf_context:
            print("     ▶️ [MNN Task 3.1] 正在发现 grammar title...")
            discovered_titles = self._discover_titles(
                llm_provider=llm_provider,
                lesson_pdf=lesson_pdf,
                lesson_file_obj=lesson_file_obj,
                lesson_id=lesson_id,
                support_language=support_language,
            )
            print(
                "     ✨ [MNN Task 3.1] grammar title discovery 完成: "
                f"{len(discovered_titles)} 条"
            )
            self._print_titles(discovered_titles)
            print("     ▶️ [MNN Task 3.2] 正在逐节修复 grammar_sections...")
            repaired_sections = self._repair_sections(
                llm_provider=llm_provider,
                lesson_pdf=lesson_pdf,
                lesson_file_obj=lesson_file_obj,
                lesson_id=lesson_id,
                support_language=support_language,
                titles=discovered_titles,
                current_sections=current_sections,
                lesson_data=refined,
            )
            if repaired_sections:
                current_sections = repaired_sections
                print(
                    "     ✨ [MNN Task 3.2] grammar section repair 完成: "
                    f"{len(current_sections)} 条"
                )
            else:
                print("     ⚠️ [MNN Task 3.2] repair 未返回有效 sections，保留 raw grammar_sections。")
        else:
            print("     ⏭️ [MNN Task 3.1/3.2] 未配置 LLM/PDF，跳过语法标题发现与修复。")

        self._set_grammar_sections(refined, current_sections)
        print(
            "     📊 [MNN Task 3.3] grammar_sections 落盘统计: "
            f"{len(current_sections)} 条"
        )
        self._print_section_summary(current_sections)
        diagnostics = refined.setdefault("pipeline_diagnostics", {})
        diagnostics["grammar_refinement"] = {
            "title_count": len(discovered_titles),
            "section_count": len(current_sections),
            "used_llm": can_use_pdf_context,
        }
        return refined

    def _print_titles(self, titles: list[dict]) -> None:
        if not titles:
            print("        - 未发现 grammar titles")
            return
        for item in titles[:12]:
            order = item.get("order", "")
            title = item.get("title", "")
            source_hint = item.get("source_hint", "")
            source_text = f" ({source_hint})" if source_hint else ""
            print(f"        - {order}. {title}{source_text}")
        if len(titles) > 12:
            print(f"        ... 还有 {len(titles) - 12} 条")

    def _print_section_summary(self, sections: list[dict]) -> None:
        if not sections:
            print("        - 无 grammar_sections")
            return
        for section in sections[:12]:
            title = section.get("title", "")
            patterns = section.get("patterns") if isinstance(section.get("patterns"), list) else []
            examples = section.get("examples") if isinstance(section.get("examples"), list) else []
            explanation = (section.get("explanation") or "").strip()
            status = "ok" if title and explanation and (patterns or examples) else "needs_check"
            print(
                f"        - {title} | patterns={len(patterns)} "
                f"examples={len(examples)} | {status}"
            )
        if len(sections) > 12:
            print(f"        ... 还有 {len(sections) - 12} 条")

    def _discover_titles(
        self,
        *,
        llm_provider: BaseLLMProvider,
        lesson_pdf: Path | None,
        lesson_file_obj=None,
        lesson_id: int | None,
        support_language: str,
    ) -> list[dict]:
        result = llm_provider.generate_structured_json(
            self._title_prompt(lesson_id=lesson_id, support_language=support_language),
            file_path=None if lesson_file_obj is not None else str(lesson_pdf),
            file_obj=lesson_file_obj,
        )
        titles = result.get("grammar_titles") if isinstance(result, dict) else []
        return self._normalize_titles(titles if isinstance(titles, list) else [])

    def _repair_sections(
        self,
        *,
        llm_provider: BaseLLMProvider,
        lesson_pdf: Path | None,
        lesson_file_obj=None,
        lesson_id: int | None,
        support_language: str,
        titles: list[dict],
        current_sections: list[dict],
        lesson_data: dict,
    ) -> list[dict]:
        result = llm_provider.generate_structured_json(
            self._section_prompt(
                lesson_id=lesson_id,
                support_language=support_language,
                titles=titles,
                current_sections=current_sections,
                lesson_data=lesson_data,
            ),
            file_path=None if lesson_file_obj is not None else str(lesson_pdf),
            file_obj=lesson_file_obj,
        )
        sections = result.get("grammar_sections") if isinstance(result, dict) else []
        return self._normalize_sections(sections if isinstance(sections, list) else [])

    def _title_prompt(self, *, lesson_id: int | None, support_language: str) -> str:
        profile = resolve_lesson_profile(int(lesson_id)) if lesson_id is not None else None
        if profile and profile.pedagogy_profile == "intermediate_read_write_speak_listen_grammar":
            return f"""
        你是一名《みんなの日本語 中級》语法目录审校员。请只根据当前单课 PDF，
        找出 文法・練習 中真正应该讲解的语法点标题；必要时参考 読む・書く /
        話す・聞く 中反复出现的表达。

        lesson_id: {lesson_id}
        source_lesson: {profile.source_lesson}
        support_language: {support_language}
        source_sections: {json.dumps(list(profile.source_sections), ensure_ascii=False)}

        要求：
        1. 只输出 JSON，不要 Markdown。
        2. 不要提取页眉、页码、练习编号、目录噪声。
        3. 标题应覆盖本课 文法・練習 的核心句型、表达和语用功能。
        4. 标题数量宁缺毋滥，通常 3-8 个。

        输出结构：
        {{
          "grammar_titles": [
            {{"order": 1, "title": "〜ていただけませんか", "source_hint": "文法・練習"}}
          ]
        }}
        """
        return f"""
        你是一名《みんなの日本語》语法目录审校员。请只根据当前单课 PDF，
        找出本课真正应该讲解的语法点标题。

        lesson_id: {lesson_id}
        support_language: {support_language}

        要求：
        1. 只输出 JSON，不要 Markdown。
        2. 不要提取页眉、页码、练习编号、目录噪声。
        3. 标题应覆盖 文型 / 例文 / 会話 中实际出现的句型、助词、疑问词、否定/肯定形式等。
        4. 标题数量宁缺毋滥，通常 3-8 个。

        输出结构：
        {{
          "grammar_titles": [
            {{"order": 1, "title": "N1 は N2 です", "source_hint": "文型"}}
          ]
        }}
        """

    def _section_prompt(
        self,
        *,
        lesson_id: int | None,
        support_language: str,
        titles: list[dict],
        current_sections: list[dict],
        lesson_data: dict,
    ) -> str:
        compact_content = self._compact_lesson_content(lesson_data)
        profile = resolve_lesson_profile(int(lesson_id)) if lesson_id is not None else None
        if profile and profile.pedagogy_profile == "intermediate_read_write_speak_listen_grammar":
            return f"""
        你是一名日语语法讲解编辑。请根据《みんなの日本語 中級》单课 PDF、
        已发现的语法标题、以及当前抽取结果，修复/重写本课 grammar_sections。

        lesson_id: {lesson_id}
        source_lesson: {profile.source_lesson}
        support_language: {support_language}
        source_sections: {json.dumps(list(profile.source_sections), ensure_ascii=False)}

        已发现标题：
        {json.dumps(titles, ensure_ascii=False, indent=2)}

        当前 grammar_sections：
        {json.dumps(current_sections, ensure_ascii=False, indent=2)}

        本课核心文本摘要：
        {json.dumps(compact_content, ensure_ascii=False, indent=2)}

        要求：
        1. 只输出 JSON，不要 Markdown。
        2. 每个 section 必须有 title、explanation、patterns、examples。
        3. explanation 用中文，面向中文母语中级学习者，简洁但要准确。
        4. patterns 放抽象句型或表达功能；examples 优先放本课出现过或非常贴近本课的日语例句。
        5. 不要编造本课没有出现的高级语法。
        6. 可以在 usage_notes 中说明该表达适用的读写/听说场景。

        输出结构：
        {{
          "grammar_sections": [
            {{
              "title": "〜ていただけませんか",
              "explanation": "用于礼貌请求对方为自己做某事。",
              "patterns": [
                {{"text": "Vて いただけませんか", "translation": "能请您……吗？"}}
              ],
              "examples": [
                {{"text": "この資料を見ていただけませんか。", "reading": "このしりょうをみていただけませんか。", "translation": "能请您看一下这份资料吗？"}}
              ],
              "usage_notes": ["适合在职场或正式场合中提出请求。"]
            }}
          ]
        }}
        """
        return f"""
        你是一名日语语法讲解编辑。请根据单课 PDF、已发现的语法标题、
        以及当前抽取结果，修复/重写本课 grammar_sections。

        lesson_id: {lesson_id}
        support_language: {support_language}

        已发现标题：
        {json.dumps(titles, ensure_ascii=False, indent=2)}

        当前 grammar_sections：
        {json.dumps(current_sections, ensure_ascii=False, indent=2)}

        本课核心文本摘要：
        {json.dumps(compact_content, ensure_ascii=False, indent=2)}

        要求：
        1. 只输出 JSON，不要 Markdown。
        2. 每个 section 必须有 title、explanation、patterns、examples。
        3. explanation 用中文，面向中文母语初学者，简洁但要准确。
        4. patterns 放抽象句型；examples 放本课出现过或非常贴近本课的日语例句。
        5. 不要编造本课没有出现的高级语法。

        输出结构：
        {{
          "grammar_sections": [
            {{
              "title": "N1 は N2 です",
              "explanation": "表示判断或说明身份、职业、属性。",
              "patterns": [
                {{"text": "N1 は N2 です", "translation": "N1 是 N2。"}}
              ],
              "examples": [
                {{"text": "わたしは会社員です。", "reading": "わたしはかいしゃいんです。", "translation": "我是公司职员。"}}
              ],
              "usage_notes": ["句末用です表示礼貌。"]
            }}
          ]
        }}
        """

    def _compact_lesson_content(self, lesson_data: dict) -> dict:
        content = lesson_data.get("course_content") if isinstance(lesson_data.get("course_content"), dict) else {}
        dialogue = content.get("dialogue") if isinstance(content.get("dialogue"), dict) else {}
        return {
            "sentence_patterns": self._compact_lines(content.get("sentence_patterns") or []),
            "example_sentences": self._compact_lines(content.get("example_sentences") or []),
            "dialogue_lines": self._compact_lines(dialogue.get("lines") or []),
        }

    def _compact_lines(self, lines: list[dict]) -> list[dict]:
        compact = []
        for index, line in enumerate(lines or [], start=1):
            if not isinstance(line, dict):
                continue
            text = (line.get("text") or line.get("ja") or "").strip()
            if not text:
                continue
            compact.append({
                "ref": line.get("line_ref") or line.get("pattern_id") or index,
                "text": text,
                "reading": (line.get("reading") or "").strip(),
                "translation": (line.get("translation") or "").strip(),
            })
        return compact

    def _normalize_titles(self, titles: list[dict]) -> list[dict]:
        normalized = []
        seen = set()
        for index, item in enumerate(titles or [], start=1):
            if isinstance(item, str):
                title = item.strip()
                source_hint = ""
                order = index
            elif isinstance(item, dict):
                title = (item.get("title") or item.get("grammar_title") or "").strip()
                source_hint = (item.get("source_hint") or item.get("source") or "").strip()
                order = item.get("order") or index
            else:
                continue
            if not title:
                continue
            key = title.casefold()
            if key in seen:
                continue
            seen.add(key)
            normalized.append({"order": int(order), "title": title, "source_hint": source_hint})
        return normalized

    def _normalize_sections(self, sections: list[dict]) -> list[dict]:
        normalized = []
        seen = set()
        for index, item in enumerate(sections or [], start=1):
            if not isinstance(item, dict):
                continue
            title = (item.get("title") or item.get("grammar_title") or "").strip()
            if not title:
                continue
            key = title.casefold()
            if key in seen:
                continue
            seen.add(key)
            normalized.append({
                "section_id": item.get("section_id") or index,
                "title": title,
                "explanation": (item.get("explanation") or item.get("description") or "").strip(),
                "patterns": item.get("patterns") if isinstance(item.get("patterns"), list) else [],
                "examples": item.get("examples") if isinstance(item.get("examples"), list) else [],
                "usage_notes": item.get("usage_notes") if isinstance(item.get("usage_notes"), list) else [],
                "common_mistakes": item.get("common_mistakes") if isinstance(item.get("common_mistakes"), list) else [],
            })
        return normalized

    def _grammar_sections(self, lesson_data: dict) -> list[dict]:
        content = lesson_data.get("course_content") if isinstance(lesson_data.get("course_content"), dict) else {}
        sections = content.get("grammar_sections")
        return sections if isinstance(sections, list) else []

    def _set_grammar_sections(self, lesson_data: dict, sections: list[dict]) -> None:
        lesson_data.setdefault("course_content", {})["grammar_sections"] = sections
