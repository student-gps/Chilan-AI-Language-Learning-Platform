from __future__ import annotations


def normalize_teaching_list(items) -> list[dict]:
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def split_vocabulary_by_section(vocabulary: list[dict]) -> tuple[list[dict], list[dict]]:
    core = []
    supplementary = []
    for item in vocabulary or []:
        if not isinstance(item, dict):
            continue
        if item.get("lesson_section") == "supplementary":
            supplementary.append(item)
        else:
            core.append(item)
    return core, supplementary


class MinnaNoNihongoTeachingFlowBuilder:
    def run(self, course_content: dict, teaching_materials: dict | None = None) -> dict:
        teaching_materials = teaching_materials if isinstance(teaching_materials, dict) else {}
        return {
            "lesson_flow": self.build_lesson_flow(
                course_content,
                normalize_teaching_list(teaching_materials.get("lesson_flow")),
            ),
            "pronunciation_notes": self.build_pronunciation_notes(
                course_content,
                normalize_teaching_list(teaching_materials.get("pronunciation_notes")),
            ),
            "usage_notes": normalize_teaching_list(teaching_materials.get("usage_notes")),
        }

    def build_pronunciation_notes(self, course_content: dict, existing_notes: list[dict]) -> list[dict]:
        notes = list(existing_notes)
        seen_titles = {
            (note.get("title") or note.get("key") or "").strip()
            for note in notes
            if isinstance(note, dict)
        }

        token_items = []
        token_items.extend(course_content.get("sentence_patterns") or [])
        token_items.extend(course_content.get("example_sentences") or [])
        token_items.extend(((course_content.get("dialogue") or {}).get("lines")) or [])
        particle_readings = {}
        for item in token_items:
            if not isinstance(item, dict):
                continue
            for token in item.get("tokens") or []:
                if not isinstance(token, dict):
                    continue
                surface = token.get("surface")
                reading = token.get("reading")
                if surface in {"は", "へ", "を"} and reading:
                    particle_readings[surface] = reading

        defaults = {
            "は": ("助词 は", "作主题助词时通常读作 わ。"),
            "へ": ("助词 へ", "表示方向时通常读作 え。"),
            "を": ("助词 を", "作宾格助词时通常读作 お。"),
        }
        for surface, reading in particle_readings.items():
            title, explanation = defaults[surface]
            if title in seen_titles:
                continue
            notes.append({
                "title": title,
                "surface": surface,
                "reading": reading,
                "explanation": explanation,
            })
            seen_titles.add(title)
        return notes

    def build_lesson_flow(self, course_content: dict, existing_flow: list[dict]) -> list[dict]:
        if existing_flow:
            return existing_flow

        sentence_patterns = course_content.get("sentence_patterns") or []
        example_sentences = course_content.get("example_sentences") or []
        dialogue = course_content.get("dialogue") or {}
        grammar_sections = course_content.get("grammar_sections") or []
        display_only_vocabulary = course_content.get("display_only_vocabulary") or []
        core_vocabulary, supplementary_vocabulary = split_vocabulary_by_section(course_content.get("vocabulary") or [])

        flow = []
        if sentence_patterns:
            flow.append({
                "flow_id": "sentence_patterns",
                "kind": "sentence_patterns",
                "title": "文型",
                "title_localized": "文型",
                "items": sentence_patterns,
            })
        if example_sentences:
            flow.append({
                "flow_id": "example_sentences",
                "kind": "example_sentences",
                "title": "例文",
                "title_localized": "例句",
                "items": example_sentences,
            })
        if dialogue.get("lines"):
            flow.append({
                "flow_id": "dialogue",
                "kind": "dialogue",
                "title": dialogue.get("title") or "会話",
                "title_localized": dialogue.get("title_localized") or "会话",
                "lines": dialogue.get("lines") or [],
            })
        if core_vocabulary:
            flow.append({
                "flow_id": "core_vocabulary",
                "kind": "vocabulary",
                "title": "語彙",
                "title_localized": "词汇",
                "review_mode": "full",
                "items": core_vocabulary,
            })
        if grammar_sections:
            flow.append({
                "flow_id": "grammar",
                "kind": "grammar_sections",
                "title": "文法",
                "title_localized": "语法",
                "sections": grammar_sections,
            })
        if supplementary_vocabulary:
            flow.append({
                "flow_id": "supplementary_vocabulary",
                "kind": "vocabulary",
                "title": "補充語彙",
                "title_localized": "补充词汇",
                "review_mode": "full",
                "items": supplementary_vocabulary,
            })
        if display_only_vocabulary:
            flow.append({
                "flow_id": "display_only_vocabulary",
                "kind": "display_only_vocabulary",
                "title": "名前・固有名詞",
                "title_localized": "专名",
                "review_mode": "display_only",
                "items": display_only_vocabulary,
            })
        return flow
