from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path


PLACEHOLDER_TERMS = {"", "〜", "~", "N", "A", "B", "N1", "N2", "AかB"}
STABLE_SINGLE_KANJI_READING_ALIASES = {"私", "貴方", "誰"}


class MinnaNoNihongoVocabMemory:
    """Track learned Japanese vocabulary across Minna no Nihongo lessons."""

    def __init__(self, memory_dir: Path):
        self.memory_file = Path(memory_dir) / "vocab_memory" / "global_vocab_memory.json"
        self.global_vocab = self._load_memory()

    def annotate_lesson(self, lesson_data: dict) -> dict:
        annotated = deepcopy(lesson_data if isinstance(lesson_data, dict) else {})
        metadata = annotated.get("lesson_metadata") if isinstance(annotated.get("lesson_metadata"), dict) else {}
        lesson_id = self._safe_int(metadata.get("lesson_id"))
        course_id = metadata.get("course_id", "")
        lesson_slug = metadata.get("lesson_slug", "")
        content = annotated.get("course_content") if isinstance(annotated.get("course_content"), dict) else {}
        vocabulary = content.get("vocabulary") if isinstance(content.get("vocabulary"), list) else []

        counts = {"new": 0, "review": 0, "new_meaning": 0}
        for vocab in vocabulary:
            if not isinstance(vocab, dict):
                continue
            if not isinstance(vocab.get("example_sentence"), dict):
                example = self._find_example_for_vocab(vocab, content)
                if example:
                    vocab["example_sentence"] = example

            term_key = self._term_key(vocab)
            previous_usages = self._previous_usages(term_key, lesson_id)
            current_meaning = self._meaning_key(vocab)
            same_meaning = [
                usage for usage in previous_usages
                if self._meaning_key(usage) == current_meaning and current_meaning
            ]
            ordered_usages = same_meaning + [
                usage for usage in previous_usages
                if usage not in same_meaning
            ]

            if same_meaning:
                memory_status = "review"
                is_new_vocabulary = False
            elif previous_usages:
                memory_status = "new_meaning"
                is_new_vocabulary = True
            else:
                memory_status = "new"
                is_new_vocabulary = True

            counts[memory_status] += 1
            vocab["memory_status"] = memory_status
            vocab["is_new_vocabulary"] = is_new_vocabulary
            vocab["previous_lesson_ids"] = self._lesson_ids(ordered_usages)
            if ordered_usages:
                vocab["first_seen_lesson_id"] = self._lesson_ids(ordered_usages)[0]
                vocab["historical_usages"] = self._compact_usages(ordered_usages)
                vocab["historical_examples"] = [
                    usage["example"]
                    for usage in self._compact_usages(ordered_usages)
                    if isinstance(usage.get("example"), dict) and usage["example"].get("text")
                ][:3]
            vocab.setdefault("memory_context", {})
            vocab["memory_context"].update({
                "course_id": course_id,
                "lesson_slug": lesson_slug,
            })

        diagnostics = annotated.setdefault("pipeline_diagnostics", {})
        diagnostics["vocab_memory"] = {
            "memory_file": str(self.memory_file),
            "new_count": counts["new"],
            "review_count": counts["review"],
            "new_meaning_count": counts["new_meaning"],
        }
        return annotated

    def save_lesson_vocabulary(self, lesson_data: dict) -> dict:
        full_dict = self._load_memory()
        metadata = lesson_data.get("lesson_metadata") if isinstance(lesson_data.get("lesson_metadata"), dict) else {}
        lesson_id = self._safe_int(metadata.get("lesson_id"))
        course_id = metadata.get("course_id", "")
        lesson_slug = metadata.get("lesson_slug", "")
        content = lesson_data.get("course_content") if isinstance(lesson_data.get("course_content"), dict) else {}
        vocabulary = content.get("vocabulary") if isinstance(content.get("vocabulary"), list) else []

        saved_count = 0
        for vocab in vocabulary:
            if not isinstance(vocab, dict):
                continue
            term = (vocab.get("term") or vocab.get("word") or "").strip()
            definition = (vocab.get("translation") or vocab.get("definition") or "").strip()
            if not term or not definition:
                continue
            term_key = self._term_key(vocab)
            entry = {
                "term": term,
                "reading": (vocab.get("reading") or "").strip(),
                "romaji": (vocab.get("romaji") or "").strip(),
                "part_of_speech": (vocab.get("part_of_speech") or "").strip(),
                "definition": definition,
                "translation": definition,
                "example": self._normalize_example(
                    vocab.get("example_sentence") or self._find_example_for_vocab(vocab, content)
                ),
                "lesson_id": lesson_id,
                "lesson_slug": lesson_slug,
                "course_id": course_id,
                "memory_status": (vocab.get("memory_status") or "new").strip(),
            }
            entries = full_dict.setdefault(term_key, [])
            if self._replace_same_lesson_usage(entries, entry):
                continue
            entries.append(entry)
            saved_count += 1

        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self.memory_file.write_text(
            json.dumps(full_dict, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.global_vocab = full_dict
        return {"saved_count": saved_count, "memory_file": str(self.memory_file)}

    def token_merge_vocabulary(self, lesson_id: int | None = None) -> list[dict]:
        """Return prior learned vocabulary entries safe for token merging.

        This is a long-lived historical lexicon, not a recent-lesson window. It
        keeps low-risk whole words and stable reading aliases, while excluding
        pure numbers, placeholders, and ambiguous single-character terms.
        """
        items = []
        seen = set()
        for usages in self.global_vocab.values():
            if not isinstance(usages, list):
                continue
            for usage in usages:
                if not isinstance(usage, dict):
                    continue
                usage_lesson_id = self._safe_int(usage.get("lesson_id"))
                if lesson_id is not None and usage_lesson_id is not None and usage_lesson_id >= lesson_id:
                    continue
                for item in self._token_merge_entries_for_usage(usage):
                    key = ((item.get("term") or "").casefold(), item.get("reading") or "")
                    if key in seen:
                        continue
                    seen.add(key)
                    items.append(item)
        return items

    def _token_merge_entries_for_usage(self, usage: dict) -> list[dict]:
        term = (usage.get("term") or "").strip()
        reading = (usage.get("reading") or "").strip()
        if not term:
            return []

        base = {
            "romaji": (usage.get("romaji") or "").strip(),
            "part_of_speech": (usage.get("part_of_speech") or "").strip(),
            "translation": (usage.get("translation") or usage.get("definition") or "").strip(),
            "lesson_section": "memory",
        }
        entries = []
        surface = self._normalize_token_surface(term)
        if self._safe_historical_surface(surface):
            entries.append({
                **base,
                "term": surface,
                "word": surface,
                "reading": self._normalize_reading_for_surface(reading, term),
            })

        reading_surface = self._normalize_token_surface(reading)
        if self._safe_historical_reading_alias(term, reading_surface):
            entries.append({
                **base,
                "term": reading_surface,
                "word": reading_surface,
                "reading": reading_surface,
            })
        return entries

    def _normalize_token_surface(self, value: str) -> str:
        normalized = "".join(str(value or "").split()).strip()
        while normalized.startswith(("〜", "~")):
            normalized = normalized[1:]
        return normalized

    def _normalize_reading_for_surface(self, reading: str, term: str) -> str:
        normalized = self._normalize_token_surface(reading)
        if normalized:
            return normalized
        return self._normalize_token_surface(term)

    def _safe_historical_surface(self, surface: str) -> bool:
        if not surface or surface in PLACEHOLDER_TERMS:
            return False
        if re.fullmatch(r"\d+", surface):
            return False
        if re.fullmatch(r"[A-Za-z]\d*", surface):
            return False
        if len(surface) < 2:
            return False
        if not any(self._is_japanese_char(char) or char.isalnum() for char in surface):
            return False
        return True

    def _safe_historical_reading_alias(self, term: str, reading: str) -> bool:
        if not reading or reading in PLACEHOLDER_TERMS:
            return False
        if reading == self._normalize_token_surface(term):
            return False
        if not re.fullmatch(r"[\u3040-\u30ffー]+", reading):
            return False
        if len(reading) >= 3:
            return True
        return term in STABLE_SINGLE_KANJI_READING_ALIASES

    def _is_japanese_char(self, char: str) -> bool:
        return (
            "\u3040" <= char <= "\u30ff"
            or "\u4e00" <= char <= "\u9fff"
            or char in {"ー", "・", "･"}
        )

    def _load_memory(self) -> dict:
        if not self.memory_file.exists():
            return {}
        try:
            data = json.loads(self.memory_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def _previous_usages(self, term_key: str, lesson_id: int | None) -> list[dict]:
        usages = self.global_vocab.get(term_key)
        if not isinstance(usages, list):
            return []
        previous = []
        for usage in usages:
            if not isinstance(usage, dict):
                continue
            usage_lesson_id = self._safe_int(usage.get("lesson_id"))
            if lesson_id is not None and usage_lesson_id == lesson_id:
                continue
            if lesson_id is not None and usage_lesson_id is not None and usage_lesson_id > lesson_id:
                continue
            previous.append(usage)
        return previous

    def _find_example_for_vocab(self, vocab: dict, content: dict) -> dict:
        term = (vocab.get("term") or vocab.get("word") or "").strip()
        if not term:
            return {}
        for source_section, lines in self._sentence_sources(content):
            for index, line in enumerate(lines, start=1):
                if not isinstance(line, dict):
                    continue
                text = (line.get("text") or "").strip()
                if term not in text:
                    continue
                return {
                    "text": text,
                    "reading": (line.get("reading") or "").strip(),
                    "romaji": (line.get("romaji") or "").strip(),
                    "translation": (line.get("translation") or "").strip(),
                    "source_section": source_section,
                    "source_ref": line.get("line_ref") or line.get("pattern_id") or index,
                }
        return {}

    def _sentence_sources(self, content: dict):
        yield "sentence_patterns", content.get("sentence_patterns") or []
        yield "example_sentences", content.get("example_sentences") or []
        dialogue = content.get("dialogue") if isinstance(content.get("dialogue"), dict) else {}
        yield "dialogue", dialogue.get("lines") or []

    def _compact_usages(self, usages: list[dict]) -> list[dict]:
        compact = []
        for usage in usages[:6]:
            compact.append({
                "lesson_id": usage.get("lesson_id"),
                "lesson_slug": usage.get("lesson_slug", ""),
                "definition": usage.get("definition") or usage.get("translation") or "",
                "reading": usage.get("reading", ""),
                "part_of_speech": usage.get("part_of_speech", ""),
                "example": self._normalize_example(usage.get("example")),
            })
        return compact

    def _lesson_ids(self, usages: list[dict]) -> list[int]:
        lesson_ids = []
        for usage in usages:
            lesson_id = self._safe_int(usage.get("lesson_id"))
            if lesson_id is not None and lesson_id not in lesson_ids:
                lesson_ids.append(lesson_id)
        return sorted(lesson_ids)

    def _normalize_example(self, example) -> dict:
        if not isinstance(example, dict):
            return {}
        return {
            "text": (example.get("text") or example.get("ja") or "").strip(),
            "reading": (example.get("reading") or "").strip(),
            "romaji": (example.get("romaji") or "").strip(),
            "translation": (example.get("translation") or example.get("definition") or "").strip(),
            "source_section": (example.get("source_section") or "").strip(),
            "source_ref": example.get("source_ref") or example.get("line_ref") or example.get("pattern_id"),
        }

    def _replace_same_lesson_usage(self, entries: list[dict], entry: dict) -> bool:
        meaning = self._meaning_key(entry)
        lesson_id = self._safe_int(entry.get("lesson_id"))
        for index, existing in enumerate(entries):
            if not isinstance(existing, dict):
                continue
            if self._safe_int(existing.get("lesson_id")) == lesson_id and self._meaning_key(existing) == meaning:
                entries[index] = entry
                return True
        return False

    def _term_key(self, item: dict) -> str:
        return " ".join((item.get("term") or item.get("word") or "").strip().split()).casefold()

    def _meaning_key(self, item: dict) -> str:
        return " ".join((item.get("definition") or item.get("translation") or "").strip().split()).casefold()

    def _safe_int(self, value) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
