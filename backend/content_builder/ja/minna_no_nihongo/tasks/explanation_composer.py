from __future__ import annotations

try:
    from content_builder.ja.minna_no_nihongo.tasks.render_plan_builder import (
        MinnaNoNihongoRenderPlanBuilder,
        _grammar_board,
        _grammar_cards,
        _ja_focus_tokens,
        _ja_pattern_highlights,
        _pattern_note,
        _sentence_card,
        _sentence_stack_note,
        _segment,
        _translation,
        _vocab_board,
        _vocab_footer,
        _vocab_note,
    )
    from content_builder.ja.minna_no_nihongo.tasks.teaching_flow_builder import split_vocabulary_by_section
except ImportError:
    from content_builder.ja.minna_no_nihongo.tasks.render_plan_builder import (
        MinnaNoNihongoRenderPlanBuilder,
        _grammar_board,
        _grammar_cards,
        _ja_focus_tokens,
        _ja_pattern_highlights,
        _pattern_note,
        _sentence_card,
        _sentence_stack_note,
        _segment,
        _translation,
        _vocab_board,
        _vocab_footer,
        _vocab_note,
    )
    from content_builder.ja.minna_no_nihongo.tasks.teaching_flow_builder import split_vocabulary_by_section


DIRECTOR_PLAN_VERSION = "mnn_llm_director_v1"


def _text(value) -> str:
    return str(value or "").strip()


def _duration(value, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return round(max(8.0, min(parsed, 45.0)), 2)


def _source(segment: dict) -> tuple[str, list[int]]:
    raw = segment.get("source") if isinstance(segment.get("source"), dict) else {}
    kind = _text(raw.get("kind") or segment.get("source_kind"))
    indexes = raw.get("indexes") if isinstance(raw.get("indexes"), list) else segment.get("source_indexes")
    if not isinstance(indexes, list):
        indexes = []
    normalized: list[int] = []
    for item in indexes:
        try:
            index = int(item)
        except (TypeError, ValueError):
            continue
        if index > 0 and index not in normalized:
            normalized.append(index)
    return kind, normalized


def _pick_by_indexes(items: list[dict], indexes: list[int], limit: int) -> list[dict]:
    picked = []
    for index in indexes:
        if 1 <= index <= len(items):
            item = items[index - 1]
            if isinstance(item, dict):
                picked.append(item)
        if len(picked) >= limit:
            break
    return picked


def _first_text(*values) -> str:
    for value in values:
        text = _text(value)
        if text:
            return text
    return ""


def _chunk(items: list, size: int) -> list[list]:
    return [items[index:index + size] for index in range(0, len(items), size)]


def _recap_word_from_item(item: dict) -> dict | None:
    word = _first_text(item.get("term"), item.get("word"), item.get("text"))
    if not word:
        return None
    return {
        "word": word,
        "pinyin": _first_text(item.get("reading"), item.get("romaji")),
        "translation": _first_text(item.get("translation"), item.get("definition")),
    }


_OPENING_TITLE_RE = ("目标", "學習目標", "学习目标", "本课目标", "课程概览", "概览", "导入", "开场", "欢迎")
_OPENING_TEXT_RE = ("欢迎来到", "准备好了吗", "我们将学习", "这一课，我们将", "本课我们将", "学习目标")


class MinnaNoNihongoExplanationComposer:
    """Compose LLM-directed explanation segments into supported Japanese slide templates."""

    def __init__(self, fallback_builder: MinnaNoNihongoRenderPlanBuilder | None = None):
        self.fallback_builder = fallback_builder or MinnaNoNihongoRenderPlanBuilder()

    def run(self, metadata: dict, course_content: dict, explanation: dict | None) -> dict:
        if not self._has_director_shape(explanation):
            return self.fallback_builder.run(metadata, course_content, existing_plan=None)

        context = self._context(course_content)
        raw_segments = explanation.get("segments") if isinstance(explanation, dict) else []
        segments = []
        cursor = 0.0
        recap_raw = None

        for raw in raw_segments:
            if not isinstance(raw, dict):
                continue
            if _text(raw.get("segment_type")) == "recap":
                recap_raw = recap_raw or raw
                continue
            if self._is_opening_overview_segment(raw, context):
                continue
            composed = self._compose_one(
                order=len(segments) + 1,
                start_time_seconds=cursor,
                raw=raw,
                metadata=metadata,
                context=context,
            )
            if not composed:
                continue
            composed_segments = composed if isinstance(composed, list) else [composed]
            for segment in composed_segments:
                if not segment:
                    continue
                segments.append(segment)
                cursor = segment["end_time_seconds"]

        cursor = self._append_required_content_segments(segments, cursor, context)
        cursor = self._append_required_vocabulary_segments(segments, cursor, context)

        if recap_raw:
            recap = self._compose_one(
                order=len(segments) + 1,
                start_time_seconds=cursor,
                raw=recap_raw,
                metadata=metadata,
                context=context,
            )
            if recap:
                segments.append(recap)
                cursor = recap["end_time_seconds"]

        if not any(segment.get("segment_type") == "recap" for segment in segments):
            recap = self._auto_recap_segment(
                order=len(segments) + 1,
                start=cursor,
                metadata=metadata,
                context=context,
            )
            if recap:
                segments.append(recap)
                cursor = recap["end_time_seconds"]

        if not segments:
            return self.fallback_builder.run(metadata, course_content, existing_plan=None)

        return {
            "explanation": {
                "lesson_id": metadata.get("lesson_id"),
                "course_id": metadata.get("course_id"),
                "lesson_title": metadata.get("title_localized") or metadata.get("title") or "",
                "target_audience": "Chinese speakers learning Japanese",
                "video_style": {
                    "presenter_mode": "voice_over",
                    "teaching_style": (
                        (explanation.get("global_config") or {}).get("teaching_style")
                        if isinstance(explanation.get("global_config"), dict)
                        else ""
                    ) or "LLM-directed beginner Japanese lesson",
                    "visual_style": "static teaching slide deck",
                    "aspect_ratio": "16:9",
                    "safe_area": "title_safe",
                },
                "segments": segments,
                "timeline": {
                    "total_duration_seconds": round(cursor, 2),
                    "segment_count": len(segments),
                },
                "renderer_notes": {
                    "plan_version": DIRECTOR_PLAN_VERSION,
                    "recommended_renderer": "static_teaching_slide_deck",
                    "remarks": "Japanese render plan composed from an LLM-directed explanation script.",
                },
            }
        }

    def _has_director_shape(self, explanation: dict | None) -> bool:
        if not isinstance(explanation, dict):
            return False
        segments = explanation.get("segments")
        if not isinstance(segments, list) or not segments:
            return False
        for segment in segments:
            if not isinstance(segment, dict):
                return False
            narration = segment.get("narration")
            if not isinstance(narration, dict) or not _text(narration.get("subtitle_zh")):
                return False
        return True

    def _is_opening_overview_segment(self, segment: dict, context: dict) -> bool:
        segment_type = _text(segment.get("segment_type"))
        if segment_type not in {"line_walkthrough", "sentence_focus", "dialogue_focus", "grammar_focus", "vocabulary_focus", ""}:
            return False
        title = _text(segment.get("segment_title"))
        narration = segment.get("narration") if isinstance(segment.get("narration"), dict) else {}
        text = _text(narration.get("subtitle_zh") or narration.get("script"))
        kind, indexes = _source(segment)
        has_valid_source = bool(indexes) and kind in {
            "sentence_patterns",
            "example_sentences",
            "dialogue",
            "grammar_sections",
            "core_vocabulary",
            "supplementary_vocabulary",
            "display_only_vocabulary",
            "vocabulary",
        }
        has_real_lesson_text = False
        for collection_name in ("sentence_patterns", "example_sentences", "dialogue_lines"):
            for item in context.get(collection_name) or []:
                item_text = _text(item.get("text")) if isinstance(item, dict) else ""
                if item_text and item_text in text:
                    has_real_lesson_text = True
                    break
            if has_real_lesson_text:
                break
        if has_valid_source and has_real_lesson_text:
            return False
        return any(token in title for token in _OPENING_TITLE_RE) or any(token in text for token in _OPENING_TEXT_RE)

    def _context(self, course_content: dict) -> dict:
        dialogue = course_content.get("dialogue") if isinstance(course_content.get("dialogue"), dict) else {}
        vocabulary = course_content.get("vocabulary") if isinstance(course_content.get("vocabulary"), list) else []
        core_vocabulary, supplementary_vocabulary = split_vocabulary_by_section(vocabulary)
        display_only = (
            course_content.get("display_only_vocabulary")
            if isinstance(course_content.get("display_only_vocabulary"), list)
            else []
        )
        return {
            "sentence_patterns": course_content.get("sentence_patterns") or [],
            "example_sentences": course_content.get("example_sentences") or [],
            "dialogue": dialogue,
            "dialogue_lines": dialogue.get("lines") or [],
            "vocabulary": vocabulary,
            "core_vocabulary": core_vocabulary,
            "supplementary_vocabulary": supplementary_vocabulary,
            "display_only_vocabulary": display_only,
            "grammar_sections": course_content.get("grammar_sections") or [],
        }

    def _compose_one(
        self,
        *,
        order: int,
        start_time_seconds: float,
        raw: dict,
        metadata: dict,
        context: dict,
    ) -> dict | list[dict] | None:
        segment_type = _text(raw.get("segment_type")) or "line_walkthrough"
        if segment_type == "sentence_stack":
            segment_type = "sentence_focus"
        kind, indexes = _source(raw)
        narration = raw.get("narration") if isinstance(raw.get("narration"), dict) else {}
        narration_text = _text(narration.get("subtitle_zh") or narration.get("script"))
        if not narration_text:
            return None
        title = _text(raw.get("segment_title")) or f"讲解 {order}"
        teaching_goal = _text(raw.get("teaching_goal")) or "帮助学生理解本页内容。"

        if segment_type == "line_walkthrough":
            return self._line_segment(order, start_time_seconds, raw, context, kind, indexes, title, teaching_goal, narration_text)
        if segment_type == "sentence_focus":
            if len(indexes) > 4:
                return self._split_sentence_segments(
                    order,
                    start_time_seconds,
                    raw,
                    context,
                    kind or "example_sentences",
                    indexes,
                    title,
                    teaching_goal,
                )
            return self._sentence_segment(order, start_time_seconds, raw, context, kind or "example_sentences", indexes, title, teaching_goal, narration_text)
        if segment_type == "dialogue_focus":
            if len(indexes) > 4:
                return self._split_sentence_segments(
                    order,
                    start_time_seconds,
                    raw,
                    context,
                    "dialogue",
                    indexes,
                    title,
                    teaching_goal,
                )
            return self._sentence_segment(order, start_time_seconds, raw, context, "dialogue", indexes, title, teaching_goal, narration_text)
        if segment_type == "vocabulary_focus":
            return self._vocab_segment(order, start_time_seconds, raw, context, kind or "vocabulary", indexes, title, teaching_goal, narration_text)
        if segment_type == "grammar_focus":
            return self._grammar_segment(order, start_time_seconds, raw, context, indexes, title, teaching_goal, narration_text)
        if segment_type == "recap":
            return self._recap_segment(order, start_time_seconds, raw, context, title, teaching_goal, narration_text)
        return None

    def _line_segment(self, order, start, raw, context, kind, indexes, title, goal, narration) -> dict | None:
        if kind == "dialogue":
            source_items = context["dialogue_lines"]
        elif kind == "example_sentences":
            source_items = context["example_sentences"]
        else:
            source_items = context["sentence_patterns"]
        item = (_pick_by_indexes(source_items, indexes, 1) or source_items[:1] or [{}])[0]
        focus_text = _text(item.get("text"))
        if not focus_text:
            return None
        vocabulary = context["vocabulary"]
        return _segment(
            order=order,
            segment_type="line_walkthrough",
            template_name="ja_line_focus",
            title=title,
            teaching_goal=goal,
            duration_seconds=_duration(raw.get("estimated_duration_seconds"), 18.0),
            visual_blocks=[
                {
                    "block_type": "hero_line",
                    "content": {
                        "focus_text": focus_text,
                        "focus_pinyin": _text(item.get("reading")),
                        "focus_gloss_en": _translation(item),
                        "tokens": _ja_focus_tokens(item, vocabulary),
                    },
                    "weight": 0.62,
                },
                {
                    "block_type": "teaching_points",
                    "content": {
                        "notes": _pattern_note(item),
                        "highlight_words": _ja_pattern_highlights(item, vocabulary),
                    },
                    "weight": 0.38,
                },
            ],
            start_time_seconds=start,
            narration_text=narration,
        )

    def _sentence_segment(self, order, start, raw, context, kind, indexes, title, goal, narration) -> dict | None:
        source_items = context["dialogue_lines"] if kind == "dialogue" else context["example_sentences"]
        items = _pick_by_indexes(source_items, indexes, 4)
        if not items:
            return None
        mode = "dialogue" if kind == "dialogue" else "examples"
        return _segment(
            order=order,
            segment_type="dialogue_focus" if mode == "dialogue" else "sentence_focus",
            template_name="ja_sentence_stack",
            title=title,
            teaching_goal=goal,
            duration_seconds=_duration(raw.get("estimated_duration_seconds"), max(14.0, len(items) * 4.0)),
            visual_block_type="ja_sentence_stack",
            visual_content={
                "mode": mode,
                "note": _sentence_stack_note(items, mode=mode),
                "lines": [_sentence_card(item, vocabulary=context["vocabulary"]) for item in items],
            },
            start_time_seconds=start,
            narration_text=narration,
        )

    def _split_sentence_segments(self, order, start, raw, context, kind, indexes, title, goal) -> list[dict]:
        chunks = self._split_focus_indexes(indexes, max_per_page=4)
        segments: list[dict] = []
        cursor = start
        mode = "dialogue" if kind == "dialogue" else "examples"
        source_items = context["dialogue_lines"] if kind == "dialogue" else context["example_sentences"]
        total = len(chunks)
        for offset, chunk in enumerate(chunks, start=1):
            items = _pick_by_indexes(source_items, chunk, 4)
            if not items:
                continue
            part_title = title if total <= 1 else f"{title} ({offset})"
            part_goal = goal if total <= 1 else f"{goal} 这是第 {offset} 部分。"
            segment = self._sentence_segment(
                order + len(segments),
                cursor,
                {"estimated_duration_seconds": max(14, len(items) * 4)},
                context,
                kind,
                chunk,
                part_title,
                part_goal,
                self._auto_sentence_narration(items, mode=mode),
            )
            if segment:
                segments.append(segment)
                cursor = segment["end_time_seconds"]
        return segments

    def _split_focus_indexes(self, indexes: list[int], max_per_page: int = 4) -> list[list[int]]:
        valid = []
        for item in indexes:
            try:
                index = int(item)
            except (TypeError, ValueError):
                continue
            if index > 0 and index not in valid:
                valid.append(index)
        if len(valid) <= max_per_page:
            return [valid] if valid else []

        page_count = (len(valid) + max_per_page - 1) // max_per_page
        base = len(valid) // page_count
        remainder = len(valid) % page_count
        sizes = [base + (1 if i < remainder else 0) for i in range(page_count)]
        if sizes and sizes[-1] == 1 and len(sizes) >= 2 and sizes[-2] < max_per_page:
            sizes[-2] += 1
            sizes.pop()

        chunks: list[list[int]] = []
        cursor = 0
        for size in sizes:
            chunk = valid[cursor:cursor + size]
            if chunk:
                chunks.append(chunk)
            cursor += size
        return chunks

    def _vocab_segment(self, order, start, raw, context, kind, indexes, title, goal, narration) -> dict | None:
        if kind == "display_only_vocabulary":
            group = "display_only"
            source_items = context["display_only_vocabulary"]
            heading = "专名识别"
        elif kind == "supplementary_vocabulary":
            group = "supplementary"
            source_items = context["supplementary_vocabulary"]
            heading = "补充词汇"
        elif kind == "core_vocabulary":
            group = "core"
            source_items = context["core_vocabulary"]
            heading = "主线词汇"
        else:
            group = "core"
            source_items = context["core_vocabulary"]
            heading = "主线词汇"
        items = _pick_by_indexes(source_items, indexes, 4)
        if not items:
            return None
        return _segment(
            order=order,
            segment_type="vocabulary_focus",
            template_name="ja_vocab_board",
            title=title,
            teaching_goal=goal,
            duration_seconds=_duration(raw.get("estimated_duration_seconds"), max(12.0, len(items) * 3.0)),
            visual_block_type="ja_vocab_board",
            visual_content=_vocab_board(
                items,
                group=group,
                heading=heading,
                note=_vocab_note(items, group=group),
                footer=_vocab_footer(items, group=group),
            ),
            start_time_seconds=start,
            narration_text=narration,
        )

    def _append_required_content_segments(self, segments: list[dict], cursor: float, context: dict) -> float:
        covered_patterns = self._covered_line_texts(segments, mode="line")
        covered_examples = self._covered_line_texts(segments, mode="examples")
        covered_dialogue = self._covered_line_texts(segments, mode="dialogue")
        covered_grammar = self._covered_grammar_titles(segments)

        for index, pattern in enumerate(context.get("sentence_patterns") or [], start=1):
            if not isinstance(pattern, dict):
                continue
            text = _text(pattern.get("text"))
            if not text or text in covered_patterns:
                continue
            segment = self._line_segment(
                len(segments) + 1,
                cursor,
                {"estimated_duration_seconds": 18},
                context,
                "sentence_patterns",
                [index],
                f"文型 {index}",
                "建立本课核心句型。",
                "这里补上本课必须掌握的文型。先听日语原句，再看它的意思和结构。",
            )
            if segment:
                segments.append(segment)
                cursor = segment["end_time_seconds"]
                covered_patterns.add(text)

        example_indexes = [
            index
            for index, item in enumerate(context.get("example_sentences") or [], start=1)
            if isinstance(item, dict) and _text(item.get("text")) and _text(item.get("text")) not in covered_examples
        ]
        for page, indexes in enumerate(_chunk(example_indexes, 3), start=1):
            items = _pick_by_indexes(context.get("example_sentences") or [], indexes, 3)
            segment = self._sentence_segment(
                len(segments) + 1,
                cursor,
                {"estimated_duration_seconds": max(14, len(indexes) * 4)},
                context,
                "example_sentences",
                indexes,
                f"例文补充 {page}",
                "覆盖教材例文中的剩余问答和独立句。",
                self._auto_sentence_narration(items, mode="examples"),
            )
            if segment:
                segments.append(segment)
                cursor = segment["end_time_seconds"]

        dialogue_indexes = [
            index
            for index, item in enumerate(context.get("dialogue_lines") or [], start=1)
            if isinstance(item, dict) and _text(item.get("text")) and _text(item.get("text")) not in covered_dialogue
        ]
        for page, indexes in enumerate(_chunk(dialogue_indexes, 3), start=1):
            items = _pick_by_indexes(context.get("dialogue_lines") or [], indexes, 3)
            segment = self._sentence_segment(
                len(segments) + 1,
                cursor,
                {"estimated_duration_seconds": max(14, len(indexes) * 4)},
                context,
                "dialogue",
                indexes,
                f"会话补充 {page}",
                "覆盖完整会话，帮助学生听懂课文场景。",
                self._auto_sentence_narration(items, mode="dialogue"),
            )
            if segment:
                segments.append(segment)
                cursor = segment["end_time_seconds"]

        for index, section in enumerate(context.get("grammar_sections") or [], start=1):
            if not isinstance(section, dict):
                continue
            title = _text(section.get("title"))
            if not title or title in covered_grammar:
                continue
            sections = _pick_by_indexes(context.get("grammar_sections") or [], [index], 1)
            segment = self._grammar_segment(
                len(segments) + 1,
                cursor,
                {"estimated_duration_seconds": 24},
                context,
                [index],
                f"语法补充 {index}",
                "覆盖本课遗漏的语法点。",
                self._auto_grammar_narration(sections[0] if sections else section),
            )
            if segment:
                segments.append(segment)
                cursor = segment["end_time_seconds"]
                covered_grammar.add(title)
        return cursor

    def _auto_sentence_narration(self, items: list[dict], *, mode: str) -> str:
        valid_items = [item for item in items if isinstance(item, dict) and _text(item.get("text"))]
        if not valid_items:
            return "这一页继续补完整段内容。先听日语原句，再看中文意思，最后回到句尾和助词确认结构。"

        clauses: list[str] = []
        for item in valid_items[:3]:
            text = _text(item.get("text"))
            translation = _translation(item)
            speaker = _text(item.get("speaker"))
            prefix = f"{speaker}说：" if mode == "dialogue" and speaker else ""
            if translation:
                clauses.append(f"{prefix}{self._tag(text)}，意思是“{translation}”")
            else:
                clauses.append(f"{prefix}{self._tag(text)}")

        joined = "；".join(clauses) + "。"
        texts = " ".join(_text(item.get("text")) for item in valid_items)
        has_question = "か" in texts or "？" in texts or "?" in texts
        has_negative = "じゃ" in texts or "ありません" in texts
        has_ellipsis = any(not _text(item.get("text")).startswith(("わたし", "あなた", "あの", "この", "その")) for item in valid_items)

        if mode == "dialogue":
            reminder = "读会话时重点不是逐字背，而是听出谁在向谁介绍、谁在回应。"
            if has_ellipsis:
                reminder += "日语会话里主语经常省略，所以要靠上一句和说话人来补出意思。"
            return f"这一页继续顺会话。{joined}{reminder}"

        reminder_parts = []
        if has_question:
            reminder_parts.append("有问句时，先听句尾的疑问语气，再判断是用“はい/いいえ”回答，还是直接给信息。")
        if has_negative:
            reminder_parts.append("看到否定形式时，不要只记中文“不”，要把整段 [ja:じゃ ありません] 当作一个句尾块来听。")
        if not reminder_parts:
            reminder_parts.append("读例文时，先确认句子在判断什么，再看助词把哪一部分标成主题。")
        return f"这一页把几个例文连起来看。{joined}{''.join(reminder_parts)}"

    def _auto_grammar_narration(self, section: dict) -> str:
        title = _text(section.get("title")) or "这个语法点"
        explanation = _text(section.get("explanation"))
        patterns = section.get("patterns") if isinstance(section.get("patterns"), list) else []
        examples = section.get("examples") if isinstance(section.get("examples"), list) else []

        pattern = ""
        for item in patterns:
            if isinstance(item, dict) and _text(item.get("text")):
                pattern = _text(item.get("text"))
                break
        example = ""
        translation = ""
        for item in examples:
            if isinstance(item, dict) and _text(item.get("text")):
                example = _text(item.get("text"))
                translation = _translation(item)
                break

        parts = [f"这里再把 {self._tag(title)} 单独拎出来确认。"]
        if explanation:
            parts.append(explanation)
        if pattern:
            parts.append(f"结构上可以先记成 {self._tag(pattern)}，把它当作一个可以替换名词或句尾的框架。")
        if example:
            if translation:
                parts.append(f"比如 {self._tag(example)}，意思是“{translation}”。")
            else:
                parts.append(f"比如 {self._tag(example)}。")
        parts.append("学习时不要急着逐词翻译，先抓住这个结构在句子里承担的功能，再换入新的词。")
        return "".join(parts)

    def _covered_line_texts(self, segments: list[dict], *, mode: str) -> set[str]:
        covered: set[str] = set()
        for segment in segments:
            if not isinstance(segment, dict):
                continue
            for block in segment.get("visual_blocks") or []:
                if not isinstance(block, dict):
                    continue
                content = block.get("content") if isinstance(block.get("content"), dict) else {}
                focus_text = _text(content.get("focus_text"))
                if mode == "line" and focus_text:
                    covered.add(focus_text)
                if mode != _text(content.get("mode")):
                    continue
                for line in content.get("lines") or []:
                    if isinstance(line, dict) and _text(line.get("text")):
                        covered.add(_text(line.get("text")))
        return covered

    def _covered_grammar_titles(self, segments: list[dict]) -> set[str]:
        covered: set[str] = set()
        for segment in segments:
            if not isinstance(segment, dict):
                continue
            for block in segment.get("visual_blocks") or []:
                if not isinstance(block, dict):
                    continue
                content = block.get("content") if isinstance(block.get("content"), dict) else {}
                if block.get("block_type") == "ja_grammar_board" and _text(content.get("title")):
                    covered.add(_text(content.get("title")))
        return covered

    def _append_required_vocabulary_segments(self, segments: list[dict], cursor: float, context: dict) -> float:
        """Ensure the director cannot silently drop required vocabulary groups."""
        groups = [
            ("core", "core_vocabulary", "主线词汇", "词汇", "掌握本课主线词汇。"),
            ("supplementary", "supplementary_vocabulary", "补充词汇", "补充词汇", "掌握练习和扩展表达中会出现的补充词汇。"),
            ("display_only", "display_only_vocabulary", "专名识别", "专名", "认读课文中的人名、机构名等专名。"),
        ]
        for group, context_key, heading, title_prefix, goal in groups:
            source_items = [item for item in context.get(context_key) or [] if isinstance(item, dict)]
            if not source_items:
                continue
            covered = self._covered_vocab_terms(segments, group)
            missing = [item for item in source_items if self._vocab_key(item) not in covered]
            if not missing:
                continue
            for page, items in enumerate(_chunk(missing, 4), start=1):
                narration = self._auto_vocab_narration(items, group, page=page)
                segment = _segment(
                    order=len(segments) + 1,
                    segment_type="vocabulary_focus",
                    template_name="ja_vocab_board",
                    title=self._auto_vocab_title(items, group, title_prefix, page),
                    teaching_goal=goal,
                    duration_seconds=max(10.0, len(items) * (1.8 if group == "display_only" else 2.2)),
                    visual_block_type="ja_vocab_board",
                    visual_content=_vocab_board(
                        items,
                        group=group,
                        heading=heading,
                        note=_vocab_note(items, group=group),
                        footer=_vocab_footer(items, group=group),
                    ),
                    start_time_seconds=cursor,
                    narration_text=narration,
                )
                segments.append(segment)
                cursor = segment["end_time_seconds"]
        return cursor

    def _covered_vocab_terms(self, segments: list[dict], group: str) -> set[str]:
        covered: set[str] = set()
        for segment in segments:
            if not isinstance(segment, dict) or segment.get("segment_type") != "vocabulary_focus":
                continue
            for block in segment.get("visual_blocks") or []:
                if not isinstance(block, dict):
                    continue
                content = block.get("content") if isinstance(block.get("content"), dict) else {}
                if content.get("group") != group:
                    continue
                for item in content.get("items") or []:
                    if isinstance(item, dict):
                        key = self._vocab_key(item)
                        if key:
                            covered.add(key)
        return covered

    def _vocab_key(self, item: dict) -> str:
        return _first_text(item.get("term"), item.get("word")).replace("〜", "").replace("~", "")

    def _auto_vocab_title(self, items: list[dict], group: str, title_prefix: str, page: int) -> str:
        relation = self._vocab_relation(items, group)
        if relation.get("title"):
            return f"{title_prefix}: {relation['title']}"
        return f"{title_prefix} {page}"

    def _auto_vocab_narration(self, items: list[dict], group: str, *, page: int) -> str:
        relation = self._vocab_relation(items, group)
        terms = [_first_text(item.get("term"), item.get("word")) for item in items if isinstance(item, dict)]
        tagged_terms = [f"[ja:{term}]" for term in terms if term]
        tagged = "、".join(tagged_terms)
        explanations = self._vocab_item_explanations(items)
        if group == "display_only":
            if relation.get("lead"):
                return f"{relation['lead']}{explanations}这些在课文里认得即可，不需要当作复习重点。"
            return f"这一页快速扫一下专名：{tagged}。{explanations}听课文和做练习时能认出来就好。"
        if group == "supplementary":
            if relation.get("lead"):
                return f"{relation['lead']} {explanations}这些词会在练习替换里出现，先做到看见能懂、听到能跟上。"
            opener = "补充词汇我们不用讲得太重，但要把读音和意思对上。"
            return f"{opener}{explanations}之后在练习里遇到时，就不会觉得陌生。"
        if relation.get("lead"):
            return f"{relation['lead']} {explanations}这些词会直接回到文型和例句里，先把读音读顺。"
        opener = "这一页继续补主线词汇。"
        if page == 1:
            opener = "先把这一组主线词汇读清楚。"
        return f"{opener}{explanations}读的时候先听假名，再把词义放回课文场景里。"

    def _vocab_item_explanations(self, items: list[dict], limit: int = 4) -> str:
        clauses: list[str] = []
        for item in items[:limit]:
            if not isinstance(item, dict):
                continue
            term = _first_text(item.get("term"), item.get("word"))
            if not term:
                continue
            reading = _first_text(item.get("reading"))
            translation = _first_text(item.get("translation"), item.get("definition"))
            if reading and reading != term and translation:
                clauses.append(f"{self._tag(term)} 读作 {self._tag(reading)}，意思是“{translation}”")
            elif translation:
                clauses.append(f"{self._tag(term)} 是“{translation}”")
            elif reading and reading != term:
                clauses.append(f"{self._tag(term)} 读作 {self._tag(reading)}")
            else:
                clauses.append(self._tag(term))
        if not clauses:
            return ""
        return "；".join(clauses) + "。"

    def _vocab_relation(self, items: list[dict], group: str) -> dict:
        terms = [_first_text(item.get("term"), item.get("word")) for item in items if isinstance(item, dict)]
        translations = [_first_text(item.get("translation"), item.get("definition")) for item in items if isinstance(item, dict)]
        pos_values = {
            _first_text(item.get("part_of_speech"), item.get("category"))
            for item in items
            if isinstance(item, dict) and _first_text(item.get("part_of_speech"), item.get("category"))
        }
        if not terms:
            return {}

        if group == "display_only":
            if all(self._is_likely_person_name(item) for item in items if isinstance(item, dict)):
                return {"title": "人名识别", "lead": "这一页都是人名，快速认一下。"}
            return {"title": "专名识别", "lead": "这些是课文里出现的专名，先有个印象。"}
        if len(terms) < 2:
            return {}

        suffix_count = sum(1 for term in terms if term.startswith("〜") or term.startswith("～"))
        age_count = sum(
            1
            for term, translation in zip(terms, translations)
            if "歳" in term or "岁" in translation or "年龄" in translation
        )
        country_terms = {"日本", "中国", "韓国", "アメリカ", "イギリス", "ドイツ", "ブラジル", "タイ", "インド", "インドネシア", "フランス", "イタリア", "スイス"}
        country_count = sum(
            1
            for term, translation in zip(terms, translations)
            if term in country_terms or any(word in translation for word in ("国", "国家", "美国", "英国", "德国", "巴西", "泰国", "印度", "韩国", "日本", "中国", "法国", "意大利", "瑞士"))
        )
        place_count = sum(
            1
            for term, translation in zip(terms, translations)
            if any(word in translation for word in ("神户", "大阪", "广岛", "医院", "大学", "公司", "机场", "办公室", "前台", "大厅", "厕所", "洗手间"))
        )
        question_count = sum(1 for term in terms if "何" in term or term in {"どこ", "どちら", "だれ", "誰", "どなた", "いくら", "おいくつ"})

        if suffix_count >= 2:
            return {
                "title": "接续表达",
                "lead": "这一页有接在别的词前后使用的表达，注意它们不是单独孤零零出现的。",
            }
        if age_count >= max(2, len(terms) - 1):
            return {"title": "年龄表达", "lead": "这组和年龄问答有关，读音要特别留意。"}
        if sum(1 for term in terms if term.endswith("語") or term.endswith("语")) >= 2 or sum(1 for text in translations if "语" in text or "語" in text) >= 2:
            return {
                "title": "语言表达",
                "lead": f"这组和语言名称有关，后面的 {self._tag('語')} 表示“某种语言”。",
            }
        if sum(1 for term in terms if term.endswith("人")) >= 2 or country_count >= max(3, len(terms) - 1):
            return {
                "title": "国家与身份",
                "lead": "这组可以和国籍、出身信息连起来看。",
            }
        if place_count >= max(2, len(terms) // 2 + 1):
            return {"title": "地点与机构", "lead": "这组多半是在介绍地点、机构或场所，适合放回课文场景里记。"}
        if sum(1 for term in terms if "員" in term or "者" in term or "生" in term) >= 2:
            return {
                "title": "身份职业",
                "lead": "这一页多和身份、职业有关。",
            }
        if question_count >= 2:
            return {
                "title": "疑问表达",
                "lead": "这组词常用来发问，听到它们就要准备接收信息。",
            }
        if len(pos_values) == 1:
            pos = next(iter(pos_values))
            if "感" in pos or "表达" in pos or "表現" in pos:
                return {"title": "常用表达", "lead": "这一页更像课堂里直接能用的表达。"}
            if "名" in pos:
                return {"title": "名词组", "lead": "这组都是名词，先把读音和具体指代对上。"}
        return {}

    def _tag(self, term: str) -> str:
        return f"[ja:{term}]" if term else ""

    def _is_likely_person_name(self, item: dict) -> bool:
        category = _first_text(item.get("category"), item.get("part_of_speech"))
        if "person" in category or "人名" in category:
            return True
        translation = _first_text(item.get("translation"), item.get("definition"))
        return "先生" in translation or "女士" in translation or "人名" in translation

    def _grammar_segment(self, order, start, raw, context, indexes, title, goal, narration) -> dict | None:
        sections = _pick_by_indexes(context["grammar_sections"], indexes, 1)
        if not sections:
            return None
        section = sections[0]
        return _segment(
            order=order,
            segment_type="grammar_focus",
            template_name="ja_grammar_board",
            title=title,
            teaching_goal=goal,
            duration_seconds=_duration(raw.get("estimated_duration_seconds"), 24.0),
            visual_block_type="ja_grammar_board",
            visual_content=_grammar_board(section),
            start_time_seconds=start,
            narration_text=narration,
            grammar_points=_grammar_cards(section),
        )

    def _recap_segment(self, order, start, raw, context, title, goal, narration) -> dict | None:
        highlight_words = self._normalize_recap_words(raw.get("highlight_words"), context)
        grammar_points = self._recap_grammar_points(context)
        notes = _text(raw.get("visual_notes") or raw.get("notes")) or "把这些句型和表达连起来，就是本课的核心骨架。"
        return _segment(
            order=order,
            segment_type="recap",
            template_name="lesson_recap",
            title=title or "本课总结",
            teaching_goal=goal or "回顾本课最重要的句型、助词和固定表达。",
            duration_seconds=_duration(raw.get("estimated_duration_seconds"), 24.0),
            visual_block_type="recap_summary",
            visual_content={
                "main_title": "本课重点回顾",
                "focus_text": "Key Phrases Review",
                "highlight_words": highlight_words,
                "grammar_points": grammar_points,
                "notes": notes,
            },
            start_time_seconds=start,
            narration_text=narration,
            highlight_words=highlight_words,
            grammar_points=grammar_points,
        )

    def _auto_recap_segment(self, order, start, metadata, context) -> dict | None:
        highlight_words = self._normalize_recap_words([], context)
        if not highlight_words:
            return None
        sample = "、".join(f"[ja:{item['word']}]" for item in highlight_words[:4] if item.get("word"))
        narration = (
            f"最后我们快速回顾一下本课重点。今天最需要记住的是：{sample}。"
            "先把这些表达读顺，再回到例文和会话里反复听，下一课会继续用到这些基础结构。"
        )
        raw = {
            "segment_title": "本课总结",
            "teaching_goal": "回顾本课最重要的句型、助词和固定表达。",
            "highlight_words": highlight_words,
            "estimated_duration_seconds": 24,
        }
        return self._recap_segment(order, start, raw, context, "本课总结", raw["teaching_goal"], narration)

    def _normalize_recap_words(self, words, context) -> list[dict]:
        normalized: list[dict] = []
        if isinstance(words, list):
            for item in words:
                if not isinstance(item, dict):
                    continue
                word = _first_text(item.get("word"), item.get("term"), item.get("text"))
                if not word:
                    continue
                normalized.append({
                    "word": word,
                    "pinyin": _first_text(item.get("pinyin"), item.get("reading"), item.get("romaji")),
                    "translation": _first_text(item.get("translation"), item.get("english"), item.get("definition")),
                })
                if len(normalized) >= 6:
                    return normalized

        candidates = []
        candidates.extend(context.get("sentence_patterns") or [])
        candidates.extend(context.get("vocabulary") or [])
        candidates.extend(context.get("display_only_vocabulary") or [])
        for item in candidates:
            if not isinstance(item, dict):
                continue
            word = _recap_word_from_item(item)
            if not word:
                continue
            if word["word"] in {existing["word"] for existing in normalized}:
                continue
            normalized.append(word)
            if len(normalized) >= 6:
                break
        return normalized

    def _recap_grammar_points(self, context) -> list[dict]:
        points: list[dict] = []
        for section in context.get("grammar_sections") or []:
            if not isinstance(section, dict):
                continue
            pattern = _first_text(section.get("title"))
            if not pattern:
                examples = section.get("examples") if isinstance(section.get("examples"), list) else []
                if examples and isinstance(examples[0], dict):
                    pattern = _first_text(examples[0].get("text"))
            if not pattern:
                continue
            points.append({
                "pattern": pattern,
                "explanation_en": _first_text(section.get("explanation")),
            })
            if len(points) >= 4:
                break
        return points
