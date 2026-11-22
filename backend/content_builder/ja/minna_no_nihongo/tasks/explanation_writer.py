from __future__ import annotations

import json

try:
    from content_builder.core.llm_providers import BaseLLMProvider
    from content_builder.ja.minna_no_nihongo.tasks.teaching_flow_builder import split_vocabulary_by_section
except ImportError:
    from content_builder.core.llm_providers import BaseLLMProvider
    from content_builder.ja.minna_no_nihongo.tasks.teaching_flow_builder import split_vocabulary_by_section


def _compact_line(item: dict, index: int) -> dict:
    return {
        "index": index,
        "text": (item.get("text") or "").strip(),
        "reading": (item.get("reading") or "").strip(),
        "translation": (item.get("translation") or item.get("definition") or "").strip(),
        "speaker": (item.get("speaker") or "").strip(),
    }


def _compact_vocab(item: dict, index: int) -> dict:
    return {
        "index": index,
        "term": (item.get("term") or item.get("word") or "").strip(),
        "reading": (item.get("reading") or "").strip(),
        "translation": (item.get("translation") or item.get("definition") or "").strip(),
        "part_of_speech": (item.get("part_of_speech") or item.get("category") or "").strip(),
        "lesson_section": (item.get("lesson_section") or "core").strip(),
    }


def _compact_grammar(section: dict, index: int) -> dict:
    return {
        "index": index,
        "title": (section.get("title") or "").strip(),
        "explanation": (section.get("explanation") or "").strip(),
        "patterns": [
            {
                "text": (pattern.get("text") or "").strip(),
                "translation": (pattern.get("translation") or "").strip(),
            }
            for pattern in (section.get("patterns") or [])[:4]
            if isinstance(pattern, dict)
        ],
        "examples": [
            {
                "text": (example.get("text") or "").strip(),
                "reading": (example.get("reading") or "").strip(),
                "translation": (example.get("translation") or "").strip(),
            }
            for example in (section.get("examples") or [])[:4]
            if isinstance(example, dict)
        ],
    }


def _replace_old_pinyin_keys(value):
    if isinstance(value, dict):
        cleaned = {}
        for key, child in value.items():
            new_key = "reading" if key == "pinyin" else key
            if new_key in cleaned and new_key == "reading":
                continue
            cleaned[new_key] = _replace_old_pinyin_keys(child)
        return cleaned
    if isinstance(value, list):
        return [_replace_old_pinyin_keys(item) for item in value]
    return value


class MinnaNoNihongoExplanationWriter:
    """Ask the LLM to direct the teaching explanation without owning rendering details."""

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider

    def _build_context(self, metadata: dict, course_content: dict, teaching_materials: dict | None) -> dict:
        dialogue = course_content.get("dialogue") if isinstance(course_content.get("dialogue"), dict) else {}
        vocabulary = course_content.get("vocabulary") if isinstance(course_content.get("vocabulary"), list) else []
        core_vocabulary, supplementary_vocabulary = split_vocabulary_by_section(vocabulary)
        display_only = (
            course_content.get("display_only_vocabulary")
            if isinstance(course_content.get("display_only_vocabulary"), list)
            else []
        )
        grammar_sections = (
            course_content.get("grammar_sections")
            if isinstance(course_content.get("grammar_sections"), list)
            else []
        )
        return {
            "metadata": {
                "lesson_id": metadata.get("lesson_id"),
                "title": metadata.get("title"),
                "title_localized": metadata.get("title_localized"),
            },
            "sentence_patterns": [
                _compact_line(item, index)
                for index, item in enumerate(course_content.get("sentence_patterns") or [], start=1)
                if isinstance(item, dict)
            ],
            "example_sentences": [
                _compact_line(item, index)
                for index, item in enumerate(course_content.get("example_sentences") or [], start=1)
                if isinstance(item, dict)
            ],
            "dialogue": {
                "title": (dialogue.get("title") or "").strip(),
                "title_localized": (dialogue.get("title_localized") or "").strip(),
                "lines": [
                    _compact_line(item, index)
                    for index, item in enumerate(dialogue.get("lines") or [], start=1)
                    if isinstance(item, dict)
                ],
            },
            "core_vocabulary": [
                _compact_vocab(item, index)
                for index, item in enumerate(core_vocabulary, start=1)
                if isinstance(item, dict)
            ],
            "supplementary_vocabulary": [
                _compact_vocab(item, index)
                for index, item in enumerate(supplementary_vocabulary, start=1)
                if isinstance(item, dict)
            ],
            "display_only_vocabulary": [
                _compact_vocab(item, index)
                for index, item in enumerate(display_only, start=1)
                if isinstance(item, dict)
            ],
            "grammar_sections": [
                _compact_grammar(section, index)
                for index, section in enumerate(grammar_sections, start=1)
                if isinstance(section, dict)
            ],
            "teaching_materials": teaching_materials if isinstance(teaching_materials, dict) else {},
        }

    def _build_prompt(self, metadata: dict, course_content: dict, teaching_materials: dict | None) -> str:
        context = self._build_context(metadata, course_content, teaching_materials)
        return f"""
你是一位给中文母语者讲《大家的日本语》的日语老师，同时也是教学视频导演。
请根据下面的结构化课程内容，生成一套【教学讲解脚本】，后续会由代码把它渲染成黑板风格 slide deck。
只输出合法 JSON，不要输出 Markdown。

课程内容：
{json.dumps(context, ensure_ascii=False)}

核心目标：
1. 你负责决定这一课应该拆成哪些讲解页面、每页讲什么、旁白怎么说，但同一份课程内容每次生成的页面结构必须尽量稳定。
2. 页面结构要服务初学者：文型先建立框架，例文和会话要帮助学生听懂真实句子，词汇和语法不要机械罗列。
3. 按教材顺序组织。允许把相近内容合并成一页，也允许把复杂内容拆成多页，但不要因为措辞变化随机改变页数。
4. 讲解语言是中文；日语词句保留日文原文。
5. 旁白要自然、具体、适合 TTS 朗读，不要写成提纲。
6. 开头必须落在第一个文型或第一句课文讲解上。可以有一句自然的开场，例如“我们来看第 X 课的第一个句型”，但不要单独生成“学习目标 / 本课目标 / 课程概览 / 欢迎页”。
7. 不要把已经在前课反复讲过的基础件重新详细讲一遍。像 [ja:は] 读作 [ja:わ]、[ja:です] 表示礼貌肯定、句末 [ja:か] 表示疑问，只在本课第一次真正需要时用一句话提醒；后续不要反复解释。
8. 讲解要有一点课堂连续感，但不要硬凑承上启下。只有当前页和上一页、课文场景、练习用途之间存在真实联系时，才自然点出来。
9. 词汇页不要只逐词翻译。可以自由选择讲读音、词义、用法、场景、词与词之间的关系；如果这一组词没有明显关系，就按课堂节奏自然带读和解释即可。
10. 讲解深度要像真实课堂，而不是词典释义。每页至少补充 1-2 个有教学价值的点：为什么这样说、中文母语者容易误解哪里、在什么场景使用、和刚学过的表达有什么轻微差别、或者如何放回课文会话里理解。
11. 详细不等于堆字。不要重复解释已经讲过的基础件；优先增加“具体用法”和“学习提醒”，而不是拉长开场白。

稳定页面配方：
1. sentence_patterns：每个文型必须生成 1 个 line_walkthrough，按原顺序，不要合并。
2. grammar_sections：必须覆盖每个语法点。可以把高度相近的连续语法点合并到同一页，但不要省略独立语法点。
3. example_sentences：必须覆盖教材例文里的主要问答和独立句。每页通常 2-3 句，最多 4 句，按教材顺序分组；只有完全重复的机械替换句才可以合并讲。
4. dialogue：必须按教材顺序覆盖完整会话。每页通常 2-3 句，最多 4 句；如果一段自然表达必须四句才完整，例如自我介绍套句，可以放 4 句，但不能只挑代表句。
5. core_vocabulary：主线词汇必须讲。每页 2-4 个词，优先按课文场景、语义、词性或表达功能分组，覆盖全部 core_vocabulary。
6. supplementary_vocabulary：补充词汇也必须讲。每页 2-4 个词，优先按练习场景、词性或表达功能分组，覆盖全部 supplementary_vocabulary。
7. display_only_vocabulary：专名/临时名词可以简单过一遍，重点是让学生在课文里认得，不要当作复习重点。
8. recap：最后固定 1 页。
9. 页数由内容量决定。不要为了压到固定页数而牺牲覆盖；同一课重复生成时页面结构仍需稳定。

可用 segment_type 和 source.kind：
- line_walkthrough：聚焦一句或一个文型。source.kind 可为 sentence_patterns / example_sentences / dialogue。
- sentence_focus：一页通常放 2-3 个例句，最多 4 个。source.kind 通常为 example_sentences。
- dialogue_focus：一页通常放 2-3 句会话，最多 4 句。source.kind 为 dialogue。
- vocabulary_focus：一页放 2-4 个词。source.kind 可为 core_vocabulary / supplementary_vocabulary / display_only_vocabulary。
- grammar_focus：讲一个语法点。source.kind 为 grammar_sections。
- recap：课程最后总结。source.kind 写 lesson_summary，indexes 写 []。

输出约束：
1. 每个 segment 必须包含 segment_type、source、segment_title、teaching_goal、narration、estimated_duration_seconds。
2. source 使用 1-based index，例如 {{"kind": "example_sentences", "indexes": [1, 2, 3]}}。
3. narration 只放 subtitle_zh 一个字段，写完整中文讲解段落。
4. narration 里需要让 TTS 正确读日语时，用 [ja:日本語] 标记核心日语词或短句。
   示例：这里的 [ja:は] 作主题助词时读作“わ”。不要每个日语词都标，只标学生需要听到的重点。
5. line_walkthrough 的旁白建议 5-7 句；sentence/dialogue stack 建议 4-6 句；vocabulary_focus 建议 4-6 句；grammar_focus 建议 6-8 句。
   - line_walkthrough：除了读句子和翻译，至少说明一个结构点和一个使用/误区提醒。
   - sentence_focus/dialogue_focus：不要只翻译句子，要说明问答关系、主语省略、礼貌程度、回答方式或场景推进中的至少一个。
   - vocabulary_focus：不要只列“读作/意思是”；至少挑 1-2 个词讲清用法、搭配、礼貌感、同组关系或课文场景。
   - grammar_focus：用“结构 → 例句 → 使用条件/注意点”的顺序讲，避免只复述 grammar_sections.explanation。
6. 不要输出 visual_blocks，视觉结构由 composer 根据 source 自动生成。
7. 不要直接生成 practice 或 quiz。
8. 如果某个 source index 不确定，宁可少引用，不要编不存在的 index。
9. 最后必须包含 1 个 recap segment，用来做课末总结，不要省略。
10. recap segment 必须包含 highlight_words，列出本课 4-6 个最值得回顾的内容。优先选核心句型/固定表达，其次选重要词汇或助词。
    每条格式：{{"word": "日语词句", "reading": "かな读音", "translation": "中文释义"}}。
    注意：日语课程 JSON 禁止使用 pinyin 字段，假名读音一律写 reading。
11. 不要把 supplementary_vocabulary 当作可选内容；它和 core_vocabulary 一样需要进入讲解页。
12. display_only_vocabulary 的讲解可以短，但不能和 core/supplementary 混为一类。
13. 禁止输出不绑定具体教材内容的 opening / objective / overview segment。第一个 segment 必须引用真实 source item。
14. 降低重复讲解：同一课里同一个基础语法提醒最多详细说一次；跨课复现时只说“这里沿用上一课的用法”或直接略过。
15. vocabulary_focus 的 narration 要像老师在带词：不要套用同一句“接下来是……这些词……”；如果词之间有自然关系，可以讲出来；没有关系时也可以只做清楚、具体的逐词讲解。
16. 不要生成空泛句子，例如“这个语法点也需要讲清楚”“这些例文也需要过一遍”。如果某页只有补充性质，也必须点出具体日语、具体意思和具体学习提醒。
17. 旁白里明确讲到的日语句子，必须全部包含在 source.indexes 对应的视觉卡片里；不要让旁白讲第四句但 source 或画面只包含前三句。
18. 如果 example_sentences 或 dialogue 一组超过 4 句，必须拆成多个 segment。每个 segment 的 source.indexes 最多 4 个，旁白也只讲该 segment 画面上的句子。

输出格式：
{{
  "global_config": {{
    "teaching_style": "中文讲解，初学者友好，先读音再意义再结构",
    "target_audience": "Chinese speakers learning beginner Japanese",
    "presenter_mode": "voice_over"
  }},
  "segments": [
    {{
      "segment_type": "line_walkthrough",
      "source": {{"kind": "sentence_patterns", "indexes": [1]}},
      "segment_title": "文型 1",
      "teaching_goal": "建立 N1 は N2 です 的判断句框架。",
      "narration": {{"subtitle_zh": "先看本课最基础的判断句。..."}},
      "estimated_duration_seconds": 18
    }},
    {{
      "segment_type": "recap",
      "source": {{"kind": "lesson_summary", "indexes": []}},
      "segment_title": "本课总结",
      "teaching_goal": "回顾本课最重要的句型、助词和固定表达。",
      "highlight_words": [
        {{"word": "わたしは学生です", "reading": "わたしはがくせいです", "translation": "我是学生"}}
      ],
      "narration": {{"subtitle_zh": "最后我们快速回顾一下本课重点。..."}},
      "estimated_duration_seconds": 24
    }}
  ]
}}
"""

    def run(self, metadata: dict, course_content: dict, teaching_materials: dict | None = None) -> dict:
        prompt = self._build_prompt(metadata, course_content, teaching_materials)
        result = self.llm.generate_structured_json(prompt, file_path=None, file_obj=None)
        if not isinstance(result, dict):
            return {"global_config": {}, "segments": []}
        return _replace_old_pinyin_keys(result)
