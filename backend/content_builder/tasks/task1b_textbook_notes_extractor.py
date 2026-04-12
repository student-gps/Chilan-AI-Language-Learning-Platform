from llm_providers import BaseLLMProvider


class Task1BTextbookNotesExtractor:
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider

    # ── Round 0: 发现所有 section 标题 ──────────────────────────────────────
    def _build_discovery_prompt(self, lesson_id: int, course_id: int) -> str:
        return f"""
        你是一名教材结构分析专家。请解析提供的教材 PDF，只提取教材中的结构标题列表，不要提取任何内容正文。
        只输出合法 JSON，不要包含 Markdown。

        【任务】提取两类标题：
        1. language_note_titles：教材中 Language Notes 板块的每条注释标题（如 "你好"、"请问"、"你 vs 您"）
        2. grammar_section_titles：教材中 Grammar 板块每个语法点的标题（如 "The verb 姓 (xìng)"、"Numbers up to 100"）

        【不要提取】课文对话正文、生词表、练习题。

        【输出结构】
        {{
          "lesson_id": {lesson_id},
          "language_note_titles": ["标题1", "标题2"],
          "grammar_section_titles": ["Numbers up to 100", "Dates", "Time"]
        }}
        """

    # ── Round 1: 提取所有 language notes 完整内容（通常较短，一次搞定）──────
    def _build_language_notes_prompt(self, lesson_id: int, course_id: int, titles: list) -> str:
        titles_str = "\n".join(f"- {t}" for t in titles)
        return f"""
        你是一名教材讲解素材提取专家。请从教材 PDF 中提取以下 Language Notes 条目的完整内容。
        只输出合法 JSON，不要包含 Markdown。

        需要提取的条目（共 {len(titles)} 条）：
        {titles_str}

        【提取要求】
        - 只提取 Language Notes 板块的内容，不要提取课文对话或练习题。
        - 每条尽量包含：note_id、label、focus_text、focus_pinyin、explanation_en、source_section。
        - 如果某字段无法可靠提取，返回空字符串，不要编造。

        【输出结构】
        {{
          "language_notes": [
            {{
              "note_id": "LN-1",
              "label": "a",
              "focus_text": "你好",
              "focus_pinyin": "Nǐ hǎo",
              "explanation_en": "This common greeting ...",
              "source_section": "Language Notes"
            }}
          ]
        }}
        """

    # ── Round 2+: 逐条提取每个 grammar section 完整内容 ─────────────────────
    def _build_grammar_section_prompt(self, title: str, grammar_id: str) -> str:
        return f"""
        你是一名教材语法内容提取专家。请从教材 PDF 中提取标题为【{title}】的语法点的完整内容。
        只输出合法 JSON，不要包含 Markdown。

        【提取要求】
        - 只提取这一个语法点，不要混入其他语法点的内容。
        - 完整提取：解释说明、所有句型结构、所有例句、使用说明、常见错误。
        - 对于数字/日期/时间类语法点，必须完整列出所有例子（如数字 1-100、时间表达格式等）。
        - 如果某字段无法可靠提取，返回空字符串或空数组，不要编造。

        【输出结构】
        {{
          "grammar_section": {{
            "grammar_id": "{grammar_id}",
            "title": "{title}",
            "explanation_en": "完整的语法说明...",
            "patterns": [
              {{
                "pattern": "句型结构",
                "pattern_pinyin": "拼音",
                "meaning_en": "含义"
              }}
            ],
            "examples": [
              {{
                "hanzi": "例句汉字",
                "pinyin": "拼音",
                "english": "英文"
              }}
            ],
            "usage_notes": ["使用说明1", "使用说明2"],
            "common_errors": [
              {{
                "wrong": "错误写法",
                "correct": "正确写法",
                "explanation_en": "说明"
              }}
            ]
          }}
        }}
        """

    # ── 主流程 ───────────────────────────────────────────────────────────────
    def run(self, lesson_id: int, course_id: int, file_path: str = None, file_obj=None):
        print("  ▶️ [Task 1B] 正在提取教材讲解素材 (Language Notes / Grammar)...")

        # 第一轮：发现所有标题
        discovery = self.llm.generate_structured_json(
            self._build_discovery_prompt(lesson_id, course_id),
            file_path=file_path,
            file_obj=file_obj,
        )
        ln_titles = discovery.get("language_note_titles", []) if isinstance(discovery, dict) else []
        gs_titles = discovery.get("grammar_section_titles", []) if isinstance(discovery, dict) else []
        print(f"     🔍 发现 language notes {len(ln_titles)} 条，grammar sections {len(gs_titles)} 条")

        # 第二轮：一次提取所有 language notes（内容通常不长）
        language_notes = []
        if ln_titles:
            ln_result = self.llm.generate_structured_json(
                self._build_language_notes_prompt(lesson_id, course_id, ln_titles),
                file_path=file_path,
                file_obj=file_obj,
            )
            language_notes = ln_result.get("language_notes", []) if isinstance(ln_result, dict) else []

        # 第三轮起：逐条提取每个 grammar section
        grammar_sections = []
        for idx, title in enumerate(gs_titles, start=1):
            grammar_id = f"G-{idx}"
            print(f"     📖 正在提取语法点 {idx}/{len(gs_titles)}: {title}")
            gs_result = self.llm.generate_structured_json(
                self._build_grammar_section_prompt(title, grammar_id),
                file_path=file_path,
                file_obj=file_obj,
            )
            section = gs_result.get("grammar_section") if isinstance(gs_result, dict) else None
            if section:
                grammar_sections.append(section)
            else:
                # 提取失败时保留骨架，不丢失标题
                grammar_sections.append({
                    "grammar_id": grammar_id,
                    "title": title,
                    "explanation_en": "",
                    "patterns": [],
                    "examples": [],
                    "usage_notes": [],
                    "common_errors": [],
                })

        print(f"  ✨ Task 1B 提取完成，language notes {len(language_notes)} 条，grammar sections {len(grammar_sections)} 条。")

        return {
            "teaching_materials": {
                "lesson_id": lesson_id,
                "course_id": course_id,
                "lesson_title": discovery.get("lesson_title", "") if isinstance(discovery, dict) else "",
                "language_notes": language_notes,
                "grammar_sections": grammar_sections,
            }
        }
