from __future__ import annotations

from pathlib import Path

try:
    from content_builder.ja.minna_no_nihongo.book_profiles import book1, lesson_profile as resolve_lesson_profile
    from content_builder.ja.minna_no_nihongo.tasks.practice_generator import MinnaNoNihongoPracticeGenerator
    from content_builder.ja.minna_no_nihongo.tasks.reading_annotator import JapaneseReadingAnnotator
    from content_builder.ja.minna_no_nihongo.tasks.render_plan_builder import MinnaNoNihongoRenderPlanBuilder
    from content_builder.ja.minna_no_nihongo.tasks.teaching_flow_builder import MinnaNoNihongoTeachingFlowBuilder
except ImportError:
    from content_builder.ja.minna_no_nihongo.book_profiles import book1, lesson_profile as resolve_lesson_profile
    from content_builder.ja.minna_no_nihongo.tasks.practice_generator import MinnaNoNihongoPracticeGenerator
    from content_builder.ja.minna_no_nihongo.tasks.reading_annotator import JapaneseReadingAnnotator
    from content_builder.ja.minna_no_nihongo.tasks.render_plan_builder import MinnaNoNihongoRenderPlanBuilder
    from content_builder.ja.minna_no_nihongo.tasks.teaching_flow_builder import MinnaNoNihongoTeachingFlowBuilder


def _first_non_empty(*values) -> str:
    for value in values:
        if value is None:
            continue
        normalized = str(value).strip()
        if normalized:
            return normalized
    return ""


def _normalize_lesson_section(value: str | None, default: str = "core") -> str:
    normalized = (value or default).strip().lower()
    aliases = {
        "text": "core",
        "dialogue": "core",
        "sentence_patterns": "core",
        "example_sentences": "core",
        "vocabulary": "core",
        "practice": "supplementary",
        "drill": "supplementary",
        "exercise": "supplementary",
        "question": "supplementary",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in {"core", "supplementary"}:
        return default
    return normalized


def _normalize_part_of_speech(value: str | None) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    aliases = {
        "代": "代词",
        "代名詞": "代词",
        "代名词": "代词",
        "pronoun": "代词",
        "名": "名词",
        "名詞": "名词",
        "noun": "名词",
        "動": "动词",
        "动": "动词",
        "動詞": "动词",
        "动词": "动词",
        "verb": "动词",
        "形": "形容词",
        "形容詞": "形容词",
        "adjective": "形容词",
        "い形": "い形容词",
        "い形容詞": "い形容词",
        "い adjective": "い形容词",
        "i-adjective": "い形容词",
        "な形": "な形容词",
        "な形容詞": "な形容词",
        "な adjective": "な形容词",
        "na-adjective": "な形容词",
        "副": "副词",
        "副詞": "副词",
        "adverb": "副词",
        "助": "助词",
        "助詞": "助词",
        "particle": "助词",
        "接": "接续词",
        "接続詞": "接续词",
        "conjunction": "接续词",
        "接尾": "接尾词",
        "接尾詞": "接尾词",
        "suffix": "接尾词",
        "感": "感叹词",
        "感動詞": "感叹词",
        "感叹词": "感叹词",
        "interjection": "感叹词",
        "連語": "惯用表达",
        "连语": "惯用表达",
        "慣用表現": "惯用表达",
        "惯用表达": "惯用表达",
        "phrase": "惯用表达",
        "表現": "表达",
        "表现": "表达",
        "expression": "表达",
        "挨拶": "寒暄语",
        "寒暄": "寒暄语",
        "greeting": "寒暄语",
        "疑問詞": "疑问词",
        "疑问词": "疑问词",
        "question word": "疑问词",
        "助数": "助数词",
        "助数詞": "助数词",
        "counter": "助数词",
        "固有名詞": "专有名词",
        "固有名词": "专有名词",
        "proper noun": "专有名词",
        "person_name": "专有名词",
        "organization_name": "专有名词",
        "location_name": "专有名词",
    }
    return aliases.get(text, aliases.get(text.lower(), text))


def _compact_text(value: str | None) -> str:
    return "".join(str(value or "").split())


def _source_section_key(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    aliases = {
        "文型": "sentence_patterns",
        "sentence_pattern": "sentence_patterns",
        "sentence_patterns": "sentence_patterns",
        "patterns": "sentence_patterns",
        "例文": "example_sentences",
        "example": "example_sentences",
        "examples": "example_sentences",
        "example_sentences": "example_sentences",
        "会話": "dialogue",
        "会话": "dialogue",
        "dialogue": "dialogue",
        "dialogue_lines": "dialogue",
    }
    return aliases.get(normalized, normalized)


def _source_ref(value) -> int | None:
    try:
        ref = int(value)
    except (TypeError, ValueError):
        return None
    return ref if ref > 0 else None


def _copy_tokens(tokens: list[dict] | None) -> list[dict]:
    return [dict(token) for token in tokens or [] if isinstance(token, dict)]


def _tokens_match_text(tokens: list[dict] | None, text: str | None) -> bool:
    expected = _compact_text(text)
    if not expected:
        return True
    actual = _compact_text("".join(
        str(token.get("surface") or token.get("text") or token.get("word") or "")
        for token in tokens or []
        if isinstance(token, dict)
    ))
    return bool(actual) and actual == expected


class MinnaNoNihongoLessonNormalizer:
    def __init__(
        self,
        reading_annotator: JapaneseReadingAnnotator | None = None,
        teaching_flow_builder: MinnaNoNihongoTeachingFlowBuilder | None = None,
        practice_generator: MinnaNoNihongoPracticeGenerator | None = None,
        render_plan_builder: MinnaNoNihongoRenderPlanBuilder | None = None,
    ):
        self.reading_annotator = reading_annotator or JapaneseReadingAnnotator()
        self.teaching_flow_builder = teaching_flow_builder or MinnaNoNihongoTeachingFlowBuilder()
        self.practice_generator = practice_generator or MinnaNoNihongoPracticeGenerator()
        self.render_plan_builder = render_plan_builder or MinnaNoNihongoRenderPlanBuilder()

    def run(
        self,
        data: dict,
        lesson_id: int,
        source_pdf: Path,
        lesson_pdf: Path,
        support_language: str = "zh",
        course_id: int | str = book1.COURSE_ID,
        token_merge_vocabulary: list[dict] | None = None,
    ) -> dict:
        data = data if isinstance(data, dict) else {}
        profile = resolve_lesson_profile(lesson_id)
        metadata = data.get("lesson_metadata") if isinstance(data.get("lesson_metadata"), dict) else {}
        course_content = data.get("course_content") if isinstance(data.get("course_content"), dict) else {}

        vocabulary = self._normalize_vocabulary(
            course_content.get("vocabulary") if isinstance(course_content.get("vocabulary"), list) else []
        )
        display_only_vocabulary = self._normalize_display_only_vocabulary(
            course_content.get("display_only_vocabulary")
            if isinstance(course_content.get("display_only_vocabulary"), list)
            else [],
            vocabulary,
        )
        lexical_notes = self._normalize_lexical_notes(
            course_content.get("lexical_notes") if isinstance(course_content.get("lexical_notes"), list) else []
        )
        base_token_merge_vocabulary = token_merge_vocabulary or []
        token_merge_vocabulary = base_token_merge_vocabulary + vocabulary + display_only_vocabulary
        sentence_patterns = self.reading_annotator.normalize_sentence_patterns(
            course_content.get("sentence_patterns")
            if isinstance(course_content.get("sentence_patterns"), list)
            else [],
            vocabulary,
            merge_vocabulary=token_merge_vocabulary,
        )
        example_sentences = self.reading_annotator.normalize_lines(
            course_content.get("example_sentences")
            if isinstance(course_content.get("example_sentences"), list)
            else [],
            vocabulary,
            merge_vocabulary=token_merge_vocabulary,
        )
        dialogue = course_content.get("dialogue") if isinstance(course_content.get("dialogue"), dict) else {}
        dialogue = {
            "title": (dialogue.get("title") or "").strip(),
            "title_localized": (dialogue.get("title_localized") or "").strip(),
            "lines": self.reading_annotator.normalize_lines(
                dialogue.get("lines") if isinstance(dialogue.get("lines"), list) else [],
                vocabulary,
                merge_vocabulary=token_merge_vocabulary,
            ),
        }
        vocabulary = self._hydrate_vocabulary_example_sentences(
            vocabulary,
            sentence_patterns=sentence_patterns,
            example_sentences=example_sentences,
            dialogue_lines=dialogue["lines"],
            merge_vocabulary=token_merge_vocabulary,
        )
        token_merge_vocabulary = base_token_merge_vocabulary + vocabulary + display_only_vocabulary
        grammar_sections = self._normalize_grammar_sections(
            course_content.get("grammar_sections")
            if isinstance(course_content.get("grammar_sections"), list)
            else [],
            vocabulary,
            merge_vocabulary=token_merge_vocabulary,
        )
        practice_items = self.practice_generator.normalize_practice_items(
            data.get("practice_items") if isinstance(data.get("practice_items"), list) else [],
            sentence_patterns,
            dialogue,
            lesson_id=lesson_id,
        )
        normalized_metadata = self._normalize_metadata(
            metadata=metadata,
            profile=profile,
            dialogue=dialogue,
            source_pdf=source_pdf,
            lesson_pdf=lesson_pdf,
            course_id=course_id,
        )
        normalized_course_content = {
            "sentence_patterns": sentence_patterns,
            "example_sentences": example_sentences,
            "dialogue": dialogue,
            "vocabulary": vocabulary,
            "lexical_notes": lexical_notes,
            "display_only_vocabulary": display_only_vocabulary,
            "grammar_sections": grammar_sections,
            "practice_source": (
                course_content.get("practice_source")
                if isinstance(course_content.get("practice_source"), list)
                else []
            ),
        }
        teaching_materials = self.teaching_flow_builder.run(
            normalized_course_content,
            data.get("teaching_materials") if isinstance(data.get("teaching_materials"), dict) else {},
        )
        video_render_plan = self.render_plan_builder.run(
            normalized_metadata,
            normalized_course_content,
            data.get("video_render_plan") if isinstance(data.get("video_render_plan"), dict) else None,
        )

        return {
            "schema_version": "1.0",
            "pipeline_id": "minna_no_nihongo",
            "target_language": "ja",
            "support_language": support_language,
            "lesson_metadata": normalized_metadata,
            "course_content": normalized_course_content,
            "teaching_materials": teaching_materials,
            "video_render_plan": video_render_plan,
            "practice_items": practice_items,
        }

    def _normalize_metadata(
        self,
        *,
        metadata: dict,
        profile: book1.LessonProfile,
        dialogue: dict,
        source_pdf: Path,
        lesson_pdf: Path,
        course_id: int | str,
    ) -> dict:
        topic_title, topic_title_localized = self._normalize_topic_titles(metadata, dialogue)
        section_titles = self._normalize_section_titles(metadata.get("section_titles"))
        if not section_titles:
            section_titles = self._default_section_titles(profile, dialogue)
        return {
            "course_id": int(course_id) if str(course_id).isdigit() else course_id,
            "course_slug": profile.course_slug,
            "lesson_id": profile.lesson_id,
            "lesson_slug": profile.lesson_slug,
            "title": (metadata.get("title") or f"第{profile.source_lesson}課").strip(),
            "title_localized": (metadata.get("title_localized") or f"第{profile.source_lesson}课").strip(),
            "topic_title": topic_title,
            "topic_title_localized": topic_title_localized,
            "section_titles": section_titles,
            "content_type": (metadata.get("content_type") or profile.content_type).strip(),
            "source": {
                "textbook": profile.textbook_name,
                "textbook_ja": profile.textbook_name_ja,
                "textbook_zh": profile.textbook_name_zh,
                "book": profile.book,
                "source_lesson": profile.source_lesson,
                "source_sections": list(profile.source_sections),
                "source_pdf": str(source_pdf),
                "lesson_pdf": str(lesson_pdf),
            },
        }

    def _normalize_topic_titles(self, metadata: dict, dialogue: dict) -> tuple[str, str]:
        topic_title = (metadata.get("topic_title") or "").strip()
        topic_title_localized = (metadata.get("topic_title_localized") or "").strip()
        if topic_title:
            return topic_title, topic_title_localized

        dialogue_title = (dialogue.get("title") or "").strip() if isinstance(dialogue, dict) else ""
        dialogue_title_localized = (
            (dialogue.get("title_localized") or "").strip() if isinstance(dialogue, dict) else ""
        )
        if dialogue_title and dialogue_title not in {"会話", "話す・聞く"}:
            return dialogue_title, dialogue_title_localized
        return "", topic_title_localized

    def _normalize_section_titles(self, items) -> list[dict]:
        normalized = []
        for item in items or []:
            if not isinstance(item, dict):
                continue
            section = (item.get("section") or item.get("source_section") or "").strip()
            title = (item.get("title") or "").strip()
            title_localized = (item.get("title_localized") or item.get("translation") or "").strip()
            if not section and not title and not title_localized:
                continue
            normalized.append({
                "section": section,
                "title": title,
                "title_localized": title_localized,
            })
        return normalized

    def _default_section_titles(self, profile: book1.LessonProfile, dialogue: dict) -> list[dict]:
        if profile.pedagogy_profile == "intermediate_read_write_speak_listen_grammar":
            return [
                {"section": "読む・書く", "title": "読む・書く", "title_localized": "读写"},
                {"section": "話す・聞く", "title": "話す・聞く", "title_localized": "会话与听力"},
                {"section": "文法・練習", "title": "文法・練習", "title_localized": "语法与练习"},
            ]

        dialogue_title = (dialogue.get("title") or "会話").strip() if isinstance(dialogue, dict) else "会話"
        dialogue_title_localized = (
            (dialogue.get("title_localized") or "会话").strip() if isinstance(dialogue, dict) else "会话"
        )
        return [
            {"section": "文型", "title": "文型", "title_localized": "文型"},
            {"section": "例文", "title": "例文", "title_localized": "例句"},
            {"section": "会話", "title": dialogue_title, "title_localized": dialogue_title_localized},
        ]

    def _normalize_grammar_sections(
        self,
        sections: list[dict],
        vocabulary: list[dict],
        merge_vocabulary: list[dict] | None = None,
    ) -> list[dict]:
        normalized = []
        for index, section in enumerate(sections or [], start=1):
            if not isinstance(section, dict):
                continue
            patterns = (
                section.get("patterns")
                if isinstance(section.get("patterns"), list)
                else []
            )
            examples = (
                section.get("examples")
                if isinstance(section.get("examples"), list)
                else []
            )
            normalized.append({
                "section_id": section.get("section_id") or f"grammar_{index}",
                "title": (section.get("title") or "").strip(),
                "explanation": (section.get("explanation") or "").strip(),
                "patterns": self.reading_annotator.normalize_sentence_patterns(
                    patterns,
                    vocabulary,
                    merge_vocabulary=merge_vocabulary,
                ),
                "examples": self.reading_annotator.normalize_lines(
                    examples,
                    vocabulary,
                    merge_vocabulary=merge_vocabulary,
                ),
                "usage_notes": [
                    str(note).strip()
                    for note in section.get("usage_notes", [])
                    if str(note).strip()
                ] if isinstance(section.get("usage_notes"), list) else [],
                "common_mistakes": [
                    str(note).strip()
                    for note in section.get("common_mistakes", [])
                    if str(note).strip()
                ] if isinstance(section.get("common_mistakes"), list) else [],
            })
        return normalized

    def _hydrate_vocabulary_example_sentences(
        self,
        vocabulary: list[dict],
        *,
        sentence_patterns: list[dict],
        example_sentences: list[dict],
        dialogue_lines: list[dict],
        merge_vocabulary: list[dict] | None = None,
    ) -> list[dict]:
        source_lookup: dict[tuple[str, int], dict] = {}
        text_lookup: dict[str, dict] = {}

        def add_sources(section: str, items: list[dict], ref_field: str) -> None:
            for fallback_ref, source in enumerate(items or [], start=1):
                if not isinstance(source, dict):
                    continue
                tokens = _copy_tokens(source.get("tokens") if isinstance(source.get("tokens"), list) else [])
                text = (source.get("text") or source.get("pattern") or "").strip()
                if not text or not tokens:
                    continue
                ref = _source_ref(source.get(ref_field)) or fallback_ref
                source_lookup[(section, ref)] = source
                text_lookup.setdefault(_compact_text(text), source)

        add_sources("sentence_patterns", sentence_patterns, "pattern_id")
        add_sources("example_sentences", example_sentences, "line_ref")
        add_sources("dialogue", dialogue_lines, "line_ref")

        hydrated = []
        for item in vocabulary or []:
            if not isinstance(item, dict):
                continue
            example = item.get("example_sentence")
            if not isinstance(example, dict):
                hydrated.append(item)
                continue
            text = (example.get("text") or example.get("ja") or "").strip()
            if not text:
                hydrated.append(item)
                continue

            normalized_example = dict(example)
            section_key = _source_section_key(example.get("source_section"))
            ref = _source_ref(example.get("source_ref") or example.get("line_ref") or example.get("pattern_id"))
            matched = source_lookup.get((section_key, ref)) if section_key and ref else None
            if matched and _compact_text(matched.get("text") or matched.get("pattern") or "") != _compact_text(text):
                matched = None
            matched = matched or text_lookup.get(_compact_text(text))

            if matched and _tokens_match_text(matched.get("tokens"), text):
                normalized_example["text"] = text
                normalized_example["reading"] = (matched.get("reading") or normalized_example.get("reading") or "").strip()
                normalized_example["romaji"] = (matched.get("romaji") or normalized_example.get("romaji") or "").strip()
                normalized_example["translation"] = (
                    normalized_example.get("translation")
                    or matched.get("translation")
                    or ""
                ).strip()
                normalized_example["tokens"] = _copy_tokens(matched.get("tokens"))
            else:
                normalized_lines = self.reading_annotator.normalize_lines(
                    [normalized_example],
                    vocabulary,
                    merge_vocabulary=merge_vocabulary or vocabulary,
                )
                if normalized_lines:
                    normalized_line = normalized_lines[0]
                    normalized_example["text"] = normalized_line.get("text") or text
                    normalized_example["reading"] = normalized_line.get("reading") or normalized_example.get("reading") or ""
                    normalized_example["romaji"] = normalized_line.get("romaji") or normalized_example.get("romaji") or ""
                    normalized_example["translation"] = normalized_example.get("translation") or normalized_line.get("translation") or ""
                    normalized_example["tokens"] = _copy_tokens(normalized_line.get("tokens"))

            hydrated.append({
                **item,
                "example_sentence": normalized_example,
            })
        return hydrated

    def _normalize_vocabulary(self, items: list[dict]) -> list[dict]:
        normalized = []
        seen = set()
        for item in items or []:
            if not isinstance(item, dict):
                continue
            term = (item.get("term") or item.get("word") or item.get("text") or item.get("ja") or "").strip()
            if not term:
                continue
            key = term.casefold()
            if key in seen:
                continue
            seen.add(key)
            translation = _first_non_empty(item.get("translation"), item.get("definition"), item.get("meaning"))
            normalized.append({
                "term": term,
                "word": term,
                "reading": (item.get("reading") or item.get("kana") or "").strip(),
                "romaji": (item.get("romaji") or "").strip(),
                "part_of_speech": _normalize_part_of_speech(item.get("part_of_speech")),
                "translation": translation,
                "definition": translation,
                "accent": item.get("accent") or "",
                **({"category": item.get("category")} if item.get("category") else {}),
                **({"type": item.get("type")} if item.get("type") else {}),
                "lesson_section": _normalize_lesson_section(item.get("lesson_section") or item.get("section")),
                **({"example_sentence": item.get("example_sentence")} if isinstance(item.get("example_sentence"), dict) else {}),
            })
        return normalized

    def _normalize_display_only_vocabulary(
        self,
        items: list[dict],
        learnable_vocabulary: list[dict],
    ) -> list[dict]:
        learnable_terms = {
            (item.get("term") or item.get("word") or "").strip().casefold()
            for item in learnable_vocabulary
            if isinstance(item, dict) and (item.get("term") or item.get("word") or "").strip()
        }
        normalized = []
        seen = set()
        for item in items or []:
            if not isinstance(item, dict):
                continue
            term = (item.get("term") or item.get("word") or item.get("text") or item.get("ja") or "").strip()
            if not term:
                continue
            key = term.casefold()
            if key in seen or key in learnable_terms:
                continue
            seen.add(key)
            normalized.append({
                "term": term,
                "reading": (item.get("reading") or item.get("kana") or "").strip(),
                "romaji": (item.get("romaji") or "").strip(),
                "category": (item.get("category") or item.get("type") or "proper_noun").strip(),
                "translation": _first_non_empty(item.get("translation"), item.get("definition"), item.get("meaning"), term),
                "reason": (item.get("reason") or "display_only").strip(),
                "lesson_section": (item.get("lesson_section") or item.get("section") or "reference").strip(),
            })
        return normalized

    def _normalize_lexical_notes(self, items: list[dict]) -> list[dict]:
        normalized = []
        seen = set()
        for item in items or []:
            if not isinstance(item, dict):
                continue
            term = (item.get("term") or item.get("word") or item.get("text") or item.get("ja") or "").strip()
            if not term:
                continue
            key = term.casefold()
            if key in seen:
                continue
            seen.add(key)
            translation = _first_non_empty(item.get("translation"), item.get("definition"), item.get("meaning"))
            normalized.append({
                "term": term,
                "word": term,
                "reading": (item.get("reading") or item.get("kana") or "").strip(),
                "romaji": (item.get("romaji") or "").strip(),
                "part_of_speech": _normalize_part_of_speech(item.get("part_of_speech")),
                "translation": translation,
                "definition": translation,
                "source_section": (item.get("source_section") or item.get("section") or "").strip(),
                "learning_role": (item.get("learning_role") or "context_only").strip(),
                "quiz_eligible": bool(item.get("quiz_eligible")) if "quiz_eligible" in item else False,
                "reason": (item.get("reason") or item.get("policy_reason") or "reading_support").strip(),
            })
        return normalized
