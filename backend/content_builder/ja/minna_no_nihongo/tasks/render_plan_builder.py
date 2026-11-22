from __future__ import annotations

try:
    from content_builder.ja.minna_no_nihongo.tasks.teaching_flow_builder import split_vocabulary_by_section
except ImportError:
    from content_builder.ja.minna_no_nihongo.tasks.teaching_flow_builder import split_vocabulary_by_section


RENDER_PLAN_VERSION = "mnn_golden_slide_v1"


def _timeline_block(duration_seconds: float, block_type: str, content: dict) -> dict:
    return {
        "block_type": block_type,
        "start_time_seconds": 0.0,
        "end_time_seconds": round(duration_seconds, 2),
        "duration_seconds": round(duration_seconds, 2),
        "content": content,
    }


def _timeline_blocks(duration_seconds: float, blocks: list[dict]) -> list[dict]:
    normalized = []
    cursor = 0.0
    total_weight = sum(float(block.get("weight", 1.0) or 1.0) for block in blocks) or 1.0
    for block in blocks:
        weight = float(block.get("weight", 1.0) or 1.0)
        block_duration = round(duration_seconds * weight / total_weight, 2)
        normalized.append({
            "block_type": block.get("block_type") or "content",
            "start_time_seconds": round(cursor, 2),
            "end_time_seconds": round(cursor + block_duration, 2),
            "duration_seconds": block_duration,
            "content": block.get("content") if isinstance(block.get("content"), dict) else {},
        })
        cursor += block_duration
    return normalized


def _segment(
    *,
    order: int,
    segment_type: str,
    template_name: str,
    title: str,
    teaching_goal: str,
    duration_seconds: float,
    visual_block_type: str | None = None,
    visual_content: dict | None = None,
    visual_blocks: list[dict] | None = None,
    start_time_seconds: float,
    narration_text: str = "",
    highlight_words: list | None = None,
    grammar_points: list | None = None,
) -> dict:
    duration_seconds = round(duration_seconds, 2)
    start_time_seconds = round(start_time_seconds, 2)
    return {
        "segment_id": order,
        "segment_order": order,
        "segment_type": segment_type,
        "template_name": template_name,
        "segment_title": title,
        "teaching_goal": teaching_goal,
        "narration_track": {
            "mode": "voice_over",
            "script": narration_text,
            "subtitle_zh": narration_text,
            "subtitle_en": narration_text,
        },
        "visual_blocks": (
            _timeline_blocks(duration_seconds, visual_blocks)
            if visual_blocks
            else [_timeline_block(duration_seconds, visual_block_type or "content", visual_content or {})]
        ),
        "highlight_words": highlight_words or [],
        "grammar_points": grammar_points or [],
        "start_time_seconds": start_time_seconds,
        "duration_seconds": duration_seconds,
        "end_time_seconds": round(start_time_seconds + duration_seconds, 2),
    }


def _translation(item: dict) -> str:
    return (item.get("translation") or item.get("definition") or "").strip()


def _reading(item: dict) -> str:
    return (item.get("reading") or item.get("romaji") or "").strip()


def _term(item: dict) -> str:
    return (item.get("term") or item.get("word") or item.get("text") or "").strip()


def _surface_set(items: list[dict]) -> set[str]:
    surfaces: set[str] = set()
    for item in items or []:
        if not isinstance(item, dict):
            continue
        text = (item.get("text") or "").strip()
        if text:
            surfaces.add(text)
        for token in item.get("tokens") or []:
            if isinstance(token, dict) and (token.get("surface") or "").strip():
                surfaces.add(token["surface"].strip())
    return surfaces


def _sample_terms(items: list[dict], limit: int = 3) -> list[str]:
    terms: list[str] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        term = _term(item)
        if term and term not in terms:
            terms.append(term)
        if len(terms) >= limit:
            break
    return terms


def _contains_any(texts: set[str], needles: set[str]) -> bool:
    return any(needle in texts for needle in needles)


def _pattern_note(pattern: dict) -> str:
    text = (pattern.get("text") or "").strip()
    surfaces = _surface_set([pattern])
    if "じゃ" in text or "ありません" in text:
        return "这里把 N は N です 变成否定句，じゃありません 是口语里常见的礼貌否定。"
    if "ですか" in text or "か" in surfaces:
        return "句末加 か 就变成疑问句；は 仍然提示主题，读作 わ。"
    if "も" in surfaces:
        return "も 表示“也”，会替换主题后的 は，用来说明前后两个人或事物相同。"
    if "さん" in surfaces:
        return "さん 接在人名后表示礼貌称呼，介绍别人时通常保留。"
    if "です" in surfaces or text.endswith("です。"):
        return "这是最基础的名词判断句：N1 は N2 です，用来介绍身份、职业或事实。"
    return "先抓住句子的整体框架，再观察助词和句末表达。"


def _sentence_stack_note(items: list[dict], *, mode: str) -> str:
    surfaces = _surface_set(items)
    texts = [(item.get("text") or "").strip() for item in items if isinstance(item, dict)]
    if mode == "dialogue":
        speakers = []
        for item in items:
            speaker = (item.get("speaker") or "").strip() if isinstance(item, dict) else ""
            if speaker and speaker not in speakers:
                speakers.append(speaker)
        if _contains_any(surfaces, {"こちら", "はじめまして", "どうぞよろしく"}):
            return "这一段是在正式介绍人物；こちらは 用来把身边的人介绍给对方。"
        if speakers:
            return f"这一页注意说话人转换：{'、'.join(speakers[:3])}。先听语气，再跟读整句。"
        return "会话里先确认场景和说话人，再跟读每一句的语气。"
    if any("[" in text and "]" in text for text in texts):
        return "方括号里的主语在自然对话中常省略；理解时补出来，跟读时读未省略的日语。"
    if _contains_any(surfaces, {"か"}):
        return "这些例句在练习判断句问答：问题用 か，回答常省略已经明确的主语。"
    if _contains_any(surfaces, {"も"}):
        return "这里的重点是 も，表示“也”；它会接在主题位置，说明两者情况相同。"
    if _contains_any(surfaces, {"じゃ", "ありません"}):
        return "这一组例句练习否定回答；じゃありません 是口语里常用的礼貌否定。"
    return "例文按一句一卡拆开。先看中文意思，再回到日语原句跟读。"


def _vocab_note(items: list[dict], *, group: str) -> str:
    terms = _sample_terms(items, 3)
    labels = {(_term(item), (item.get("part_of_speech") or item.get("category") or "").strip()) for item in items if isinstance(item, dict)}
    pos_values = {label for _, label in labels if label}
    term_set = {term for term, _ in labels if term}

    if group == "display_only":
        category_values = {
            (item.get("category") or "").strip()
            for item in items
            if isinstance(item, dict) and (item.get("category") or "").strip()
        }
        if category_values and category_values <= {"person_name"}:
            return f"{'、'.join(terms)} 是人名；会话里认得即可。"
        if category_values and category_values <= {"organization_name", "company_name"}:
            return f"{'、'.join(terms)} 是机构名；听到时知道指代谁。"
        return f"{'、'.join(terms)} 是专名；认得即可。"

    if any(term.startswith("〜") for term in term_set):
        suffixes = [term for term in term_set if term.startswith("〜")][:2]
        return f"{'、'.join(suffixes)} 接在名词后面，一起读。"
    if {"代名詞", "代词"} & pos_values:
        return f"{'、'.join(terms)} 是代词；先认清指代。"
    if {"感動詞", "感叹词"} & pos_values:
        return f"{'、'.join(terms)} 是寒暄/应答；听到要会接。"
    if {"名詞", "名词"} & pos_values and any("員" in term or "者" in term or "生" in term for term in term_set):
        return f"{'、'.join(terms)} 多和身份、职业有关。"
    if group == "supplementary":
        return f"{'、'.join(terms)} 会在练习里出现。"
    return f"{'、'.join(terms)} 是这一页的核心词。"


def _vocab_footer(items: list[dict], *, group: str) -> str:
    if group == "display_only":
        return "知道它是人名、地名或机构名即可。"
    review_count = sum(1 for item in items if isinstance(item, dict) and item.get("memory_status") == "review")
    if review_count:
        return f"{review_count} 个复现词，重点看新用法。"
    if group == "supplementary":
        return "重点是见到能懂，之后会在练习里反复遇到。"
    return "先读假名，再把词义和课文场景连起来。"


def _line_card(item: dict, *, prefix: str = "") -> dict:
    text = (item.get("text") or item.get("term") or item.get("word") or "").strip()
    if prefix:
        text = f"{prefix}：{text}"
    return {
        "word": text,
        "pinyin": _reading(item),
        "translation": _translation(item),
        "character_insight_en": (item.get("part_of_speech") or item.get("category") or "").strip(),
    }


def _clean_vocab_key(value: str) -> str:
    return (
        str(value or "")
        .strip()
        .replace("〜", "")
        .replace("~", "")
        .replace("・", "")
    )


def _vocab_lookup(vocabulary: list[dict]) -> dict[str, dict]:
    lookup: dict[str, dict] = {}
    for item in vocabulary or []:
        if not isinstance(item, dict):
            continue
        for key in (
            item.get("term"),
            item.get("word"),
            item.get("reading"),
            item.get("romaji"),
        ):
            cleaned = _clean_vocab_key(str(key or ""))
            if cleaned and cleaned not in lookup:
                lookup[cleaned] = item
    return lookup


def _is_punctuation_token(token: dict) -> bool:
    return (token.get("surface") or "").strip() in {"。", "、", "？", "?", "！", "!", "[", "]"}


def _ja_focus_tokens(item: dict, vocabulary: list[dict] | None = None) -> list[dict]:
    tokens = item.get("tokens") if isinstance(item.get("tokens"), list) else []
    normalized = []
    for token in tokens:
        if not isinstance(token, dict):
            continue
        surface = (token.get("surface") or "").strip()
        if not surface:
            continue
        normalized.append({
            "surface": surface,
            "reading": (token.get("reading") or "").strip(),
            "romaji": (token.get("romaji") or "").strip(),
            "pos": (token.get("pos") or "").strip(),
            "highlight": bool(token.get("highlight")),
        })
    if not vocabulary or len(normalized) < 2:
        return normalized

    vocab = _vocab_lookup(vocabulary)
    merged: list[dict] = []
    index = 0
    while index < len(normalized):
        current = normalized[index]
        if _is_punctuation_token(current):
            merged.append(current)
            index += 1
            continue

        best: dict | None = None
        best_end = index + 1
        for end in range(min(len(normalized), index + 5), index + 1, -1):
            window = normalized[index:end]
            if any(_is_punctuation_token(token) for token in window):
                continue
            surface = "".join(token.get("surface", "") for token in window)
            reading = "".join(token.get("reading", "") for token in window)
            if len(surface) <= len(current.get("surface", "")):
                continue
            vocab_item = vocab.get(_clean_vocab_key(surface)) or vocab.get(_clean_vocab_key(reading))
            if not vocab_item:
                continue
            best = {
                "surface": surface,
                "reading": reading or (vocab_item.get("reading") or "").strip(),
                "romaji": (vocab_item.get("romaji") or "").strip(),
                "pos": (vocab_item.get("part_of_speech") or window[0].get("pos") or "").strip(),
                "highlight": any(token.get("highlight") for token in window),
            }
            best_end = end
            break

        if best:
            merged.append(best)
            index = best_end
        else:
            merged.append(current)
            index += 1

    return merged


def _ja_grammar_hint(surface: str, reading: str, pos: str) -> str:
    if surface == "は":
        return "主题助词；这里读作 わ。"
    if surface == "も":
        return "表示“也”，会替换主题后的 は。"
    if surface == "か":
        return "句末疑问助词，相当于把句子变成问题。"
    if surface == "です":
        return "礼貌判断句的句末，相当于“是”。"
    if surface == "じゃ":
        return "和 ありません 组成口语礼貌否定。"
    if surface == "ありません":
        return "礼貌否定，表示“不是 / 没有”。"
    if pos in {"助詞", "助词"}:
        return "助词决定词和词之间的关系。"
    if reading and reading != surface:
        return "先把读音和词义连起来，再放回整句。"
    return ""


_FOUNDATION_REVIEW_SURFACES = {"は", "です"}
_COMMON_PARTICLE_SURFACES = {"は", "も", "か", "の", "へ", "を", "に", "で", "と"}


def _ja_pattern_highlights(pattern: dict, vocabulary: list[dict], limit: int = 3) -> list[dict]:
    vocab = _vocab_lookup(vocabulary)
    highlights: list[dict] = []
    seen: set[str] = set()
    tokens = _ja_focus_tokens(pattern, vocabulary)

    def add_from_token(token: dict) -> None:
        if len(highlights) >= limit:
            return
        surface = (token.get("surface") or "").strip()
        if not surface or surface in {"。", "、", "？", "!", "！", "?", "[", "]"}:
            return
        key = _clean_vocab_key(surface)
        if key in seen:
            return
        reading = (token.get("reading") or "").strip()
        pos = (token.get("pos") or "").strip()
        vocab_item = (
            vocab.get(_clean_vocab_key(surface))
            or vocab.get(_clean_vocab_key(reading))
        )
        translation = _translation(vocab_item) if isinstance(vocab_item, dict) else ""
        explanation = _ja_grammar_hint(surface, reading, pos)
        if not translation and not explanation:
            return
        seen.add(key)
        highlights.append({
            "word": surface,
            "pinyin": reading,
            "translation": translation or "语法焦点",
            "explanation": explanation,
            "part_of_speech": pos,
        })

    lesson_specific_tokens = [
        token for token in tokens
        if (token.get("surface") or "").strip() not in _FOUNDATION_REVIEW_SURFACES
    ]
    for token in lesson_specific_tokens:
        if token.get("highlight"):
            add_from_token(token)
    for token in lesson_specific_tokens:
        if len(highlights) >= limit:
            break
        surface = (token.get("surface") or "").strip()
        pos = (token.get("pos") or "").strip()
        if pos in {"名詞", "名词", "代名詞", "代词", "接尾辞", "表現"} or surface in {"じゃ", "ありません"}:
            add_from_token(token)
    for token in lesson_specific_tokens:
        if len(highlights) >= limit:
            break
        surface = (token.get("surface") or "").strip()
        if surface in _COMMON_PARTICLE_SURFACES:
            add_from_token(token)
    if len(highlights) >= 2:
        return highlights
    for token in tokens:
        if len(highlights) >= limit:
            break
        surface = (token.get("surface") or "").strip()
        if surface in _FOUNDATION_REVIEW_SURFACES:
            add_from_token(token)
    return highlights


def _vocab_card(item: dict) -> dict:
    return {
        "term": (item.get("term") or item.get("word") or "").strip(),
        "reading": _reading(item),
        "romaji": (item.get("romaji") or "").strip(),
        "translation": _translation(item),
        "part_of_speech": (item.get("part_of_speech") or item.get("category") or "").strip(),
        "category": (item.get("category") or "").strip(),
        "memory_status": (item.get("memory_status") or "").strip(),
    }


def _vocab_board(items: list[dict], *, group: str, heading: str, note: str, footer: str = "") -> dict:
    return {
        "group": group,
        "heading": heading,
        "note": note,
        "footer": footer,
        "items": [_vocab_card(item) for item in items if isinstance(item, dict)],
    }


def _sentence_card(item: dict, *, speaker: str = "", vocabulary: list[dict] | None = None) -> dict:
    return {
        "speaker": (speaker or item.get("speaker") or "").strip(),
        "text": (item.get("text") or "").strip(),
        "reading": _reading(item),
        "translation": _translation(item),
        "tokens": _ja_focus_tokens(item, vocabulary or []),
    }


def _chunk(items: list, size: int) -> list[list]:
    return [items[index:index + size] for index in range(0, len(items), size)]


def _first_pattern_text(section: dict) -> str:
    patterns = section.get("patterns") if isinstance(section.get("patterns"), list) else []
    for pattern in patterns:
        if isinstance(pattern, dict) and (pattern.get("text") or "").strip():
            return pattern["text"].strip()
    return (section.get("title") or "").strip()


def _grammar_cards(section: dict) -> list[dict]:
    cards = []
    patterns = section.get("patterns") if isinstance(section.get("patterns"), list) else []
    for pattern in patterns[:3]:
        if not isinstance(pattern, dict):
            continue
        text = (pattern.get("text") or "").strip()
        if text:
            cards.append({
                "pattern": text,
                "pattern_pinyin": "",
                "explanation_en": (pattern.get("translation") or "").strip(),
            })
    examples = section.get("examples") if isinstance(section.get("examples"), list) else []
    for example in examples[: max(0, 4 - len(cards))]:
        if not isinstance(example, dict):
            continue
        text = (example.get("text") or "").strip()
        if text:
            cards.append({
                "pattern": text,
                "pattern_pinyin": (example.get("reading") or "").strip(),
                "explanation_en": (example.get("translation") or "").strip(),
            })
    return cards[:4]


def _grammar_board(section: dict) -> dict:
    patterns = section.get("patterns") if isinstance(section.get("patterns"), list) else []
    examples = section.get("examples") if isinstance(section.get("examples"), list) else []
    usage_notes = section.get("usage_notes") if isinstance(section.get("usage_notes"), list) else []
    common_mistakes = section.get("common_mistakes") if isinstance(section.get("common_mistakes"), list) else []
    return {
        "title": (section.get("title") or "").strip(),
        "explanation": (section.get("explanation") or "").strip(),
        "patterns": [
            {
                "text": (pattern.get("text") or "").strip(),
                "translation": (pattern.get("translation") or "").strip(),
            }
            for pattern in patterns
            if isinstance(pattern, dict) and (pattern.get("text") or "").strip()
        ],
        "examples": [
            {
                "text": (example.get("text") or "").strip(),
                "reading": (example.get("reading") or "").strip(),
                "translation": (example.get("translation") or "").strip(),
                "tokens": _ja_focus_tokens(example),
            }
            for example in examples
            if isinstance(example, dict) and (example.get("text") or "").strip()
        ],
        "usage_notes": [str(note).strip() for note in usage_notes if str(note).strip()],
        "common_mistakes": [str(note).strip() for note in common_mistakes if str(note).strip()],
    }


class MinnaNoNihongoRenderPlanBuilder:
    def run(self, metadata: dict, course_content: dict, existing_plan: dict | None = None) -> dict:
        if self._can_reuse_existing_plan(existing_plan):
            explanation = existing_plan.get("explanation")
            if isinstance(explanation, dict) and isinstance(explanation.get("segments"), list):
                return existing_plan

        title = metadata.get("title_localized") or metadata.get("title") or ""
        sentence_patterns = course_content.get("sentence_patterns") or []
        example_sentences = course_content.get("example_sentences") or []
        dialogue = course_content.get("dialogue") or {}
        vocabulary = course_content.get("vocabulary") or []
        display_only_vocabulary = course_content.get("display_only_vocabulary") or []
        grammar_sections = course_content.get("grammar_sections") or []
        core_vocabulary, supplementary_vocabulary = split_vocabulary_by_section(vocabulary)

        segments = []
        cursor = 0.0

        def add_segment(**kwargs) -> None:
            nonlocal cursor
            segment = _segment(
                order=len(segments) + 1,
                start_time_seconds=cursor,
                **kwargs,
            )
            cursor = segment["end_time_seconds"]
            segments.append(segment)

        if sentence_patterns:
            for index, pattern in enumerate(sentence_patterns, start=1):
                focus_text = (pattern.get("text") or "").strip()
                add_segment(
                    segment_type="line_walkthrough",
                    template_name="ja_line_focus",
                    title=f"文型 {index}",
                    teaching_goal="建立本课核心句型。",
                    duration_seconds=9.0,
                    visual_blocks=[
                        {
                            "block_type": "hero_line",
                            "content": {
                                "focus_text": focus_text,
                                "focus_pinyin": _reading(pattern),
                                "focus_gloss_en": _translation(pattern),
                                "tokens": _ja_focus_tokens(pattern, vocabulary),
                            },
                            "weight": 0.62,
                        },
                        {
                            "block_type": "teaching_points",
                            "content": {
                                "notes": _pattern_note(pattern),
                                "highlight_words": _ja_pattern_highlights(pattern, vocabulary),
                            },
                            "weight": 0.38,
                        },
                    ],
                    narration_text="先看这个基本句型。读日语时不要急着逐词翻译，先抓住句子的框架。",
                )
        if example_sentences:
            for page, items in enumerate(_chunk(example_sentences, 3), start=1):
                add_segment(
                    segment_type="sentence_focus",
                    template_name="ja_sentence_stack",
                    title=f"例文 {page}",
                    teaching_goal="用例句理解句型的真实问答方式。",
                    duration_seconds=max(12.0, len(items) * 3.5),
                    visual_blocks=[
                        {
                            "block_type": "ja_sentence_stack",
                            "content": {
                                "mode": "examples",
                                "note": _sentence_stack_note(items, mode="examples"),
                                "lines": [_sentence_card(item, vocabulary=vocabulary) for item in items],
                            },
                            "weight": 1.0,
                        },
                    ],
                    narration_text="现在看例文。每张卡片是一句日语，注意回答里省略的主语和助词。",
                )
        if dialogue.get("lines"):
            for page, lines in enumerate(_chunk(dialogue.get("lines") or [], 3), start=1):
                add_segment(
                    segment_type="dialogue_focus",
                    template_name="ja_sentence_stack",
                    title=f"{dialogue.get('title_localized') or dialogue.get('title') or '会话'} {page}",
                    teaching_goal="串起本课对话，建立听读输入。",
                    duration_seconds=max(12.0, len(lines) * 4.0),
                    visual_blocks=[
                        {
                            "block_type": "ja_sentence_stack",
                            "content": {
                                "mode": "dialogue",
                                "note": _sentence_stack_note(lines, mode="dialogue"),
                                "lines": [_sentence_card(line, vocabulary=vocabulary) for line in lines],
                            },
                            "weight": 1.0,
                        },
                    ],
                    narration_text="接下来读会话。先确认是谁在说话，再跟读每一句的语气。",
                )
        if core_vocabulary:
            for page, items in enumerate(_chunk(core_vocabulary, 4), start=1):
                add_segment(
                    segment_type="vocabulary_focus",
                    template_name="ja_vocab_board",
                    title=f"词汇 {page}",
                    teaching_goal="掌握本课主线词汇。",
                    duration_seconds=max(12.0, len(items) * 2.2),
                    visual_blocks=[
                        {
                            "block_type": "ja_vocab_board",
                            "content": _vocab_board(
                                items,
                                group="core",
                                heading="主线词汇",
                                note=_vocab_note(items, group="core"),
                                footer=_vocab_footer(items, group="core"),
                            ),
                            "weight": 1.0,
                        },
                    ],
                    narration_text="这些是本课主线词汇。先看假名读音，再看中文意思。",
                )
        if grammar_sections:
            for index, section in enumerate(grammar_sections, start=1):
                board = _grammar_board(section)
                add_segment(
                    segment_type="grammar_focus",
                    template_name="ja_grammar_board",
                    title=f"语法 {index}",
                    teaching_goal="解释本课句型和语用限制。",
                    duration_seconds=14.0,
                    visual_blocks=[
                        {
                            "block_type": "ja_grammar_board",
                            "content": board,
                            "weight": 1.0,
                        },
                    ],
                    narration_text=f"这个语法点是：{(section.get('title') or '').strip()}。先看结构，再看例句。",
                    grammar_points=_grammar_cards(section),
                )
        if supplementary_vocabulary:
            for page, items in enumerate(_chunk(supplementary_vocabulary, 4), start=1):
                add_segment(
                    segment_type="vocabulary_focus",
                    template_name="ja_vocab_board",
                    title=f"补充词汇 {page}",
                    teaching_goal="补充练习中会用到的可复习词汇。",
                    duration_seconds=max(12.0, len(items) * 2.0),
                    visual_blocks=[
                        {
                            "block_type": "ja_vocab_board",
                            "content": _vocab_board(
                                items,
                                group="supplementary",
                                heading="补充词汇",
                                note=_vocab_note(items, group="supplementary"),
                                footer=_vocab_footer(items, group="supplementary"),
                            ),
                            "weight": 1.0,
                        },
                    ],
                    narration_text="这些是补充词汇。它们常出现在练习里，也会作为复习素材。",
                )
        if display_only_vocabulary:
            for page, items in enumerate(_chunk(display_only_vocabulary, 4), start=1):
                add_segment(
                    segment_type="vocabulary_focus",
                    template_name="ja_vocab_board",
                    title=f"专名 {page}",
                    teaching_goal="展示人名、机构名等不进入复习的词。",
                    duration_seconds=max(10.0, len(items) * 1.8),
                    visual_blocks=[
                        {
                            "block_type": "ja_vocab_board",
                            "content": _vocab_board(
                                items,
                                group="display_only",
                                heading="专名识别",
                                note=_vocab_note(items, group="display_only"),
                                footer=_vocab_footer(items, group="display_only"),
                            ),
                            "weight": 1.0,
                        },
                    ],
                    narration_text="最后看专名。这些词只需要在课文里认得，不会作为复习题反复考。",
                )

        return {
            "explanation": {
                "lesson_id": metadata.get("lesson_id"),
                "course_id": metadata.get("course_id"),
                "lesson_title": title,
                "target_audience": "Chinese speakers learning Japanese",
                "video_style": {
                    "presenter_mode": "voice_over",
                    "teaching_style": "structured beginner Japanese lesson",
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
                    "plan_version": RENDER_PLAN_VERSION,
                    "recommended_renderer": "static_teaching_slide_deck",
                    "remarks": "Japanese render plan generated from lesson001 golden slide structure.",
                },
            }
        }

    def _can_reuse_existing_plan(self, existing_plan: dict | None) -> bool:
        if not isinstance(existing_plan, dict):
            return False
        explanation = existing_plan.get("explanation")
        if not isinstance(explanation, dict):
            return False
        segments = explanation.get("segments")
        if not isinstance(segments, list) or not segments:
            return False
        notes = explanation.get("renderer_notes") if isinstance(explanation.get("renderer_notes"), dict) else {}
        if notes.get("plan_version") == RENDER_PLAN_VERSION:
            return True
        return self._looks_like_lesson001_golden_plan(explanation)

    def _looks_like_lesson001_golden_plan(self, explanation: dict) -> bool:
        lesson_id = str(explanation.get("lesson_id") or "").strip()
        if lesson_id not in {"1", "001"}:
            return False
        segments = explanation.get("segments")
        if not isinstance(segments, list) or len(segments) < 30:
            return False
        template_names = {
            (segment.get("template_name") or "").strip()
            for segment in segments
            if isinstance(segment, dict)
        }
        allowed = {"ja_line_focus", "ja_sentence_stack", "ja_vocab_board", "ja_grammar_board"}
        return bool(template_names) and template_names <= allowed and {"ja_line_focus", "ja_sentence_stack"} <= template_names
