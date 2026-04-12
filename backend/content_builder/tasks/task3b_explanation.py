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
        【本轮生成目标：逐句讲解阶段】
        - 严格按课文对话顺序，一句一句讲解所有对话行，不得跳过任何一句。
        - 允许的 segment_type：line_walkthrough、vocabulary_focus、usage_focus。
        - 严禁生成 grammar_focus 和 recap，语法点留给 advanced 轮。
        - 遇到句子中的新词可以穿插 vocabulary_focus，但不要展开系统语法讲解。
        - 每一句课文必须有自己的 line_walkthrough，极短重复句可以简短带过（6-8秒）。
        - 建议生成 4-8 个 segments；覆盖全部对话行优先，数量不是硬性限制。
            """
        else:
            batch_guidance = """
        【本轮生成目标：语法讲解阶段】
        - 本轮只讲语法点，不重复逐句讲解对话。
        - 必须覆盖 teaching_materials.grammar_sections 中的每一个语法点，按教材顺序逐一展开。
        - 每个 grammar_section 对应一个或多个 grammar_focus segment，不得遗漏。
        - 讲解语法点时，优先引用前一轮已讲过的对话句子作为例子（通过 source_line_refs 标注），帮助学生建立联系。
        - 数字、日期、时间等系统性语法点必须完整展开，不能简略带过。
        - 最后必须包含 1 个 recap segment。
        - 建议生成 3-6 个 segments（grammar_focus 数量 = grammar_sections 数量），加 1 个 recap。
            """

        return f"""
        你是一位专业的中文教学视频老师。你的任务不是设计剧情，而是根据课文内容生成一段结构清晰、适合后续模板动画与配音合成的【教学讲解脚本】。
        只输出合法 JSON，不要包含任何 Markdown。

        课程内容：
        {content_str}

        {batch_guidance}

        【任务目标】
        1. 将本课拆分为结构清晰的讲解片段，严格按”① 逐句讲解全部对话 → ② 逐一展开所有语法点 → ③ 总结回顾”的顺序组织，两个阶段不交叉。
        2. 讲解对象是以英文为母语的中文学习者，英文讲解必须清晰自然、教学性强。
        3. foundation 轮专注对话理解，advanced 轮专注语法系统讲解，两轮合并后形成完整的”情境→规律”学习路径。
        4. 【一句一页原则】每个 line_walkthrough segment 的 source_line_refs 必须只包含 1 个 line ref，即一句课文对应一个独立页面。即使是问答对（问句+答句），也必须拆成两个独立的 segment，不得合并。严禁把多句课文塞进同一个 line_walkthrough。
        5. 每一句课文都必须有至少一个 segment_type 为 “line_walkthrough” 的片段来明确讲解它，仅在 grammar_focus 或其他类型中引用 source_line_refs 不算覆盖。
        6. 对非常短的重复句（例如重复的”你好”）可以用简短的 line_walkthrough（estimated_duration_seconds 设为 6-8）快速说明其回应功能，不必展开成冗长解释。
        7. teaching_materials 中的 language_notes 和 grammar_sections 是本次讲解的重要依据，必须优先参考，不要只依赖对话正文自行推断。
        8. grammar_points 可作为补充素材，但教材原有的 grammar_sections 优先级更高。
        9. vocabulary 用于识别和组织高亮新词。
        10. 每个片段都要适合后续做成教学卡片视频，而不是影视剧情。
        11. 只保留一条英文主字幕/主讲解文本，不要输出中文整段讲稿。
        12. 中文内容只保留在重点词、重点句和屏幕展示字段里。
        18. 【旁白语言规则 — TTS 友好】narration.subtitle_en 以英文为主，适合 TTS 朗读：
            - 严禁在旁白中直接嵌入裸汉字（不加标记），TTS 无法正确处理语言切换。
            - 严禁在旁白中出现带声调拼音（如 nǐ hǎo），TTS 会将其读成英文乱音。
            - 如需在旁白中让学生听到某个中文词的发音，使用 [zh:汉字] 标记语法（标记内填汉字，不要填拼音），例如：
              * "The greeting [zh:你好] is the most common way to say hello."
              * "This line opens with [zh:请问], a polite way to ask for information."
              * "The key verb here is [zh:是], meaning 'to be'."
            - [zh:...] 标记内的汉字会被 TTS 正确识别并朗读，读完后自动停顿。
            - 每句话最多嵌入 1-2 个 [zh:...] 标记；不要连续堆叠多个标记，每段关键词出现一次即可。
            - 标记只用于需要学生听到发音的核心词或短句（通常是 focus_text 中的关键词），不要对每个汉字都加标记。
            - 声调变化描述用英文文字：例如 "the first syllable shifts from third tone to second tone"。
            - 汉字全文留给屏幕展示字段（on_screen_text.focus_text / focus_pinyin），旁白不重复。
        17. 【旁白详细度要求】narration.subtitle_en 必须足够详细，让学生仅靠听旁白就能理解该段内容，不能只是一两句带过。具体要求：
            - line_walkthrough：至少 4-6 句话，需涵盖：① 句子含义 ② 逐词拆解（每个关键汉字/词的意思）③ 发音要点或声调提示 ④ 使用场景或文化背景（如有）。
            - grammar_focus：至少 5-8 句话，需涵盖：① 语法规律说明 ② 2-3 个实例演示 ③ 常见错误提示 ④ 与之前所学内容的联系。
            - vocabulary_focus：至少 4-6 句话，需涵盖：① 每个词的含义 ② 汉字构成解析 ③ 使用场景举例。
            - usage_focus：至少 4-6 句话，需涵盖：① 正确用法说明 ② 错误用法警示及原因 ③ 记忆技巧。
            - 所有段落的 estimated_duration_seconds 必须与旁白长度匹配：默认 line_walkthrough 18-22 秒，grammar_focus 25-35 秒，vocabulary_focus 18-25 秒，usage_focus 20-28 秒，recap 15-20 秒。
        13. on_screen_text.main_title 必须固定为本课课文标题。
        14. highlight_words 用于本段涉及的新词；grammar_points 用于本段涉及的新语法。
        15. 在适合的高频词、礼貌表达或合成词上，可以加入简短的汉字结构/构词说明，帮助初学者理解，但不要把整段变成文字学课程。
        16. 汉字结构说明必须服务理解，长度要短，优先解释”这个词由哪些常见汉字组成，以及组合后为什么是这个意思”。

        【输出要求】
        1. global_config 中给出统一讲解风格，并明确 target audience。
        2. segments 中每条都必须说明其对应课文的哪一句或哪几句。
        3. narration 只保留 subtitle_en 一个字段。
        4. 不要输出 subtitle_tracks。
        5. estimated_duration_seconds 只是建议值，不是硬约束。旁白内容长度优先，时长跟着旁白走，不要为了压缩时长而缩短旁白。
        6. 不要重复情景演绎内容，要强调解释和教学。
        7. foundation + advanced 两轮合起来后，必须覆盖全部课文 line refs，且每个 line ref 必须在某个 line_walkthrough 的 source_line_refs 中出现，不得遗漏。
        8. 如果某个 segment 是快速带过重复句，请在 narration 里明确点出这是回复、重复问候或简短承接句。
        9. segment 数量不是硬性 KPI；优先保证逐句覆盖、教学完整和节奏自然。通常整课建议在 8-16 个 segments 左右（含语法段），但必要时可以略多。
        10. recap segment 的 highlight_words 必须列出本课 4-6 个最值得回顾的内容，可以是：
            - 核心句型或短句，例如 "你好！" / "你贵姓？" / "我叫..."
            - 本课重点单词，例如 "姓" / "请问" / "名字"
            - 优先选句型，词汇作为补充；具体比例根据课文内容自然决定，不强制要求全是句型或全是单词。
            每条格式：word（句型或词）、pinyin（拼音）、english（简短英文释义）。
            这些内容将在总结页面以突出样式展示，帮助学生快速回顾本课重点。

        【segment_type 可选值】
        "line_walkthrough", "vocabulary_focus", "grammar_focus", "usage_focus", "recap"

        【template_name 字段规则】
        - 每个 segment 必须包含 template_name 字段。
        - 默认映射：line_walkthrough→"line_focus"、vocabulary_focus→"vocab_spotlight"、grammar_focus→"grammar_pattern"、usage_focus→"usage_note"、recap→"lesson_recap"。
        - 例外：当 grammar_focus 内容属于枚举型汉字集合或规律表时，必须将 template_name 设为 "grammar_table"，同时在 visual_blocks 字段中输出对应数据块（见 grammar_table 格式规则），不得使用 grammar_points 字段。

        【字段格式约束】
        - on_screen_text.focus_text 格式规则：
          * 只写汉字和标点，绝对不要把拼音内嵌进文本，禁止 "不(bù)+是(shì)→不是(búshì)" 这类写法；拼音统一放 focus_pinyin 字段。
          * line_walkthrough / usage_focus：直接写课文句子，例如 "你好！" 或 "请问，你贵姓？"
          * vocabulary_focus：多个词用" / "分隔，例如 "请 / 问 / 贵 / 姓"
          * grammar_focus：如果展示问答句型，必须用 "Q: 问句 A: 答句" 格式，例如 "Q: 你贵姓？ A: 我姓王。"；如果正反两种回答都需要展示，A 部分用 " / " 分隔，例如 "Q: 你是老师吗？ A: 我是老师。/ 我不是老师。"；如果只展示单句句型，直接写句子。【严禁使用 "A: 句 / B: 句" 这类字母标签格式，只允许 Q:/A: 格式或纯句子。】Q: 部分后面必须有对应的 A: 部分，不得只写 Q: 而省略 A: 部分。
          * 【关键规则】顶层 " / " 分隔符只用于分隔两个完整的、结构相近的平行句型（例如 "我是老师。/ 我不是老师。"）。绝对禁止用 "/" 表示同一槽位内的备选词，例如 "这/那 + 个 + Noun" 是错误写法。备选词必须用方括号包裹，例如 "[这/那] + 个 + Noun"。方括号内的 "/" 不会被解析为分隔符，整个括号内容作为一个整体显示。
          * recap：写 "Key Phrases Review"
        - on_screen_text.focus_gloss_en 格式规则：
          * 如果对应的 focus_text 是问答句型（Q:/A: 格式），focus_gloss_en 也必须用 "Q: 英文问句 A: 英文答句" 格式，例如 "Q: What is your honorable surname? A: My surname is Wang."
          * 如果是单句，直接写英文翻译。
          * 不要用 "/" 分隔问答翻译。
        - usage_focus segment 字段格式规则（template_name 固定为 "usage_note"）：
          * highlight_words：【必填，不得为空数组】列出 2-4 个本段对比的核心词汇（如 姓、贵姓），含 word/pinyin/english/explanation_en。
          * visual_blocks 中 usage_context 块的 content.notes：【必填，不得为空字符串】必须用 "Correct: 正确中文例句。 Incorrect: 错误中文例句。" 格式，从本段讲解的错误中选最典型的一对，只写一对对比句，简洁明确。示例：notes: "Correct: 我姓王。 Incorrect: 我贵姓王。"
          * content.focus_gloss_en：用一句英文概括使用规则，例如 "Use 我姓 not 我贵姓 in your answer."
          * narration_track.subtitle_en：放完整的讲解段落（可较长），这段文字只在字幕中逐句显示，不要出现在任何可视区字段里。
        - grammar_focus segment 布局规则：
          * 每个 grammar_focus segment 的 grammar_points[] 最多包含 4 条 pattern，超出必须拆成多个 segment。
          * 对于系统性语法（如数字、日期、时间），必须按教材的教学顺序逐步展开：先讲基础（如 0-10），再讲进阶（如 11-99），不得跳过基础直接讲复合形式。如有必要，拆成"基础篇"和"进阶篇"两个 segment。
          * 每个 pattern 对应一条独立的教学规律或句型，不要把多条规律压缩成一条。
          * 对于枚举型语法内容（数字 0-10、月份、量词集合等）或结构规律表（如数字构成规律），优先使用 template_name: "grammar_table" 而非 "grammar_pattern"，见下方格式规则。
        - grammar_table segment 格式规则（template_name 固定为 "grammar_table"）：
          * 适用场景：
            - char_grid：内容是有限个汉字的枚举集合（如数字 0-10、星期一到日、月份、量词），每个字有独立拼音和英文释义。
            - pattern_table：内容是系统性构成规律表（如数字 11-99 的三种构成方式、日期表达格式），有明确的"规律 + 适用范围 + 例子"三列结构。
          * 一个 segment 只放一种 block_type（char_grid 或 pattern_table），内容多时拆成两个 segment，不要强行塞进同一页。
          * char_grid 的 items 数量：建议 6-12 个，超过 12 个必须拆分。
          * pattern_table 的 rows 数量：建议 2-4 行，超过 4 行必须拆分。
          * char_grid 字段：
            - title：内容类型标题，例如 "Numbers 0–10"
            - items[]：每项含 char（汉字）、pinyin（拼音）、english（简短英文释义）
            - note（可选）：关于整组内容的简短补充说明
          * pattern_table 字段：
            - title：规律表标题，例如 "Forming Numbers 11–99"
            - rows[]：每行含 pattern（语法结构式，可用 [Placeholder]）、pattern_pinyin（结构式中汉字的拼音，不含 [Placeholder] 内部）、range（适用范围，如 "11–19"）、example（汉字例子）、example_pinyin、example_english
            - note（可选）：表格下方的补充说明
          * on_screen_text 字段对 grammar_table 不适用，可留空或省略。
          * grammar_table segment 示例（数字语法点 → 两个 segment）：
            Segment A 使用 char_grid：block_type 为 "char_grid"，content 含 title 和 items 数组，每项含 char/pinyin/english。
            Segment B 使用 pattern_table：block_type 为 "pattern_table"，content 含 title 和 rows 数组，每行含 pattern/pattern_pinyin/range/example/example_pinyin/example_english。
        - grammar_points[].pattern 格式规则：
          * 如果是问答例句，必须用 "Q: 问句 A: 答句" 格式，例如 "Q: 你叫什么名字？ A: 我叫李友。"
          * 如果是语法结构式，可以使用 [Placeholder] 占位符表示可替换成分，例如 "[Statement], [Pronoun]+呢？" 或 "我叫 [Full Name]。"
          * [Placeholder] 内的备选用 "|" 表示，例如 "[Noun|Pronoun]"，不要用 "/"，避免被误识别为句型分隔符。
          * 如果需要在句型结构中表示"A 或 B"的备选词（非占位符），用方括号包裹并用 "/" 分隔，例如 "[这/那] + 个 + Noun"。此时括号内的 "/" 不会被解析为分隔符。
          * 不要用"/"或"→"分隔问答句，问答必须用 Q:/A: 格式。
        - grammar_points[].pattern_pinyin 格式规则：
          * 必须填写，对应 pattern 中所有汉字（按出现顺序，不含 [Placeholder] 内部文字）的完整拼音字符串。
          * Q:A: 格式时，连续写出问句汉字拼音再接答句汉字拼音，中间用空格自然分隔，例如 "Nǐ jiào shénme míngzi? Wǒ jiào Lǐ Yǒu."
          * 结构式有 [Placeholder] 时，只写括号外汉字的拼音，例如 "我叫 [Full Name]。" → pattern_pinyin 为 "Wǒ jiào"。

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
              "template_name": "line_focus",
              "source_line_refs": [1],
              "segment_title": "片段标题",
              "teaching_goal": "这一段想教会学生什么",
              "narration": {{
                "subtitle_en": "English teaching script with key Chinese phrases embedded when needed"
              }},
              "on_screen_text": {{
                "main_title": "本课课文标题",
                "focus_text": "按字段格式约束填写，grammar_focus 示例：Q: 你贵姓？ A: 我姓王。",
                "focus_pinyin": "focus_text 中所有汉字的完整拼音（按出现顺序，包含 Q/A 全部行，不得只写第一句）。示例：Q: 你贵姓？ A: 我姓王。→ 'Nǐ guì xìng? Wǒ xìng Wáng.'",
                "focus_gloss_en": "英文释义",
                "notes": "辅助说明"
              }},
              "highlight_words": [
                {{
                  "word": "新词",
                  "pinyin": "pinyin",
                  "english": "English meaning",
                  "explanation_en": "English explanation",
                  "character_insight_en": "Optional short note explaining the word's character makeup or how the characters combine in meaning"
                }}
              ],
              "grammar_points": [
                {{
                  "pattern": "例句或结构式。问答示例：Q: 你叫什么名字？ A: 我叫李友。结构式示例：[Statement], [Pronoun]+呢？",
                  "pattern_pinyin": "Nǐ jiào shénme míngzi? Wǒ jiào Lǐ Yǒu.",
                  "explanation_en": "English explanation of the grammar structure or usage rule"
                }}
              ],
              "visual_notes": "后续制作教学卡片时的视觉提示",
              "estimated_duration_seconds": 12
            }},
            {{
              "segment_id": 2,
              "segment_type": "grammar_focus",
              "template_name": "grammar_table",
              "source_line_refs": [],
              "segment_title": "片段标题（如 Numbers: 0–10）",
              "teaching_goal": "这一段的教学目标",
              "narration": {{
                "subtitle_en": "English teaching script for this segment"
              }},
              "visual_blocks": [
                {{
                  "block_type": "char_grid",
                  "content": {{
                    "title": "Numbers 0–10",
                    "items": [
                      {{"char": "○", "pinyin": "líng", "english": "zero"}},
                      {{"char": "一", "pinyin": "yī", "english": "one"}}
                    ],
                    "note": "Optional supplementary note"
                  }}
                }}
              ],
              "highlight_words": [],
              "grammar_points": [],
              "estimated_duration_seconds": 14
            }}
          ]
        }}
        """

    def _flatten_dialogue_lines(self, dialogues: list) -> list:
        flattened = []
        running_ref = 1

        for section in dialogues or []:
            if not isinstance(section, dict):
                continue

            # Flat format: {"role": ..., "chinese": ..., "english": ...}
            if "chinese" in section:
                hanzi = (section.get("chinese") or "").strip()
                english = (section.get("english") or "").strip()
                if hanzi:
                    flattened.append({
                        "line_ref": running_ref,
                        "hanzi": hanzi,
                        "pinyin": "",
                        "english": english,
                    })
                    running_ref += 1

            # Legacy format: {"lines": [{"words": [...], "english": ...}]}
            elif "lines" in section:
                for line in section.get("lines", []):
                    if not isinstance(line, dict):
                        continue
                    words = line.get("words", [])
                    hanzi = "".join(
                        token.get("cn", "")
                        for token in words
                        if isinstance(token, dict)
                    ).strip()
                    pinyin = " ".join(
                        token.get("py", "").strip()
                        for token in words
                        if isinstance(token, dict) and token.get("py")
                    ).strip()
                    english = (line.get("english") or "").strip()
                    flattened.append({
                        "line_ref": running_ref,
                        "hanzi": hanzi,
                        "pinyin": pinyin,
                        "english": english,
                    })
                    running_ref += 1

        return flattened

    def _build_missing_line_segment(self, line_item: dict, segment_id: int, lesson_title: str) -> dict:
        hanzi = (line_item.get("hanzi") or "").strip()
        english = (line_item.get("english") or "").strip()
        pinyin = (line_item.get("pinyin") or "").strip()
        line_ref = line_item.get("line_ref")

        is_short_reply = len(hanzi) <= 4
        meaning_clause = f" It means: {english}." if english else ""
        subtitle_en = (
            f"This short line works as a quick natural reply in the conversation.{meaning_clause}"
            if is_short_reply
            else f"In this line the speaker makes a statement that helps move the conversation forward naturally.{meaning_clause}"
        )

        return {
            "segment_id": segment_id,
            "segment_type": "line_walkthrough",
            "source_line_refs": [line_ref] if line_ref else [],
            "segment_title": f"Quick Walkthrough: {hanzi}" if hanzi else "Quick Walkthrough",
            "teaching_goal": "Make sure this dialogue line is explicitly covered in the lesson explanation.",
            "narration": {
                "subtitle_en": subtitle_en.strip()
            },
            "on_screen_text": {
                "main_title": lesson_title,
                "focus_text": hanzi,
                "focus_pinyin": pinyin,
                "focus_gloss_en": english,
                "notes": "Quick coverage for a short or lightly emphasized line."
            },
            "highlight_words": [],
            "grammar_points": [],
            "visual_notes": "Keep this segment brief and visually simple, like a quick reinforcement card.",
            "estimated_duration_seconds": 7,
        }

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
        highlight_words = segment.get("highlight_words", []) if isinstance(segment.get("highlight_words"), list) else []
        normalized_highlights = []
        for item in highlight_words:
            if not isinstance(item, dict):
                continue
            normalized_highlights.append({
                "word": (item.get("word") or "").strip(),
                "pinyin": (item.get("pinyin") or "").strip(),
                "english": (item.get("english") or "").strip(),
                "explanation_en": (item.get("explanation_en") or "").strip(),
                "character_insight_en": (item.get("character_insight_en") or "").strip(),
            })

        result = {
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
            "highlight_words": normalized_highlights,
            "grammar_points": segment.get("grammar_points", []) if isinstance(segment.get("grammar_points"), list) else [],
            "visual_notes": (segment.get("visual_notes") or "").strip(),
            "estimated_duration_seconds": segment.get("estimated_duration_seconds", 12),
        }
        # Preserve grammar_table overrides from AI output
        if (segment.get("template_name") or "").strip() == "grammar_table":
            result["template_name"] = "grammar_table"
            raw_vb = segment.get("visual_blocks")
            if isinstance(raw_vb, list):
                result["visual_blocks"] = raw_vb
        return result

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
        flattened_lines = self._flatten_dialogue_lines(dialogues or [])
        all_line_refs = [item["line_ref"] for item in flattened_lines if item.get("line_ref")]
        # Only line_walkthrough / usage_focus counts as true coverage.
        # grammar_focus / vocabulary_focus referencing a line is NOT sufficient.
        WALKTHROUGH_TYPES = {"line_walkthrough", "usage_focus"}
        covered_line_refs = set()
        for segment in merged_segments:
            if not isinstance(segment, dict):
                continue
            if segment.get("segment_type") not in WALKTHROUGH_TYPES:
                continue
            refs = segment.get("source_line_refs", [])
            if isinstance(refs, list):
                for ref in refs:
                    if isinstance(ref, int):
                        covered_line_refs.add(ref)

        missing_line_refs = [ref for ref in all_line_refs if ref not in covered_line_refs]
        if missing_line_refs:
            print(f"  ⚠️ Task 3B 检测到未覆盖课文行 {missing_line_refs}，正在自动补全简短讲解片段...")
            line_lookup = {item["line_ref"]: item for item in flattened_lines}
            fallback_segments = []
            for ref in missing_line_refs:
                line_item = line_lookup.get(ref)
                if not line_item:
                    continue
                fallback_segments.append(self._build_missing_line_segment(line_item, 0, lesson_title))

            if fallback_segments:
                # Insert each fallback before the first existing segment that references the same line.
                # This ensures grammar segments derived from that line come AFTER its walkthrough.
                # Fall back to inserting before recap if nothing else references that line.
                for fallback in sorted(fallback_segments, key=lambda s: (s.get("source_line_refs") or [0])[0]):
                    fallback_ref = (fallback.get("source_line_refs") or [0])[0]
                    insert_idx = next(
                        (i for i, seg in enumerate(merged_segments)
                         if isinstance(seg, dict)
                         and isinstance(seg.get("source_line_refs"), list)
                         and fallback_ref in seg["source_line_refs"]),
                        None,
                    )
                    if insert_idx is None:
                        # Nothing references this line — insert before recap
                        insert_idx = next(
                            (i for i, s in enumerate(merged_segments)
                             if isinstance(s, dict) and s.get("segment_type") == "recap"),
                            len(merged_segments),
                        )
                    merged_segments.insert(insert_idx, fallback)

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
