from __future__ import annotations

import json
import re
from pathlib import Path

try:
    from content_builder.core.llm_providers import BaseLLMProvider
    from content_builder.ja.minna_no_nihongo.book_profiles import book1, lesson_profile as resolve_lesson_profile
    from content_builder.ja.minna_no_nihongo.tasks.lesson_normalizer import MinnaNoNihongoLessonNormalizer
except ImportError:
    from content_builder.core.llm_providers import BaseLLMProvider
    from content_builder.ja.minna_no_nihongo.book_profiles import book1, lesson_profile as resolve_lesson_profile
    from content_builder.ja.minna_no_nihongo.tasks.lesson_normalizer import MinnaNoNihongoLessonNormalizer


class MinnaNoNihongoExtractor:
    """PDF -> raw lesson structure.

    Normalization, reading repair, teaching flow, practice items, and render
    planning live in separate Stage 1 tasks orchestrated by the agent.
    """

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider

    def _is_intermediate_profile(self, lesson_profile: book1.LessonProfile) -> bool:
        return lesson_profile.pedagogy_profile == "intermediate_read_write_speak_listen_grammar"

    def _context(
        self,
        lesson_profile: book1.LessonProfile,
        support_language: str,
    ) -> dict:
        return {
            "book": lesson_profile.book,
            "lesson_id": lesson_profile.lesson_id,
            "lesson_slug": lesson_profile.lesson_slug,
            "source_lesson": lesson_profile.source_lesson,
            "textbook": lesson_profile.textbook_name_ja,
            "pedagogy_profile": lesson_profile.pedagogy_profile,
            "source_sections": list(lesson_profile.source_sections),
            "target_language": "ja",
            "support_language": support_language,
        }

    def _base_payload(
        self,
        lesson_profile: book1.LessonProfile,
        support_language: str,
        course_id: int | str,
    ) -> dict:
        return {
            "schema_version": "1.0",
            "pipeline_id": "minna_no_nihongo",
            "target_language": "ja",
            "support_language": support_language,
            "lesson_metadata": {
                "course_id": course_id,
                "course_slug": lesson_profile.course_slug,
                "lesson_id": lesson_profile.lesson_id,
                "lesson_slug": lesson_profile.lesson_slug,
                "title": f"第{lesson_profile.source_lesson}課",
                "title_localized": f"第{lesson_profile.source_lesson}课",
                "topic_title": "",
                "topic_title_localized": "",
                "section_titles": [],
                "content_type": lesson_profile.content_type,
                "source": {
                    "textbook": lesson_profile.textbook_name,
                    "textbook_ja": lesson_profile.textbook_name_ja,
                    "textbook_zh": lesson_profile.textbook_name_zh,
                    "book": lesson_profile.book,
                    "source_lesson": lesson_profile.source_lesson,
                    "source_sections": list(lesson_profile.source_sections),
                },
            },
            "course_content": {
                "sentence_patterns": [],
                "example_sentences": [],
                "dialogue": {"title": "", "title_localized": "", "lines": []},
                "vocabulary": [],
                "lexical_notes": [],
                "display_only_vocabulary": [],
                "grammar_sections": [],
                "practice_source": [],
            },
            "teaching_materials": {
                "lesson_flow": [],
                "pronunciation_notes": [],
                "usage_notes": [],
            },
            "practice_items": [],
        }

    def _build_core_text_prompt(
        self,
        lesson_profile: book1.LessonProfile,
        support_language: str,
        course_id: int | str,
    ) -> str:
        context = self._context(lesson_profile, support_language)
        if self._is_intermediate_profile(lesson_profile):
            return f"""
        你是一名日语教材解析工程师。请解析提供的《みんなの日本語 中級 /
        大家的日语 中级》单课 PDF。本任务只提取本课主线文本，并把新版
        教材结构映射到现有 App JSON 字段。只输出合法 JSON，不要包含 Markdown。

        输入上下文：
        {json.dumps(context, ensure_ascii=False)}

        新版教材结构：
        - 読む・書く：读解文章、写作主题、核心表达、读写任务。
        - 話す・聞く：会话、听力脚本、口语任务、可跟读表达。
        - 文法・練習：语法说明和练习素材。

        字段映射：
        1. lesson_metadata.title / title_localized 保持课程编号，例如 第51課 / 第51课，不要改成中级第1课。
        2. lesson_metadata.topic_title 放本课课题名或主标题，例如「お願いがあるんですが」；
           topic_title_localized 放自然中文标题。没有明确课题名时留空。
        3. section_titles 记录 読む・書く / 話す・聞く / 文法・練習 的栏目标题或任务标题。
        4. sentence_patterns 放本课最核心的表达/句型/任务句，不要强行寻找旧版「文型」栏。
        5. example_sentences 放 読む・書く 和 文法・練習 中适合讲解的短句、模型句、写作例句。
        6. dialogue.lines 放 話す・聞く 中的对话、听力脚本、口语交换；没有明确说话人时用 A/B 或「ナレーション」。
        7. text 保留日语原文；translation 用中文，并与当前短句/台词一一对应。
        8. reading 必须尽量提供，使用适合学习者跟读的假名读音；不要为了补全读音而改写 text。
        9. tokens 可以尽量提供但不是本任务硬指标，后续 Task 4/5 会补齐并审校。
        10. 严禁提取目录、页眉页脚、页码、版权页噪声。

        输出结构：
        {{
          "lesson_metadata": {{
            "course_id": {json.dumps(course_id, ensure_ascii=False)},
            "lesson_id": {lesson_profile.lesson_id},
            "title": "第{lesson_profile.source_lesson}課",
            "title_localized": "第{lesson_profile.source_lesson}课",
            "topic_title": "",
            "topic_title_localized": "",
            "section_titles": [
              {{"section": "読む・書く", "title": "", "title_localized": ""}},
              {{"section": "話す・聞く", "title": "", "title_localized": ""}},
              {{"section": "文法・練習", "title": "", "title_localized": ""}}
            ],
            "content_type": "integrated_skills_intermediate"
          }},
          "course_content": {{
            "sentence_patterns": [
              {{"text": "", "reading": "", "romaji": "", "translation": "", "tokens": [], "grammar_focus": [], "source_section": "読む・書く"}}
            ],
            "example_sentences": [
              {{"line_ref": 1, "text": "", "reading": "", "romaji": "", "translation": "", "tokens": [], "source_section": "読む・書く"}}
            ],
            "dialogue": {{"title": "", "title_localized": "", "lines": [
              {{"speaker": "", "text": "", "reading": "", "romaji": "", "translation": "", "tokens": [], "source_section": "話す・聞く"}}
            ]}}
          }}
        }}
        """
        return f"""
        你是一名日语教材解析工程师。请解析提供的《みんなの日本語 / 大家的日本语》
        单课 PDF。本任务只提取本课主线文本：文型 / 例文 / 会話。
        只输出合法 JSON，不要包含 Markdown。

        输入上下文：
        {json.dumps(context, ensure_ascii=False)}

        要求：
        1. 只提取 文型 / 例文 / 会話，不要提取词汇表、语法讲解、练习题。
        2. 如果单课 PDF 有明确课题名，把它放入 lesson_metadata.topic_title；
           普通初级课通常没有课题名，可以留空。lesson_metadata.title 仍保持 第N課。
        3. 例文必须拆成细粒度句子卡片：每个 example_sentences item 只放一个独立句子或一个短答句。
           不要把“问题 + 回答”合并成一条，也不要把多个问答连成一条。
           遇到「……」「はい、」「いいえ、」连接的问答，按教材出现顺序拆成多条。
           例如：
           - 「グプタさんは会社員ですか。……はい、会社員です。」必须拆成
             1) グプタさんは会社員ですか。
             2) はい、会社員です。
           - 「カリナさんも会社員ですか。……いいえ。[カリナさんは]学生です。」必须拆成
             1) カリナさんも会社員ですか。
             2) いいえ。
             3) [カリナさんは]学生です。
           拆分后用 line_ref 按顺序编号。
        4. text 保留日语原文；translation 用中文，并且 translation 要对应当前这一条短句，不要写整组问答的总翻译。
        5. reading 必须尽量提供，使用适合初学者跟读的整句假名读音；有汉字的词要给假名，
           例如 会社員 -> かいしゃいん。不要为了补全读音而改写 text 原文。
        6. romaji 可以提供；tokens 可以尽量提供但不是本任务硬指标，后续 Task 4/5 会补齐并审校。
        7. 会話的 speaker 直接使用教材中的说话人；不确定也要给最可能的人名。
        8. 严禁提取目录、页眉页脚、页码、版权页噪声。

        输出结构：
        {{
          "lesson_metadata": {{
            "course_id": {json.dumps(course_id, ensure_ascii=False)},
            "lesson_id": {lesson_profile.lesson_id},
            "title": "第{lesson_profile.lesson_id}課",
            "title_localized": "第{lesson_profile.lesson_id}课",
            "topic_title": "",
            "topic_title_localized": "",
            "section_titles": [],
            "content_type": "sentence_pattern_dialogue"
          }},
          "course_content": {{
            "sentence_patterns": [
              {{"text": "", "reading": "", "romaji": "", "translation": "", "tokens": [], "grammar_focus": []}}
            ],
            "example_sentences": [
              {{"line_ref": 1, "text": "", "reading": "", "romaji": "", "translation": "", "tokens": []}}
            ],
            "dialogue": {{"title": "", "title_localized": "", "lines": [
              {{"speaker": "", "text": "", "reading": "", "romaji": "", "translation": "", "tokens": []}}
            ]}}
          }}
        }}
        """

    def _build_vocabulary_prompt(
        self,
        lesson_profile: book1.LessonProfile,
        support_language: str,
    ) -> str:
        context = self._context(lesson_profile, support_language)
        if self._is_intermediate_profile(lesson_profile):
            return f"""
        你是一名日语教材词汇提取员。请解析当前《みんなの日本語 中級》单课 PDF，
        从 読む・書く / 話す・聞く / 文法・練習 中提取理解课文必需的新词候选。
        只输出合法 JSON，不要包含 Markdown。

        输入上下文：
        {json.dumps(context, ensure_ascii=False)}

        要求：
        1. 中级课没有独立词汇表；vocabulary 不要当作旧版「語彙」栏来抽。
        2. vocabulary 只放理解本课主线必需、且很可能是新出现的关键词。
           数量不设硬上限，但要克制；不要收录初级阶段常见词、功能词、已学基础动词、普通助词、
           寒暄语或只是顺手出现的词。
        3. 复现词、只为分词/读音服务的词、文章理解辅助词，不要放入 vocabulary；可以放入 lexical_notes。
        4. lesson_section 只允许 core 或 supplementary：
           - core：理解 読む・書く / 話す・聞く 主线内容所必需。
           - supplementary：主要服务 文法・練習、写作扩展或口语扩展。
        5. display_only_vocabulary 放只展示不复习的专名/机构名/作品名/临时地名等。
        6. 不要把 display_only_vocabulary 中的词重复放入 vocabulary。
        7. part_of_speech 必须使用中文全称，不要使用缩写或英文。
        8. example_sentence.source_section 标注来源：読む・書く、話す・聞く 或 文法・練習。
        9. lexical_notes 用于保存不出题的理解辅助词或复现词，数量也要克制。

        输出结构：
        {{
          "course_content": {{
            "vocabulary": [
              {{
                "term": "",
                "reading": "",
                "romaji": "",
                "part_of_speech": "",
                "translation": "",
                "accent": "",
                "lesson_section": "core",
                "source_section": "読む・書く",
                "example_sentence": {{"text": "", "reading": "", "romaji": "", "translation": "", "source_section": "読む・書く", "source_ref": 1}}
              }}
            ],
            "lexical_notes": [
              {{
                "term": "",
                "reading": "",
                "romaji": "",
                "part_of_speech": "",
                "translation": "",
                "source_section": "読む・書く",
                "learning_role": "context_only",
                "quiz_eligible": false,
                "reason": "reading_support"
              }}
            ],
            "display_only_vocabulary": [
              {{
                "term": "",
                "reading": "",
                "romaji": "",
                "category": "proper_noun",
                "translation": "",
                "reason": "display_only",
                "lesson_section": "reference",
                "source_section": "読む・書く"
              }}
            ]
          }}
        }}
        """
        return f"""
        你是一名日语教材词汇提取员。请解析当前单课 PDF，只提取新出語彙、
        練習A/B/C/問題 中用于替换操练或扩展表达的词，以及只展示不复习的专名。
        只输出合法 JSON，不要包含 Markdown。

        输入上下文：
        {json.dumps(context, ensure_ascii=False)}

        要求：
        1. vocabulary 放需要学习和复习的词；核心词和补充词同等地位。
        2. lesson_section 只允许 core 或 supplementary：
           - core：出现在 文型 / 例文 / 会話 中，理解本课主线需要。
           - supplementary：主要出现在 練習A/B/C / 問題 中，用来做替换操练或扩展表达。
        3. display_only_vocabulary 放只展示不复习的专名/临时名词：
           人名、公司名、大学名、医院名、虚构机构名、品牌名、临时地名等。
        4. 不要把 display_only_vocabulary 中的词重复放入 vocabulary。
        5. 国家名、语言名、国籍词如果是本课要掌握的普通词，可以放入 vocabulary。
        6. 不要提取语法讲解、课文句子、题目说明。
        7. part_of_speech 必须使用中文全称，不要使用缩写或英文。例如：
           代词、名词、动词、い形容词、な形容词、副词、助词、接尾词、感叹词、
           惯用表达、寒暄语、疑问词、助数词、专有名词。

        输出结构：
        {{
          "course_content": {{
            "vocabulary": [
              {{
                "term": "",
                "reading": "",
                "romaji": "",
                "part_of_speech": "",
                "translation": "",
                "accent": "",
                "lesson_section": "core",
                "example_sentence": {{"text": "", "reading": "", "romaji": "", "translation": "", "source_section": "", "source_ref": 1}}
              }}
            ],
            "display_only_vocabulary": [
              {{
                "term": "",
                "reading": "",
                "romaji": "",
                "category": "person_name",
                "translation": "",
                "reason": "display_only",
                "lesson_section": "reference"
              }}
            ]
          }}
        }}
        """

    def _build_grammar_seed_prompt(
        self,
        lesson_profile: book1.LessonProfile,
        support_language: str,
    ) -> str:
        context = self._context(lesson_profile, support_language)
        if self._is_intermediate_profile(lesson_profile):
            return f"""
        你是一名日语语法提取员。请解析当前《みんなの日本語 中級》单课 PDF，
        只提取 文法・練習 中本课实际讲解的 grammar_sections；必要时引用
        読む・書く / 話す・聞く 中出现的例句。只输出合法 JSON，不要包含 Markdown。

        输入上下文：
        {json.dumps(context, ensure_ascii=False)}

        要求：
        1. 只提取本课实际出现的语法点，不要编造高级语法。
        2. 每个 section 尽量包含 title、explanation、patterns、examples。
        3. explanation 用中文，面向中文母语学习者，简洁准确。
        4. examples 优先使用本课读解、听说或语法练习中出现的句子。
        5. source_section 可以标注为 文法・練習。

        输出结构：
        {{
          "course_content": {{
            "grammar_sections": [
              {{
                "title": "",
                "explanation": "",
                "patterns": [{{"text": "", "translation": ""}}],
                "examples": [{{"text": "", "reading": "", "translation": "", "source_section": "文法・練習"}}],
                "usage_notes": []
              }}
            ]
          }}
        }}
        """
        return f"""
        你是一名日语教材语法提取员。请解析当前单课 PDF，只提取本课语法讲解的
        粗粒度 grammar_sections，后续 Task 3 会再做 title discovery 和逐节修复。
        只输出合法 JSON，不要包含 Markdown。

        输入上下文：
        {json.dumps(context, ensure_ascii=False)}

        要求：
        1. 只提取本课实际出现的语法点，不要编造高级语法。
        2. 每个 section 尽量包含 title、explanation、patterns、examples。
        3. explanation 用中文，简洁准确。
        4. 如果 PDF 里的语法解释很长，只提炼重点。

        输出结构：
        {{
          "course_content": {{
            "grammar_sections": [
              {{
                "title": "",
                "explanation": "",
                "patterns": [{{"text": "", "translation": ""}}],
                "examples": [{{"text": "", "reading": "", "translation": ""}}],
                "usage_notes": []
              }}
            ]
          }}
        }}
        """

    def _build_practice_source_prompt(
        self,
        lesson_profile: book1.LessonProfile,
        support_language: str,
    ) -> str:
        context = self._context(lesson_profile, support_language)
        if self._is_intermediate_profile(lesson_profile):
            return f"""
        你是一名日语教材练习素材整理员。请解析当前《みんなの日本語 中級》单课 PDF，
        从 読む・書く / 話す・聞く / 文法・練習 中提取有价值的练习素材。
        完整题库会由后续 Practice Generator 生成，本任务不要生成大量题目。
        只输出合法 JSON，不要包含 Markdown。

        输入上下文：
        {json.dumps(context, ensure_ascii=False)}

        要求：
        1. practice_source 保存教材中的读写任务、口语任务、听力任务、语法练习模式、替换词和示例句。
        2. section 使用原教材栏目名：読む・書く、話す・聞く、文法・練習，必要时加小节标题。
        3. practice_items 只允许少量明确、结构简单、可直接答题的教材题；可以为空。
        4. 不要重复输出词汇表或课文全文。
        5. 题目可以覆盖读解理解、听说复述、语法转换和中译日，但必须保留标准答案。

        输出结构：
        {{
          "course_content": {{
            "practice_source": [
              {{
                "section": "文法・練習",
                "instruction": "",
                "pattern": "",
                "examples": [],
                "substitution_words": [],
                "source_section": "文法・練習"
              }}
            ]
          }},
          "practice_items": [
            {{
              "question_type": "CN_TO_JA",
              "prompt": "",
              "standard_answers": [],
              "context": {{}},
              "metadata": {{"source_section": "文法・練習"}}
            }}
          ]
        }}
        """
        return f"""
        你是一名日语教材练习素材整理员。请解析当前单课 PDF，只提取 練習A/B/C、
        問題、替换操练表格中有价值的原始素材。完整题库会由后续 Practice Generator
        生成，本任务不要生成大量题目。只输出合法 JSON，不要包含 Markdown。

        输入上下文：
        {json.dumps(context, ensure_ascii=False)}

        要求：
        1. practice_source 保存教材中的练习模式、替换词、示例句、音听素材提示。
        2. practice_items 只允许少量明确、结构简单的教材题；可以为空。
        3. 第 1-13 课不要生成用户可见的 CONJUGATION 题。
        4. 不要重复输出词汇表或课文全文。

        输出结构：
        {{
          "course_content": {{
            "practice_source": [
              {{
                "section": "練習A",
                "instruction": "",
                "pattern": "",
                "examples": [],
                "substitution_words": []
              }}
            ]
          }},
          "practice_items": [
            {{
              "question_type": "CN_TO_JA",
              "prompt": "",
              "standard_answers": [],
              "context": {{}},
              "metadata": {{}}
            }}
          ]
        }}
        """

    def run(
        self,
        lesson_pdf: Path,
        source_pdf: Path,
        lesson_id: int,
        support_language: str = "zh",
        course_id: int | str = book1.COURSE_ID,
        file_obj=None,
    ) -> dict:
        profile = resolve_lesson_profile(lesson_id)
        payload = self._base_payload(profile, support_language, course_id)

        print("     ▶️ [MNN Task 1.1] 提取 文型 / 例文 / 会話。")
        core_result = self._generate_json(
            self._build_core_text_prompt(profile, support_language, course_id),
            lesson_pdf=lesson_pdf,
            file_obj=file_obj,
        )
        self._merge_core_text(payload, core_result)
        self._print_counts("Task 1.1", payload)

        print("     ▶️ [MNN Task 1.2] 提取 vocabulary / display_only_vocabulary。")
        vocabulary_result = self._generate_json(
            self._build_vocabulary_prompt(profile, support_language),
            lesson_pdf=lesson_pdf,
            file_obj=file_obj,
        )
        self._merge_vocabulary(payload, vocabulary_result)
        self._print_counts("Task 1.2", payload)

        print("     ▶️ [MNN Task 1.3] 提取 grammar_sections 种子。")
        grammar_result = self._generate_json(
            self._build_grammar_seed_prompt(profile, support_language),
            lesson_pdf=lesson_pdf,
            file_obj=file_obj,
        )
        self._merge_grammar(payload, grammar_result)
        self._print_counts("Task 1.3", payload)

        print("     ▶️ [MNN Task 1.4] 提取 practice_source / 少量教材练习。")
        practice_result = self._generate_json(
            self._build_practice_source_prompt(profile, support_language),
            lesson_pdf=lesson_pdf,
            file_obj=file_obj,
        )
        self._merge_practice(payload, practice_result)
        self._print_counts("Task 1.4", payload)

        payload.setdefault("pipeline_diagnostics", {})["task1_extraction"] = {
            "split_tasks": ["core_text", "vocabulary", "grammar_seed", "practice_source"],
            "used_shared_pdf": file_obj is not None,
        }
        return payload

    def _generate_json(self, prompt: str, *, lesson_pdf: Path, file_obj=None) -> dict:
        result = self.llm.generate_structured_json(
            prompt,
            file_path=None if file_obj is not None else str(lesson_pdf),
            file_obj=file_obj,
        )
        if not isinstance(result, dict):
            print(f"     ⚠️ Task 1 子任务返回 {type(result).__name__}，已按空结果处理。")
            return {}
        return result

    def _course_content(self, result: dict) -> dict:
        return result.get("course_content") if isinstance(result.get("course_content"), dict) else {}

    def _merge_core_text(self, payload: dict, result: dict) -> None:
        metadata = result.get("lesson_metadata") if isinstance(result.get("lesson_metadata"), dict) else {}
        if metadata.get("title"):
            payload["lesson_metadata"]["title"] = metadata["title"]
        if metadata.get("title_localized"):
            payload["lesson_metadata"]["title_localized"] = metadata["title_localized"]
        if metadata.get("topic_title"):
            payload["lesson_metadata"]["topic_title"] = metadata["topic_title"]
        if metadata.get("topic_title_localized"):
            payload["lesson_metadata"]["topic_title_localized"] = metadata["topic_title_localized"]
        if isinstance(metadata.get("section_titles"), list):
            payload["lesson_metadata"]["section_titles"] = metadata["section_titles"]
        if metadata.get("content_type"):
            payload["lesson_metadata"]["content_type"] = metadata["content_type"]

        content = self._course_content(result)
        target = payload["course_content"]
        target["sentence_patterns"] = self._as_list(content.get("sentence_patterns"))
        target["example_sentences"] = self._split_example_sentences(
            self._as_list(content.get("example_sentences"))
        )
        dialogue = content.get("dialogue") if isinstance(content.get("dialogue"), dict) else {}
        target["dialogue"] = {
            "title": dialogue.get("title") or "会話",
            "title_localized": dialogue.get("title_localized") or "会话",
            "lines": self._as_list(dialogue.get("lines")),
        }

    def _merge_vocabulary(self, payload: dict, result: dict) -> None:
        content = self._course_content(result)
        payload["course_content"]["vocabulary"] = self._as_list(content.get("vocabulary"))
        payload["course_content"]["lexical_notes"] = self._as_list(content.get("lexical_notes"))
        payload["course_content"]["display_only_vocabulary"] = self._as_list(
            content.get("display_only_vocabulary")
        )

    def _merge_grammar(self, payload: dict, result: dict) -> None:
        content = self._course_content(result)
        payload["course_content"]["grammar_sections"] = self._as_list(content.get("grammar_sections"))

    def _merge_practice(self, payload: dict, result: dict) -> None:
        content = self._course_content(result)
        payload["course_content"]["practice_source"] = self._as_list(content.get("practice_source"))
        payload["practice_items"] = self._as_list(result.get("practice_items"))

    def _as_list(self, value) -> list:
        return value if isinstance(value, list) else []

    def _split_example_sentences(self, items: list[dict]) -> list[dict]:
        normalized = []
        for item in items or []:
            split_items = self._split_example_item(item)
            if split_items:
                normalized.extend(split_items)
        for index, item in enumerate(normalized, start=1):
            if isinstance(item, dict):
                item["line_ref"] = index
        return normalized

    def _split_example_item(self, item: dict) -> list[dict]:
        if not isinstance(item, dict):
            return []
        text = (item.get("text") or item.get("ja") or "").strip()
        if not text:
            return []
        text_parts = self._split_ja_utterances(text)
        if len(text_parts) <= 1:
            return [item]

        translation_parts = self._split_translation_utterances(
            (item.get("translation") or "").strip()
        )
        if translation_parts and len(translation_parts) != len(text_parts):
            return [item]

        reading_parts = self._split_ja_utterances((item.get("reading") or "").strip())
        romaji_parts = self._split_translation_utterances((item.get("romaji") or "").strip())
        split_items = []
        for index, text_part in enumerate(text_parts):
            child = dict(item)
            child["text"] = text_part
            child["translation"] = translation_parts[index] if translation_parts else ""
            child["reading"] = reading_parts[index] if len(reading_parts) == len(text_parts) else ""
            child["romaji"] = romaji_parts[index] if len(romaji_parts) == len(text_parts) else ""
            child["tokens"] = []
            split_items.append(child)
        return split_items

    def _split_ja_utterances(self, value: str) -> list[str]:
        normalized = self._normalize_example_boundary_text(value)
        if not normalized:
            return []
        parts = [
            part.strip(" \t\r\n…")
            for part in re.findall(r"[^。！？!?]+[。！？!?]", normalized)
        ]
        return [part for part in parts if part]

    def _split_translation_utterances(self, value: str) -> list[str]:
        normalized = self._normalize_example_boundary_text(value)
        if not normalized:
            return []
        parts = [
            part.strip(" \t\r\n…")
            for part in re.findall(r"[^。！？!?]+[。！？!?]", normalized)
        ]
        return [part for part in parts if part]

    def _normalize_example_boundary_text(self, value: str) -> str:
        normalized = str(value or "").strip()
        normalized = re.sub(r"[.．]{2,}|…{1,}", "。", normalized)
        return normalized

    def _print_counts(self, label: str, payload: dict) -> None:
        content = payload.get("course_content") if isinstance(payload.get("course_content"), dict) else {}
        dialogue = content.get("dialogue") if isinstance(content.get("dialogue"), dict) else {}
        print(
            f"        📊 {label}: "
            f"文型={len(content.get('sentence_patterns') or [])}, "
            f"例文={len(content.get('example_sentences') or [])}, "
            f"会話={len(dialogue.get('lines') or [])}, "
            f"vocab={len(content.get('vocabulary') or [])}, "
            f"display_only={len(content.get('display_only_vocabulary') or [])}, "
            f"grammar={len(content.get('grammar_sections') or [])}, "
            f"practice_source={len(content.get('practice_source') or [])}, "
            f"practice_items={len(payload.get('practice_items') or [])}"
        )


def normalize_lesson_data(
    data: dict,
    lesson_id: int,
    source_pdf: Path,
    lesson_pdf: Path,
    support_language: str = "zh",
    course_id: int | str = book1.COURSE_ID,
) -> dict:
    return MinnaNoNihongoLessonNormalizer().run(
        data,
        lesson_id=lesson_id,
        source_pdf=source_pdf,
        lesson_pdf=lesson_pdf,
        support_language=support_language,
        course_id=course_id,
    )


def build_placeholder_lesson_data(
    lesson_id: int,
    source_pdf: Path,
    lesson_pdf: Path,
    support_language: str = "zh",
    course_id: int | str = book1.COURSE_ID,
) -> dict:
    """Small deterministic payload for wiring tests and first-run sanity checks."""

    profile = resolve_lesson_profile(lesson_id)
    if profile.pedagogy_profile == "intermediate_read_write_speak_listen_grammar":
        raw = {
            "lesson_metadata": {
                "title": f"第{profile.source_lesson}課",
                "title_localized": f"第{profile.source_lesson}课",
                "topic_title": "お願いがあるんですが",
                "topic_title_localized": "有件事想拜托",
                "section_titles": [
                    {
                        "section": "読む・書く",
                        "title": "お願いがあるんですが",
                        "title_localized": "有件事想拜托",
                    },
                    {
                        "section": "話す・聞く",
                        "title": "依頼の会話",
                        "title_localized": "请求场景会话",
                    },
                    {
                        "section": "文法・練習",
                        "title": "丁寧に依頼する",
                        "title_localized": "礼貌地提出请求",
                    },
                ],
                "content_type": profile.content_type,
            },
            "course_content": {
                "sentence_patterns": [
                    {
                        "text": "この本を返していただけませんか。",
                        "reading": "このほんをかえしていただけませんか。",
                        "romaji": "kono hon o kaeshite itadakemasen ka.",
                        "translation": "能请您把这本书还给我吗？",
                        "grammar_focus": ["〜ていただけませんか"],
                        "source_section": "話す・聞く",
                    }
                ],
                "example_sentences": [
                    {
                        "text": "日本語で文章を書くことは、とても勉強になります。",
                        "reading": "にほんごでぶんしょうをかくことは、とてもべんきょうになります。",
                        "romaji": "nihongo de bunshou o kaku koto wa, totemo benkyou ni narimasu.",
                        "translation": "用日语写文章很有学习价值。",
                        "source_section": "読む・書く",
                    }
                ],
                "dialogue": {
                    "title": "話す・聞く",
                    "title_localized": "会话与听力",
                    "lines": [
                        {
                            "speaker": "A",
                            "text": "すみません、この書類を見ていただけませんか。",
                            "reading": "すみません、このしょるいをみていただけませんか。",
                            "romaji": "sumimasen, kono shorui o mite itadakemasen ka.",
                            "translation": "不好意思，能请您看一下这份文件吗？",
                            "source_section": "話す・聞く",
                        }
                    ],
                },
                "vocabulary": [
                    {
                        "term": "返す",
                        "reading": "かえす",
                        "romaji": "kaesu",
                        "part_of_speech": "动词",
                        "translation": "归还",
                        "lesson_section": "core",
                        "source_section": "話す・聞く",
                    },
                    {
                        "term": "文章",
                        "reading": "ぶんしょう",
                        "romaji": "bunshou",
                        "part_of_speech": "名词",
                        "translation": "文章",
                        "lesson_section": "core",
                        "source_section": "読む・書く",
                    },
                ],
                "display_only_vocabulary": [
                    {
                        "term": "IMC",
                        "reading": "アイエムシー",
                        "romaji": "ai emu shii",
                        "category": "organization_name",
                        "translation": "IMC 公司",
                        "reason": "display_only",
                        "source_section": "話す・聞く",
                    }
                ],
                "grammar_sections": [
                    {
                        "title": "〜ていただけませんか",
                        "explanation": "用于礼貌地请求对方为自己做某事，比「〜てください」更客气。",
                        "patterns": [{"text": "Vて いただけませんか", "translation": "能请您……吗？"}],
                        "examples": [
                            {
                                "text": "この本を返していただけませんか。",
                                "reading": "このほんをかえしていただけませんか。",
                                "translation": "能请您把这本书还给我吗？",
                            }
                        ],
                    }
                ],
                "practice_source": [
                    {
                        "section": "文法・練習",
                        "instruction": "依頼の表現を練習する。",
                        "pattern": "Vて いただけませんか",
                        "examples": ["返します -> 返していただけませんか"],
                        "source_section": "文法・練習",
                    }
                ],
            },
        }
        return normalize_lesson_data(
            raw,
            lesson_id=lesson_id,
            source_pdf=source_pdf,
            lesson_pdf=lesson_pdf,
            support_language=support_language,
            course_id=course_id,
        )

    raw = {
        "lesson_metadata": {
            "title": f"第{profile.source_lesson}課",
            "title_localized": f"第{profile.source_lesson}课",
            "topic_title": "",
            "topic_title_localized": "",
            "section_titles": [],
        },
        "course_content": {
            "sentence_patterns": [
                {
                    "text": "わたしは学生です。",
                    "reading": "わたしは がくせいです。",
                    "romaji": "watashi wa gakusei desu.",
                    "translation": "我是学生。",
                    "grammar_focus": ["N1 は N2 です"],
                }
            ],
            "example_sentences": [
                {
                    "speaker": "Example",
                    "text": "わたしは学生です。",
                    "reading": "わたしは がくせいです。",
                    "romaji": "watashi wa gakusei desu.",
                    "translation": "我是学生。",
                }
            ],
            "dialogue": {
                "title": "会話",
                "title_localized": "会话",
                "lines": [
                    {
                        "speaker": "A",
                        "text": "はじめまして。",
                        "reading": "はじめまして。",
                        "romaji": "hajimemashite.",
                        "translation": "初次见面。",
                    }
                ],
            },
            "vocabulary": [
                {
                    "term": "学生",
                    "reading": "がくせい",
                    "romaji": "gakusei",
                    "part_of_speech": "名词",
                    "translation": "学生",
                    "lesson_section": "core",
                },
                {
                    "term": "銀行員",
                    "reading": "ぎんこういん",
                    "romaji": "ginkouin",
                    "part_of_speech": "名词",
                    "translation": "银行职员",
                    "lesson_section": "supplementary",
                },
            ],
            "display_only_vocabulary": [
                {
                    "term": "マイク・ミラー",
                    "reading": "マイク・ミラー",
                    "romaji": "Maiku Miraa",
                    "category": "person_name",
                    "translation": "迈克·米勒",
                    "reason": "lesson_dialogue_character",
                }
            ],
            "grammar_sections": [
                {
                    "title": "N1 は N2 です",
                    "explanation": "用来说明身份、职业或属性。",
                    "patterns": [{"text": "N1 は N2 です", "translation": "N1 是 N2。"}],
                }
            ],
        },
    }
    return normalize_lesson_data(
        raw,
        lesson_id=lesson_id,
        source_pdf=source_pdf,
        lesson_pdf=lesson_pdf,
        support_language=support_language,
        course_id=course_id,
    )
