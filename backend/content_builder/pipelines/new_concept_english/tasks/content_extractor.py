from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

try:
    from content_builder.core.llm_providers import BaseLLMProvider
    from content_builder.pipelines.new_concept_english.book_profiles import book1
except ImportError:
    from core.llm_providers import BaseLLMProvider
    from pipelines.new_concept_english.book_profiles import book1


def _tokens(text: str, highlights: set[str] | None = None) -> list[dict]:
    highlights = highlights or set()
    pieces = []
    buffer = ""
    for char in text:
        if char.isalnum() or char == "'":
            buffer += char
            continue
        if buffer:
            pieces.append(buffer)
            buffer = ""
        if char.strip():
            pieces.append(char)
    if buffer:
        pieces.append(buffer)

    return [
        {"text": piece, "highlight": piece.lower() in highlights}
        for piece in pieces
    ]


def _term_set(vocabulary: list[dict]) -> set[str]:
    return {
        (item.get("term") or "").strip().lower()
        for item in vocabulary or []
        if isinstance(item, dict) and (item.get("term") or "").strip()
    }


def _normalize_tokens(lines: list[dict], vocabulary: list[dict]) -> list[dict]:
    highlights = _term_set(vocabulary)
    normalized = []
    for index, line in enumerate(lines or [], start=1):
        if not isinstance(line, dict):
            continue
        text = (line.get("text") or "").strip()
        if not text:
            continue
        item = {
            "line_ref": int(line.get("line_ref") or index),
            "speaker": (line.get("speaker") or line.get("role") or "Speaker").strip(),
            "text": text,
            "translation": (line.get("translation") or "").strip(),
            "tokens": _tokens(text, highlights),
        }
        normalized.append(item)
    return normalized


def _normalize_vocabulary(items: list[dict], source_lessons: tuple[int, int]) -> list[dict]:
    normalized = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        term = (item.get("term") or item.get("word") or item.get("text") or "").strip()
        if not term:
            continue
        try:
            source_lesson = int(item.get("source_lesson") or source_lessons[0])
        except (TypeError, ValueError):
            source_lesson = source_lessons[0]
        role = (item.get("role") or "").strip()
        if not role:
            role = "pattern_slot" if source_lesson == source_lessons[1] else "dialogue_word"
        normalized.append({
            "term": term,
            "pronunciation": (item.get("pronunciation") or item.get("ipa") or "").strip(),
            "part_of_speech": (item.get("part_of_speech") or "").strip(),
            "translation": (item.get("translation") or item.get("definition") or "").strip(),
            "source_lesson": source_lesson,
            "role": role,
            **({"image_index": item.get("image_index")} if item.get("image_index") is not None else {}),
            **({"example_sentence": item.get("example_sentence")} if isinstance(item.get("example_sentence"), dict) else {}),
        })
    return normalized


def _build_default_explanation_plan(anchor: dict, pattern_drills: list[dict], vocabulary: list[dict]) -> dict:
    anchor_title = (anchor.get("title") or "").strip()
    first_line = ""
    lines = anchor.get("lines") if isinstance(anchor.get("lines"), list) else []
    if lines:
        first_line = (lines[0].get("text") or "").strip()
    pattern = ""
    slots = []
    if pattern_drills:
        pattern = (pattern_drills[0].get("pattern") or "").strip()
        slots = pattern_drills[0].get("slots") if isinstance(pattern_drills[0].get("slots"), list) else []
    vocab_terms = [v.get("term", "") for v in vocabulary if isinstance(v, dict)]
    slot_terms = [s.get("text", "") for s in slots if isinstance(s, dict)] or vocab_terms[:6]

    return {
        "target_audience": "Chinese speakers learning English",
        "segments": [
            {
                "segment_id": 1,
                "segment_type": "scene_setup",
                "title": "场景导入",
                "goal": "建立本课对话场景和交际目标。",
                "on_screen": {"focus_text": first_line or anchor_title, "translation": ""},
            },
            {
                "segment_id": 2,
                "segment_type": "line_walkthrough",
                "title": "课文讲解",
                "goal": "理解核心课文/对话。",
                "source_line_refs": [line.get("line_ref") for line in lines if isinstance(line, dict)],
                "on_screen": {"focus_text": anchor_title, "translation": ""},
            },
            {
                "segment_id": 3,
                "segment_type": "pattern_focus",
                "title": "句型讲解",
                "goal": "掌握可替换的核心句型。",
                "on_screen": {"focus_text": pattern, "translation": ""},
            },
            {
                "segment_id": 4,
                "segment_type": "vocabulary_focus",
                "title": "替换词汇",
                "goal": "把词汇放进句型练习。",
                "on_screen": {"focus_text": " / ".join(slot_terms[:6]), "translation": ""},
            },
            {
                "segment_id": 5,
                "segment_type": "guided_practice",
                "title": "跟读操练",
                "goal": "看图替换并说出完整句子。",
                "on_screen": {"focus_text": pattern, "translation": ""},
            },
        ],
    }


def _build_default_practice_items(anchor: dict, pattern_drills: list[dict]) -> list[dict]:
    items = []
    question_id = 1
    if pattern_drills:
        drill = pattern_drills[0]
        pattern = (drill.get("pattern") or "").strip()
        for slot in (drill.get("slots") or [])[:8]:
            if not isinstance(slot, dict):
                continue
            text = (slot.get("text") or "").strip()
            translation = (slot.get("translation") or "").strip()
            if not text:
                continue
            answer = pattern.replace("{item}", text) if "{item}" in pattern else f"{pattern} {text}".strip()
            items.append({
                "question_id": question_id,
                "question_type": "PATTERN_DRILL",
                "prompt": f"请用本课句型表达：{translation}",
                "standard_answers": [answer],
                "context": {"pattern": pattern, "slot": text},
            })
            question_id += 1

    for line in (anchor.get("lines") or [])[:8]:
        if not isinstance(line, dict):
            continue
        text = (line.get("text") or "").strip()
        translation = (line.get("translation") or "").strip()
        if not text or not translation:
            continue
        items.append({
            "question_id": question_id,
            "question_type": "TARGET_TO_SUPPORT",
            "prompt": text,
            "standard_answers": [translation],
            "context": {"line_ref": line.get("line_ref")},
        })
        question_id += 1

    return items


def _normalize_pattern_drills(drills: list[dict], fallback_vocabulary: list[dict], source_lesson: int) -> list[dict]:
    normalized = []
    for drill in drills or []:
        if not isinstance(drill, dict):
            continue
        pattern = (drill.get("pattern") or "").strip().replace("{slot}", "{item}").replace("{word}", "{item}")
        slots = []
        for index, slot in enumerate(drill.get("slots") or [], start=1):
            if not isinstance(slot, dict):
                continue
            text = (slot.get("text") or slot.get("term") or slot.get("word") or "").strip()
            if not text:
                continue
            slots.append({
                "text": text,
                "pronunciation": (slot.get("pronunciation") or slot.get("ipa") or "").strip(),
                "translation": (slot.get("translation") or "").strip(),
                **({"image_index": slot.get("image_index")} if slot.get("image_index") is not None else {"image_index": index}),
            })
        if not slots:
            slots = [
                {
                    "text": item.get("term", ""),
                    "pronunciation": item.get("pronunciation", ""),
                    "translation": item.get("translation", ""),
                    **({"image_index": item.get("image_index")} if item.get("image_index") is not None else {}),
                }
                for item in fallback_vocabulary
                if item.get("term")
            ]
        generated_prompts = drill.get("generated_prompts") if isinstance(drill.get("generated_prompts"), list) else []
        if not generated_prompts and pattern:
            generated_prompts = [
                {
                    "text": pattern.replace("{item}", slot["text"]),
                    "translation": "",
                    **({"image_index": slot.get("image_index")} if slot.get("image_index") is not None else {}),
                }
                for slot in slots
            ]
        normalized.append({
            "source_lesson": int(drill.get("source_lesson") or source_lesson),
            "pattern": pattern,
            "translation_pattern": (drill.get("translation_pattern") or "").strip(),
            "response_patterns": drill.get("response_patterns") if isinstance(drill.get("response_patterns"), list) else [],
            "slots": slots,
            "generated_prompts": generated_prompts,
        })
    return normalized


class NewConceptEnglishExtractor:
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider

    def _build_prompt(self, lesson_slice: book1.AppLessonSlice, support_language: str) -> str:
        source_odd, source_even = lesson_slice.source_lessons
        lesson_slug = lesson_slice.lesson_slug
        context = {
            "book": 1,
            "lesson_id": lesson_slug,
            "source_lessons": list(lesson_slice.source_lessons),
            "pdf_pages": list(lesson_slice.pdf_pages),
            "target_language": "en",
            "support_language": support_language,
        }
        return f"""
        你是一名教材解析工程师。请解析提供的 New Concept English 第一册 4 页 PDF，
        并生成干净的 schema v2 JSON。只输出合法 JSON，不要包含 Markdown。

        输入上下文：
        {json.dumps(context, ensure_ascii=False)}

        页面结构固定：
        - 前 2 页是原教材 Lesson {source_odd}：核心课文/对话、New words and expressions、Notes on the text、参考译文。
        - 后 2 页是原教材 Lesson {source_even}：替换练习/图片操练、New words and expressions、Written exercise。

        解析目标：
        1. app lesson slug 固定为 "{lesson_slug}"，由原教材 Lesson {source_odd}+{source_even} 组成。
        2. target_language 是英文 en，support_language 是中文 zh。
        3. 不要使用 cn、py、pinyin 这类中文课程字段。英文原文统一用 text/term/tokens.text，中文解释统一放 translation。
        4. Lesson {source_odd} 作为 anchor。若它是对话，anchor.type="dialogue"；若是短文，anchor.type="passage"。
        5. anchor.lines 必须按原文顺序提取英语课文。每行包含 line_ref、speaker、text、translation、tokens。
           - 如果教材有角色名，speaker 用教材角色名；如果没有角色名，对话可用 Speaker A / Speaker B 交替；短文用 Narrator。
           - translation 优先用教材参考译文；没有时请翻译为自然简体中文。
           - tokens 数组只包含 text 和 highlight。
        6. vocabulary 必须同时包含 Lesson {source_odd} 和 Lesson {source_even} 的 New words and expressions。
           字段：term、pronunciation、part_of_speech、translation、source_lesson、role、example_sentence。
           - Lesson {source_odd} 的词 role="dialogue_word"。
           - Lesson {source_even} 的词 role="pattern_slot"。
        7. pattern_drills 根据 Lesson {source_even} 的标题、图片和词汇表生成。
           至少包含 pattern、translation_pattern、slots、generated_prompts。
           slots 每项包含 text、pronunciation、translation、image_index（如果可见）。
        8. teaching_materials 提取 Notes on the text 和核心语法/句型，不要泛泛而谈。
        9. explanation_plan.segments 固定按这个教学顺序生成 5 段：
           scene_setup, line_walkthrough, pattern_focus, vocabulary_focus, guided_practice。
           这 5 段要服务于后续课文讲解视频。
        10. practice_items 生成少量题目即可，题型只允许：
            PATTERN_DRILL, TARGET_TO_SUPPORT, TARGET_LISTEN_WRITE, TARGET_SPEAK。
        11. 严禁提取目录、页眉页脚、页码、图片编号以外的噪声。

        强制输出结构：
        {{
          "schema_version": "2.0",
          "pipeline_id": "new_concept_english",
          "target_language": "en",
          "support_language": "{support_language}",
          "lesson_metadata": {{
            "course_id": {book1.COURSE_ID},
            "course_slug": "{book1.COURSE_SLUG}",
            "lesson_id": {lesson_slice.app_lesson_index},
            "lesson_slug": "{lesson_slug}",
            "title": "English title",
            "title_localized": "中文标题",
            "content_type": "dialogue_pattern",
            "source": {{
              "textbook": "New Concept English",
              "book": 1,
              "source_lessons": [{source_odd}, {source_even}],
              "pdf_pages": {list(lesson_slice.pdf_pages)}
            }}
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
                  "translation": "中文翻译",
                  "tokens": [{{"text": "English", "highlight": true}}]
                }}
              ]
            }},
            "vocabulary": [],
            "pattern_drills": [],
            "writing_exercises": []
          }},
          "teaching_materials": {{
            "lesson_flow": [],
            "notes_on_text": [],
            "grammar_sections": []
          }},
          "explanation_plan": {{"target_audience": "Chinese speakers learning English", "segments": []}},
          "practice_items": []
        }}
        """

    def run(
        self,
        lesson_pdf: Path,
        source_pdf: Path,
        app_lesson_index: int,
        support_language: str = "zh",
    ) -> dict:
        lesson_slice = book1.app_lesson_slice(app_lesson_index)
        prompt = self._build_prompt(lesson_slice, support_language)
        result = self.llm.generate_structured_json(prompt, file_path=str(lesson_pdf))
        return normalize_lesson_data(
            result,
            lesson_slice=lesson_slice,
            source_pdf=source_pdf,
            lesson_pdf=lesson_pdf,
            support_language=support_language,
        )


def normalize_lesson_data(
    data: dict,
    lesson_slice: book1.AppLessonSlice,
    source_pdf: Path,
    lesson_pdf: Path,
    support_language: str = "zh",
    course_id: int | str = book1.COURSE_ID,
) -> dict:
    data = data if isinstance(data, dict) else {}
    metadata = data.get("lesson_metadata") if isinstance(data.get("lesson_metadata"), dict) else {}
    course_content = data.get("course_content") if isinstance(data.get("course_content"), dict) else {}
    anchor = course_content.get("anchor") if isinstance(course_content.get("anchor"), dict) else {}
    vocabulary = _normalize_vocabulary(
        course_content.get("vocabulary") if isinstance(course_content.get("vocabulary"), list) else [],
        lesson_slice.source_lessons,
    )
    anchor["lines"] = _normalize_tokens(
        anchor.get("lines") if isinstance(anchor.get("lines"), list) else [],
        vocabulary,
    )
    anchor["type"] = (anchor.get("type") or "dialogue").strip()
    anchor["source_lesson"] = int(anchor.get("source_lesson") or lesson_slice.source_lessons[0])
    anchor["title"] = (anchor.get("title") or metadata.get("title") or lesson_slice.lesson_slug).strip()
    if not isinstance(anchor.get("listening_question"), dict):
        anchor["listening_question"] = {"text": "", "translation": "", "answer": ""}

    raw_pattern_drills = course_content.get("pattern_drills") if isinstance(course_content.get("pattern_drills"), list) else []
    pattern_drills = _normalize_pattern_drills(
        raw_pattern_drills,
        fallback_vocabulary=[
            item for item in vocabulary if item.get("source_lesson") == lesson_slice.source_lessons[1]
        ],
        source_lesson=lesson_slice.source_lessons[1],
    )
    if not pattern_drills:
        even_vocab = [item for item in vocabulary if item.get("source_lesson") == lesson_slice.source_lessons[1]]
        if even_vocab:
            pattern_drills = [{
                "source_lesson": lesson_slice.source_lessons[1],
                "pattern": "",
                "translation_pattern": "",
                "slots": [
                    {
                        "text": item.get("term", ""),
                        "pronunciation": item.get("pronunciation", ""),
                        "translation": item.get("translation", ""),
                        **({"image_index": item.get("image_index")} if item.get("image_index") is not None else {}),
                    }
                    for item in even_vocab
                ],
                "generated_prompts": [],
            }]

    teaching_materials = data.get("teaching_materials") if isinstance(data.get("teaching_materials"), dict) else {}
    explanation_plan = data.get("explanation_plan") if isinstance(data.get("explanation_plan"), dict) else {}
    if not isinstance(explanation_plan.get("segments"), list) or not explanation_plan.get("segments"):
        explanation_plan = _build_default_explanation_plan(anchor, pattern_drills, vocabulary)

    practice_items = data.get("practice_items") if isinstance(data.get("practice_items"), list) else []
    if not practice_items:
        practice_items = _build_default_practice_items(anchor, pattern_drills)

    return {
        "schema_version": "2.0",
        "pipeline_id": "new_concept_english",
        "target_language": "en",
        "support_language": support_language,
        "lesson_metadata": {
            "course_id": int(course_id) if str(course_id).isdigit() else course_id,
            "course_slug": book1.COURSE_SLUG,
            "lesson_id": lesson_slice.app_lesson_index,
            "lesson_slug": lesson_slice.lesson_slug,
            "title": (metadata.get("title") or anchor.get("title") or lesson_slice.lesson_slug).strip(),
            "title_localized": (metadata.get("title_localized") or "").strip(),
            "content_type": (metadata.get("content_type") or "dialogue_pattern").strip(),
            "source": {
                "textbook": "New Concept English",
                "book": 1,
                "source_lessons": list(lesson_slice.source_lessons),
                "source_pdf": str(source_pdf),
                "lesson_pdf": str(lesson_pdf),
                "pdf_pages": list(lesson_slice.pdf_pages),
            },
        },
        "course_content": {
            "anchor": anchor,
            "vocabulary": vocabulary,
            "pattern_drills": pattern_drills,
            "writing_exercises": course_content.get("writing_exercises") if isinstance(course_content.get("writing_exercises"), list) else [],
        },
        "teaching_materials": {
            "lesson_flow": teaching_materials.get("lesson_flow") if isinstance(teaching_materials.get("lesson_flow"), list) else [],
            "notes_on_text": teaching_materials.get("notes_on_text") if isinstance(teaching_materials.get("notes_on_text"), list) else [],
            "grammar_sections": teaching_materials.get("grammar_sections") if isinstance(teaching_materials.get("grammar_sections"), list) else [],
        },
        "explanation_plan": explanation_plan,
        "practice_items": practice_items,
    }


def build_lesson001_data(
    source_pdf: Path,
    lesson_pdf: Path,
    course_id: int | str = book1.COURSE_ID,
) -> dict:
    lesson_slice = book1.app_lesson_slice(1)
    highlights = {
        "excuse",
        "me",
        "yes",
        "is",
        "this",
        "your",
        "handbag",
        "pardon",
        "it",
        "thank",
        "you",
    }

    dialogue_lines = [
        {
            "line_ref": 1,
            "speaker": "Man",
            "text": "Excuse me!",
            "translation": "对不起。",
            "tokens": _tokens("Excuse me!", highlights),
        },
        {
            "line_ref": 2,
            "speaker": "Woman",
            "text": "Yes?",
            "translation": "什么事？",
            "tokens": _tokens("Yes?", highlights),
        },
        {
            "line_ref": 3,
            "speaker": "Man",
            "text": "Is this your handbag?",
            "translation": "这是您的手提包吗？",
            "tokens": _tokens("Is this your handbag?", highlights),
        },
        {
            "line_ref": 4,
            "speaker": "Woman",
            "text": "Pardon?",
            "translation": "对不起，请再说一遍。",
            "tokens": _tokens("Pardon?", highlights),
        },
        {
            "line_ref": 5,
            "speaker": "Man",
            "text": "Is this your handbag?",
            "translation": "这是您的手提包吗？",
            "tokens": _tokens("Is this your handbag?", highlights),
        },
        {
            "line_ref": 6,
            "speaker": "Woman",
            "text": "Yes, it is.",
            "translation": "是的，是我的。",
            "tokens": _tokens("Yes, it is.", highlights),
        },
        {
            "line_ref": 7,
            "speaker": "Woman",
            "text": "Thank you very much.",
            "translation": "非常感谢！",
            "tokens": _tokens("Thank you very much.", highlights),
        },
    ]

    lesson1_vocabulary = [
        {
            "term": "excuse",
            "pronunciation": "/ɪkˈskjuːz/",
            "part_of_speech": "verb",
            "translation": "原谅",
            "source_lesson": 1,
            "role": "dialogue_word",
            "example_sentence": {
                "text": "Excuse me!",
                "translation": "对不起。",
                "line_ref": 1,
            },
        },
        {
            "term": "me",
            "pronunciation": "/miː/",
            "part_of_speech": "pronoun",
            "translation": "我（宾格）",
            "source_lesson": 1,
            "role": "dialogue_word",
            "example_sentence": {
                "text": "Excuse me!",
                "translation": "对不起。",
                "line_ref": 1,
            },
        },
        {
            "term": "yes",
            "pronunciation": "/jes/",
            "part_of_speech": "adverb",
            "translation": "是的",
            "source_lesson": 1,
            "role": "dialogue_word",
            "example_sentence": {
                "text": "Yes?",
                "translation": "什么事？",
                "line_ref": 2,
            },
        },
        {
            "term": "is",
            "pronunciation": "/ɪz/",
            "part_of_speech": "verb",
            "translation": "be 动词现在时第三人称单数",
            "source_lesson": 1,
            "role": "dialogue_word",
            "example_sentence": {
                "text": "Is this your handbag?",
                "translation": "这是您的手提包吗？",
                "line_ref": 3,
            },
        },
        {
            "term": "this",
            "pronunciation": "/ðɪs/",
            "part_of_speech": "pronoun",
            "translation": "这",
            "source_lesson": 1,
            "role": "dialogue_word",
            "example_sentence": {
                "text": "Is this your handbag?",
                "translation": "这是您的手提包吗？",
                "line_ref": 3,
            },
        },
        {
            "term": "your",
            "pronunciation": "/jɔː/",
            "part_of_speech": "possessive adjective",
            "translation": "你的，你们的",
            "source_lesson": 1,
            "role": "dialogue_word",
            "example_sentence": {
                "text": "Is this your handbag?",
                "translation": "这是您的手提包吗？",
                "line_ref": 3,
            },
        },
        {
            "term": "handbag",
            "pronunciation": "/ˈhændbæg/",
            "part_of_speech": "noun",
            "translation": "（女用）手提包",
            "source_lesson": 1,
            "role": "dialogue_word",
            "example_sentence": {
                "text": "Is this your handbag?",
                "translation": "这是您的手提包吗？",
                "line_ref": 3,
            },
        },
        {
            "term": "pardon",
            "pronunciation": "/ˈpɑːdn/",
            "part_of_speech": "interjection",
            "translation": "原谅，请再说一遍",
            "source_lesson": 1,
            "role": "dialogue_word",
            "example_sentence": {
                "text": "Pardon?",
                "translation": "对不起，请再说一遍。",
                "line_ref": 4,
            },
        },
        {
            "term": "it",
            "pronunciation": "/ɪt/",
            "part_of_speech": "pronoun",
            "translation": "它",
            "source_lesson": 1,
            "role": "dialogue_word",
            "example_sentence": {
                "text": "Yes, it is.",
                "translation": "是的，是我的。",
                "line_ref": 6,
            },
        },
        {
            "term": "thank you",
            "pronunciation": "/θæŋk juː/",
            "part_of_speech": "phrase",
            "translation": "感谢你（们）",
            "source_lesson": 1,
            "role": "dialogue_word",
            "example_sentence": {
                "text": "Thank you very much.",
                "translation": "非常感谢！",
                "line_ref": 7,
            },
        },
        {
            "term": "very much",
            "pronunciation": "/ˈveri mʌtʃ/",
            "part_of_speech": "adverbial phrase",
            "translation": "非常地",
            "source_lesson": 1,
            "role": "dialogue_word",
            "example_sentence": {
                "text": "Thank you very much.",
                "translation": "非常感谢！",
                "line_ref": 7,
            },
        },
    ]

    lesson2_slots = [
        {"text": "pen", "pronunciation": "/pen/", "translation": "钢笔", "image_index": 1},
        {"text": "pencil", "pronunciation": "/ˈpensəl/", "translation": "铅笔", "image_index": 2},
        {"text": "book", "pronunciation": "/bʊk/", "translation": "书", "image_index": 3},
        {"text": "watch", "pronunciation": "/wɒtʃ/", "translation": "手表", "image_index": 4},
        {"text": "coat", "pronunciation": "/kəʊt/", "translation": "上衣，外衣", "image_index": 5},
        {"text": "dress", "pronunciation": "/dres/", "translation": "连衣裙", "image_index": 6},
        {"text": "skirt", "pronunciation": "/skɜːt/", "translation": "裙子", "image_index": 7},
        {"text": "shirt", "pronunciation": "/ʃɜːt/", "translation": "衬衣", "image_index": 8},
        {"text": "car", "pronunciation": "/kɑː/", "translation": "小汽车", "image_index": 9},
        {"text": "house", "pronunciation": "/haʊs/", "translation": "房子", "image_index": 10},
    ]

    lesson2_vocabulary = [
        {
            "term": slot["text"],
            "pronunciation": slot["pronunciation"],
            "part_of_speech": "noun",
            "translation": slot["translation"],
            "source_lesson": 2,
            "role": "pattern_slot",
            "image_index": slot["image_index"],
            "example_sentence": {
                "text": f"Is this your {slot['text']}?",
                "translation": f"这是你的{slot['translation'].split('，')[0]}吗？",
            },
        }
        for slot in lesson2_slots
    ]

    pattern_drill = {
        "source_lesson": 2,
        "pattern": "Is this your {item}?",
        "translation_pattern": "这是你的{item}吗？",
        "response_patterns": [
            {"text": "Yes, it is.", "translation": "是的，是我的。"},
            {"text": "No, it isn't.", "translation": "不，不是。"},
        ],
        "slots": deepcopy(lesson2_slots),
        "generated_prompts": [
            {
                "text": f"Is this your {slot['text']}?",
                "translation": f"这是你的{slot['translation'].split('，')[0]}吗？",
                "image_index": slot["image_index"],
            }
            for slot in lesson2_slots
        ],
    }

    teaching_segments = [
        {
            "segment_id": 1,
            "segment_type": "scene_setup",
            "title": "礼貌开口",
            "goal": "理解捡到物品时如何礼貌地引起对方注意。",
            "on_screen": {
                "focus_text": "Excuse me!",
                "translation": "对不起。/ 打扰一下。",
            },
            "narration_zh": "这一课的场景很简单：有人捡到一个手提包，想礼貌地询问是不是对方的。英语里先用 Excuse me 来引起注意，比直接问问题更自然。",
        },
        {
            "segment_id": 2,
            "segment_type": "line_walkthrough",
            "title": "核心对话",
            "goal": "逐句理解 Lesson 1 的短对话。",
            "source_line_refs": [1, 2, 3, 4, 5, 6, 7],
            "on_screen": {
                "focus_text": "Is this your handbag?",
                "translation": "这是您的手提包吗？",
            },
            "narration_zh": "对话的核心句是 Is this your handbag? Is this 是询问眼前这个东西是不是某物，your 表示你的，handbag 是手提包。",
        },
        {
            "segment_id": 3,
            "segment_type": "pattern_focus",
            "title": "Is this your + 物品?",
            "goal": "掌握可替换句型。",
            "on_screen": {
                "focus_text": "Is this your {item}?",
                "translation": "这是你的……吗？",
            },
            "narration_zh": "Lesson 2 把 handbag 换成不同物品。只要保留 Is this your，再替换后面的名词，就能问很多类似的问题。",
        },
        {
            "segment_id": 4,
            "segment_type": "vocabulary_focus",
            "title": "替换词汇",
            "goal": "把 Lesson 2 的物品词汇带入句型。",
            "on_screen": {
                "focus_text": "pen / pencil / book / watch / coat",
                "translation": "钢笔 / 铅笔 / 书 / 手表 / 外衣",
            },
            "narration_zh": "先练最常见的物品词：pen、pencil、book、watch、coat。每个词都可以放进 Is this your 后面。",
        },
        {
            "segment_id": 5,
            "segment_type": "guided_practice",
            "title": "跟读操练",
            "goal": "看图替换并跟读句子。",
            "on_screen": {
                "focus_text": "Is this your pen? / Is this your book?",
                "translation": "这是你的钢笔吗？/ 这是你的书吗？",
            },
            "narration_zh": "跟读时注意 this your 之间自然连起来，不要一个词一个词地停顿。先读 Is this your pen? 再换成 Is this your book?",
        },
    ]

    practice_items = []
    question_id = 1
    for slot in lesson2_slots[:6]:
        practice_items.append({
            "question_id": question_id,
            "question_type": "PATTERN_DRILL",
            "prompt": f"这是你的{slot['translation'].split('，')[0]}吗？",
            "standard_answers": [f"Is this your {slot['text']}?"],
            "context": {"pattern": "Is this your {item}?", "slot": slot["text"]},
        })
        question_id += 1

    for line in dialogue_lines:
        if line["line_ref"] in {1, 3, 4, 6, 7}:
            practice_items.append({
                "question_id": question_id,
                "question_type": "TARGET_TO_SUPPORT",
                "prompt": line["text"],
                "standard_answers": [line["translation"]],
                "context": {"line_ref": line["line_ref"]},
            })
            question_id += 1

    for line in dialogue_lines:
        if line["line_ref"] in {1, 3, 6, 7}:
            practice_items.append({
                "question_id": question_id,
                "question_type": "TARGET_LISTEN_WRITE",
                "prompt": "听英文，写出你听到的句子。",
                "standard_answers": [line["text"]],
                "context": {"line_ref": line["line_ref"]},
            })
            question_id += 1

    practice_items.append({
        "question_id": question_id,
        "question_type": "TARGET_SPEAK",
        "prompt": "请用英语说：这是你的手提包吗？",
        "standard_answers": ["Is this your handbag?"],
        "context": {"line_ref": 3},
        "metadata": {"answer_mode": "speech"},
    })

    return {
        "schema_version": "2.0",
        "pipeline_id": "new_concept_english",
        "target_language": "en",
        "support_language": "zh",
        "lesson_metadata": {
            "course_id": int(course_id) if str(course_id).isdigit() else course_id,
            "course_slug": book1.COURSE_SLUG,
            "lesson_id": lesson_slice.app_lesson_index,
            "lesson_slug": lesson_slice.lesson_slug,
            "title": "Excuse me!",
            "title_localized": "对不起！",
            "content_type": "dialogue_pattern",
            "source": {
                "textbook": "New Concept English",
                "book": 1,
                "source_lessons": list(lesson_slice.source_lessons),
                "source_pdf": str(source_pdf),
                "lesson_pdf": str(lesson_pdf),
                "pdf_pages": list(lesson_slice.pdf_pages),
            },
        },
        "course_content": {
            "anchor": {
                "type": "dialogue",
                "source_lesson": 1,
                "title": "Excuse me!",
                "listening_question": {
                    "text": "Whose handbag is it?",
                    "translation": "这是谁的手提包？",
                    "answer": "It is the woman's handbag.",
                },
                "lines": dialogue_lines,
            },
            "vocabulary": lesson1_vocabulary + lesson2_vocabulary,
            "pattern_drills": [pattern_drill],
            "writing_exercises": [
                {
                    "source_lesson": 2,
                    "instruction": "Copy these sentences.",
                    "translation": "抄写以下句子。",
                    "sentences": [line["text"] for line in dialogue_lines],
                }
            ],
        },
        "teaching_materials": {
            "lesson_flow": [
                "scene_setup",
                "anchor_dialogue_walkthrough",
                "pattern_focus",
                "pattern_vocabulary",
                "guided_speaking_practice",
            ],
            "notes_on_text": [
                {
                    "focus_text": "Excuse me.",
                    "translation": "对不起。/ 打扰一下。",
                    "explanation": "用于与陌生人搭话、打断别人说话或从别人身边挤过。",
                    "source_lesson": 1,
                },
                {
                    "focus_text": "Pardon?",
                    "translation": "请再说一遍。",
                    "explanation": "完整形式是 I beg your pardon，用来请求对方重复刚才说过的话。",
                    "source_lesson": 1,
                },
            ],
            "grammar_sections": [
                {
                    "title": "Is this your + noun?",
                    "explanation": "用来询问眼前某物是否属于对方。",
                    "patterns": [
                        {
                            "pattern": "Is this your {item}?",
                            "translation": "这是你的{item}吗？",
                        },
                        {
                            "pattern": "Yes, it is.",
                            "translation": "是的，是我的。",
                        },
                        {
                            "pattern": "No, it isn't.",
                            "translation": "不，不是。",
                        },
                    ],
                }
            ],
        },
        "explanation_plan": {
            "target_audience": "Chinese speakers learning English",
            "segments": teaching_segments,
        },
        "practice_items": practice_items,
    }
