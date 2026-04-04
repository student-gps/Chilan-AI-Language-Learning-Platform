from llm_providers import BaseLLMProvider


class Task1BTextbookNotesExtractor:
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider

    def _build_prompt(self, lesson_id: int, course_id: int) -> str:
        return f"""
        你是一名教材讲解素材提取专家。请解析提供的教材 PDF，提取【用于老师讲课】的教材说明内容。
        只输出合法 JSON，不要包含 Markdown。

        【重要边界】
        1. 这次任务不是提取课文正文，对话正文由别的任务负责。
        2. 这次任务也不是提取练习区供学生做题，practice / exercise 内容不要输出。
        3. 只提取适合教学讲解视频使用的教材说明内容。

        【需要提取的板块】
        1. language_notes
           - 提取教材中对词语、礼貌用法、文化差异、称呼方式等的英文讲解
           - 例如：你好、请问、你 vs 您、小姐 等
        2. grammar_sections
           - 提取教材中的语法讲解标题、英文解释、例句、使用说明、常见错误
           - 例如：The verb 姓 (xìng)、Questions ending with 呢 (ne)、The verb 叫 (jiào)
        3. lesson_title
           - 提取教材中的本课英文标题；如果无法稳定提取，则返回空字符串

        【不要提取的内容】
        - 课文 dialogue 正文
        - 纯生词表 vocabulary 列表
        - 课后 exercises / language practice / role play / fill in the blank

        【字段要求】
        1. language_notes 中每项都尽量包含：
           - note_id
           - label
           - focus_text
           - focus_pinyin
           - explanation_en
           - source_section
        2. grammar_sections 中每项都尽量包含：
           - grammar_id
           - title
           - explanation_en
           - patterns
           - examples
           - usage_notes
           - common_errors
        3. 如果某些字段无法可靠提取，返回空字符串、空数组，不要编造。

        【输出结构】
        {{
          "teaching_materials": {{
            "lesson_id": {lesson_id},
            "course_id": {course_id},
            "lesson_title": "",
            "language_notes": [
              {{
                "note_id": "LN-1",
                "label": "a",
                "focus_text": "你好",
                "focus_pinyin": "Nǐ hǎo",
                "explanation_en": "This common greeting ...",
                "source_section": "Language Notes"
              }}
            ],
            "grammar_sections": [
              {{
                "grammar_id": "G-1",
                "title": "The verb 姓 (xìng)",
                "explanation_en": "姓 is both a noun and a verb ...",
                "patterns": [
                  {{
                    "pattern": "你姓什么？ / 我姓李。",
                    "pattern_pinyin": "Nǐ xìng shénme? / Wǒ xìng Lǐ.",
                    "meaning_en": "What is your family name? / My family name is Li."
                  }}
                ],
                "examples": [
                  {{
                    "hanzi": "你贵姓？",
                    "pinyin": "Nǐ guì xìng?",
                    "english": "What is your family name?"
                  }}
                ],
                "usage_notes": [
                  "The polite way to ask and give a family name is as follows."
                ],
                "common_errors": [
                  {{
                    "wrong": "你贵姓什么？",
                    "correct": "你贵姓？",
                    "explanation_en": "Do not add 什么 after 贵姓."
                  }}
                ]
              }}
            ]
          }}
        }}
        """

    def run(self, lesson_id: int, course_id: int, file_path: str = None, file_obj=None):
        print("  ▶️ [Task 1B] 正在提取教材讲解素材 (Language Notes / Grammar)...")

        result = self.llm.generate_structured_json(
            self._build_prompt(lesson_id, course_id),
            file_path=file_path,
            file_obj=file_obj
        )

        teaching_materials = result.get("teaching_materials", {}) if isinstance(result, dict) else {}
        if isinstance(teaching_materials, dict):
            notes_count = len(teaching_materials.get("language_notes", []))
            grammar_count = len(teaching_materials.get("grammar_sections", []))
            print(f"  ✨ Task 1B 提取完成，language notes {notes_count} 条，grammar sections {grammar_count} 条。")
            return {
                "teaching_materials": {
                    "lesson_id": lesson_id,
                    "course_id": course_id,
                    "lesson_title": teaching_materials.get("lesson_title", ""),
                    "language_notes": teaching_materials.get("language_notes", []),
                    "grammar_sections": teaching_materials.get("grammar_sections", [])
                }
            }

        return {
            "teaching_materials": {
                "lesson_id": lesson_id,
                "course_id": course_id,
                "lesson_title": "",
                "language_notes": [],
                "grammar_sections": []
            }
        }
