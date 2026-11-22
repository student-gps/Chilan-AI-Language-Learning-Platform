from __future__ import annotations

import re
from functools import lru_cache


JA_PUNCTUATION = set("。、！？「」『』（）()[]【】・･…：；,.;!?")
PARTICLE_READINGS = {"は": "わ", "へ": "え", "を": "お"}
COUNTER_READINGS = {
    "階": {
        "1": "いっかい",
        "2": "にかい",
        "3": "さんがい",
        "4": "よんかい",
        "5": "ごかい",
        "6": "ろっかい",
        "7": "ななかい",
        "8": "はっかい",
        "9": "きゅうかい",
        "10": "じゅっかい",
        "何": "なんがい",
    },
    "歳": {
        "1": "いっさい",
        "2": "にさい",
        "3": "さんさい",
        "4": "よんさい",
        "5": "ごさい",
        "6": "ろくさい",
        "7": "ななさい",
        "8": "はっさい",
        "9": "きゅうさい",
        "10": "じゅっさい",
        "20": "はたち",
        "何": "なんさい",
    },
    "才": {
        "1": "いっさい",
        "2": "にさい",
        "3": "さんさい",
        "4": "よんさい",
        "5": "ごさい",
        "6": "ろくさい",
        "7": "ななさい",
        "8": "はっさい",
        "9": "きゅうさい",
        "10": "じゅっさい",
        "20": "はたち",
        "何": "なんさい",
    },
    "本": {
        "1": "いっぽん",
        "2": "にほん",
        "3": "さんぼん",
        "4": "よんほん",
        "5": "ごほん",
        "6": "ろっぽん",
        "7": "ななほん",
        "8": "はっぽん",
        "9": "きゅうほん",
        "10": "じゅっぽん",
        "何": "なんぼん",
    },
    "杯": {
        "1": "いっぱい",
        "2": "にはい",
        "3": "さんばい",
        "4": "よんはい",
        "5": "ごはい",
        "6": "ろっぱい",
        "7": "ななはい",
        "8": "はっぱい",
        "9": "きゅうはい",
        "10": "じゅっぱい",
        "何": "なんばい",
    },
    "分": {
        "1": "いっぷん",
        "2": "にふん",
        "3": "さんぷん",
        "4": "よんぷん",
        "5": "ごふん",
        "6": "ろっぷん",
        "7": "ななふん",
        "8": "はっぷん",
        "9": "きゅうふん",
        "10": "じゅっぷん",
        "何": "なんぷん",
    },
    "時": {
        "1": "いちじ",
        "2": "にじ",
        "3": "さんじ",
        "4": "よじ",
        "5": "ごじ",
        "6": "ろくじ",
        "7": "しちじ",
        "8": "はちじ",
        "9": "くじ",
        "10": "じゅうじ",
        "何": "なんじ",
    },
    "人": {
        "1": "ひとり",
        "2": "ふたり",
        "3": "さんにん",
        "4": "よにん",
        "5": "ごにん",
        "6": "ろくにん",
        "7": "ななにん",
        "8": "はちにん",
        "9": "きゅうにん",
        "10": "じゅうにん",
        "何": "なんにん",
    },
}
REGULAR_COUNTERS = {"円", "課", "番", "枚", "冊", "台", "個"}
COUNTER_SURFACES = set(COUNTER_READINGS) | REGULAR_COUNTERS
ORDINAL_COUNTERS = {"課", "番"}
COMMON_TOKEN_MERGES = {
    "おはようございます": {"reading": "おはようございます", "part_of_speech": "挨拶"},
    "はじめまして": {"reading": "はじめまして", "part_of_speech": "挨拶"},
    "いらっしゃいませ": {"reading": "いらっしゃいませ", "part_of_speech": "挨拶"},
    "すみません": {"reading": "すみません", "part_of_speech": "表現"},
    "ありません": {"reading": "ありません", "part_of_speech": "表現"},
    "あります": {"reading": "あります", "part_of_speech": "動詞"},
    "じゃ": {"reading": "じゃ", "part_of_speech": "助詞"},
    "ください": {"reading": "ください", "part_of_speech": "表現"},
    "お願いします": {"reading": "おねがいします", "part_of_speech": "表現"},
    "よろしくお願いします": {"reading": "よろしくおねがいします", "part_of_speech": "表現"},
    "こちらこそ": {"reading": "こちらこそ", "part_of_speech": "表現"},
    "です": {"reading": "です", "part_of_speech": "助動詞"},
    "ます": {"reading": "ます", "part_of_speech": "助動詞"},
    "ません": {"reading": "ません", "part_of_speech": "助動詞"},
    "そう": {"reading": "そう", "part_of_speech": "副詞"},
    "いくら": {"reading": "いくら", "part_of_speech": "疑問詞"},
}


def default_reading_for_surface(surface: str) -> str:
    if not surface or all(char in JA_PUNCTUATION for char in surface):
        return ""
    if surface in PARTICLE_READINGS:
        return PARTICLE_READINGS[surface]
    if re.fullmatch(r"[\u3040-\u30ffーA-Za-z0-9・]+", surface):
        return surface
    return ""


def katakana_to_hiragana(value: str) -> str:
    converted = []
    for char in value or "":
        codepoint = ord(char)
        if 0x30A1 <= codepoint <= 0x30F6:
            converted.append(chr(codepoint - 0x60))
        else:
            converted.append(char)
    return "".join(converted)


@lru_cache(maxsize=1)
def _load_janome_tokenizer():
    try:
        from janome.tokenizer import Tokenizer
    except ImportError:
        return None
    return Tokenizer()


def vocabulary_lookup(vocabulary: list[dict]) -> dict[str, dict]:
    lookup = {}
    for item in vocabulary or []:
        if not isinstance(item, dict):
            continue
        term = (item.get("term") or item.get("word") or "").strip()
        if term:
            _add_lookup_alias(lookup, term, item)
        reading = (item.get("reading") or item.get("kana") or "").strip()
        if reading and re.fullmatch(r"[\u3040-\u30ffー]+", reading):
            _add_lookup_alias(lookup, reading, item, overwrite=False)
    return lookup


def _add_lookup_alias(lookup: dict[str, dict], term: str, item: dict, overwrite: bool = True) -> None:
    variants = {term}
    compact = "".join(term.split())
    if compact:
        variants.add(compact)
    for variant in list(variants):
        if variant.startswith(("〜", "~")) and len(variant) > 1:
            variants.add(variant[1:])
    for variant in variants:
        if not variant:
            continue
        alias_item = item
        if variant != term:
            alias_item = dict(item)
            alias_item["term"] = variant
            alias_item["word"] = variant
            reading = (alias_item.get("reading") or alias_item.get("kana") or "").strip()
            if reading.startswith(("〜", "~")):
                alias_item["reading"] = reading[1:]
        if overwrite:
            lookup[variant] = alias_item
        else:
            lookup.setdefault(variant, alias_item)


def common_token_lookup() -> dict[str, dict]:
    return {
        term: {
            "term": term,
            "reading": values["reading"],
            "part_of_speech": values["part_of_speech"],
        }
        for term, values in COMMON_TOKEN_MERGES.items()
    }


class JapaneseReadingAnnotator:
    def __init__(self, morphological_tokenizer=None):
        self.morphological_tokenizer = morphological_tokenizer if morphological_tokenizer is not None else _load_janome_tokenizer()

    def normalize_token(
        self,
        token: dict | str,
        vocab_lookup: dict[str, dict],
        highlight_terms: set[str] | None = None,
    ) -> dict | None:
        if isinstance(token, str):
            surface = token.strip()
            raw = {}
        elif isinstance(token, dict):
            surface = (
                token.get("surface")
                or token.get("text")
                or token.get("term")
                or token.get("ja")
                or ""
            ).strip()
            raw = token
        else:
            return None

        if not surface:
            return None

        vocab_item = vocab_lookup.get(surface) or {}
        if surface in PARTICLE_READINGS:
            reading = PARTICLE_READINGS[surface]
        else:
            reading = (
                raw.get("reading")
                or raw.get("kana")
                or vocab_item.get("reading")
                or default_reading_for_surface(surface)
                or ""
            ).strip()
        romaji = (raw.get("romaji") or vocab_item.get("romaji") or "").strip()
        pos = (
            raw.get("pos")
            or raw.get("part_of_speech")
            or vocab_item.get("part_of_speech")
            or ""
        ).strip()
        active_highlight_terms = set(vocab_lookup.keys()) if highlight_terms is None else highlight_terms
        return {
            "surface": surface,
            "reading": reading,
            "romaji": romaji,
            "pos": pos,
            "highlight": bool(raw.get("highlight")) or surface in active_highlight_terms,
        }

    def tokenize_text(
        self,
        text: str,
        vocabulary: list[dict] | None = None,
        merge_vocabulary: list[dict] | None = None,
    ) -> list[dict]:
        learnable_lookup = vocabulary_lookup(vocabulary or [])
        merge_lookup = common_token_lookup()
        merge_lookup.update(vocabulary_lookup(merge_vocabulary or vocabulary or []))
        highlight_terms = set(learnable_lookup.keys())
        vocab_terms = sorted(merge_lookup.keys(), key=len, reverse=True)
        tokens = []
        buffer = ""

        def flush_buffer() -> None:
            nonlocal buffer
            tokens.extend(self._tokenize_segment(buffer, merge_lookup, vocab_terms, highlight_terms))
            buffer = ""

        for char in text or "":
            if char.isspace():
                continue
            if char in JA_PUNCTUATION and char not in {"・", "･"}:
                if buffer:
                    flush_buffer()
                token = self.normalize_token(char, merge_lookup, highlight_terms=highlight_terms)
                if token:
                    token["highlight"] = False
                    tokens.append(token)
                continue
            buffer += char
        if buffer:
            flush_buffer()
        return self.merge_number_counter_tokens(tokens)

    def _tokenize_segment(
        self,
        segment: str,
        merge_lookup: dict[str, dict],
        vocab_terms: list[str],
        highlight_terms: set[str],
    ) -> list[dict]:
        segment_tokens = []
        index = 0
        while index < len(segment):
            matched = self._match_term_at(segment, index, vocab_terms)
            if matched:
                token = self.normalize_token(matched, merge_lookup, highlight_terms=highlight_terms)
                if token:
                    segment_tokens.append(token)
                index += len(matched)
                continue

            next_match_index = self._next_term_match_index(segment, index + 1, vocab_terms)
            unknown = segment[index:next_match_index] if next_match_index is not None else segment[index:]
            segment_tokens.extend(self._tokenize_unknown_segment(unknown, merge_lookup, highlight_terms))
            index = next_match_index if next_match_index is not None else len(segment)
        return segment_tokens

    def _match_term_at(self, segment: str, index: int, vocab_terms: list[str]) -> str | None:
        for term in vocab_terms:
            if term and segment.startswith(term, index):
                return term
        return None

    def _next_term_match_index(self, segment: str, start_index: int, vocab_terms: list[str]) -> int | None:
        for index in range(start_index, len(segment)):
            if self._match_term_at(segment, index, vocab_terms):
                return index
        return None

    def _tokenize_unknown_segment(
        self,
        segment: str,
        merge_lookup: dict[str, dict],
        highlight_terms: set[str],
    ) -> list[dict]:
        if not segment:
            return []

        morph_tokens = self._morphological_tokens(segment)
        if morph_tokens:
            normalized = [
                token
                for token in (
                    self.normalize_token(raw_token, merge_lookup, highlight_terms=highlight_terms)
                    for raw_token in morph_tokens
                )
                if token
            ]
            if normalized and "".join(token["surface"] for token in normalized) == segment:
                return normalized

        fallback_tokens = []
        for char in segment:
            token = self.normalize_token(char, merge_lookup, highlight_terms=highlight_terms)
            if token:
                fallback_tokens.append(token)
        return fallback_tokens

    def _morphological_tokens(self, segment: str) -> list[dict]:
        tokenizer = self.morphological_tokenizer
        if tokenizer is None:
            return []

        if callable(tokenizer):
            raw_tokens = tokenizer(segment)
            return [token for token in raw_tokens or [] if isinstance(token, dict)]

        if not hasattr(tokenizer, "tokenize"):
            return []

        tokens = []
        try:
            raw_tokens = tokenizer.tokenize(segment)
        except Exception:
            return []
        for raw_token in raw_tokens:
            surface = (getattr(raw_token, "surface", "") or "").strip()
            if not surface:
                continue
            reading = (getattr(raw_token, "reading", "") or "").strip()
            if reading == "*":
                reading = ""
            if reading and not re.fullmatch(r"[\u30a0-\u30ffー]+", surface):
                reading = katakana_to_hiragana(reading)
            pos = ""
            part_of_speech = getattr(raw_token, "part_of_speech", "") or ""
            if part_of_speech:
                pos = str(part_of_speech).split(",")[0]
            tokens.append({
                "surface": surface,
                "reading": reading or default_reading_for_surface(surface),
                "pos": pos,
            })
        return tokens

    def merge_tokens(
        self,
        tokens: list[dict],
        merge_vocabulary: list[dict] | None = None,
        highlight_vocabulary: list[dict] | None = None,
    ) -> list[dict]:
        merge_lookup = common_token_lookup()
        merge_lookup.update(vocabulary_lookup(merge_vocabulary or []))
        if not tokens or not merge_lookup:
            return tokens

        highlight_terms = set(vocabulary_lookup(highlight_vocabulary or []).keys())
        merge_terms = [term for term in sorted(merge_lookup.keys(), key=len, reverse=True) if len(term) > 1]
        if not merge_terms:
            return tokens

        merged = []
        index = 0
        while index < len(tokens):
            token = tokens[index]
            if not isinstance(token, dict):
                index += 1
                continue
            surface = (token.get("surface") or "").strip()
            if not surface or surface in JA_PUNCTUATION:
                merged.append(token)
                index += 1
                continue

            match = self._match_merge_term(tokens, index, merge_terms)
            if not match:
                merged.append(token)
                index += 1
                continue

            term, end_index = match
            merged_token = self.normalize_token(term, merge_lookup, highlight_terms=highlight_terms)
            if merged_token:
                component_tokens = tokens[index:end_index]
                merged_token["highlight"] = (
                    term in highlight_terms
                    or any(bool(item.get("highlight")) for item in component_tokens if isinstance(item, dict))
                )
                merged.append(merged_token)
            index = end_index
        return merged

    def _match_merge_term(self, tokens: list[dict], start_index: int, merge_terms: list[str]) -> tuple[str, int] | None:
        candidates = [
            term
            for term in merge_terms
            if term.startswith((tokens[start_index].get("surface") or "").strip())
        ]
        if not candidates:
            return None

        combined = ""
        for end_index in range(start_index, len(tokens)):
            token = tokens[end_index]
            if not isinstance(token, dict):
                break
            surface = (token.get("surface") or "").strip()
            if not surface or (surface in JA_PUNCTUATION and surface not in {"・", "･"}):
                break
            combined += surface
            for term in candidates:
                if combined == term:
                    return term, end_index + 1
            if not any(term.startswith(combined) for term in candidates):
                break
        return None

    def merge_number_counter_tokens(self, tokens: list[dict]) -> list[dict]:
        if not tokens:
            return tokens

        merged = []
        index = 0
        while index < len(tokens):
            token = tokens[index]
            if not isinstance(token, dict):
                index += 1
                continue

            ordinal_match = self._match_ordinal_counter(tokens, index)
            if ordinal_match:
                merged.append(ordinal_match["token"])
                index = ordinal_match["end_index"]
                continue

            counter_match = self._match_number_counter(tokens, index)
            if counter_match:
                merged.append(counter_match["token"])
                index = counter_match["end_index"]
                continue

            merged.append(token)
            index += 1
        return merged

    def _match_ordinal_counter(self, tokens: list[dict], start_index: int) -> dict | None:
        if start_index + 2 >= len(tokens):
            return None
        prefix = tokens[start_index]
        number = tokens[start_index + 1]
        counter = tokens[start_index + 2]
        if (prefix.get("surface") or "").strip() != "第":
            return None
        number_surface = (number.get("surface") or "").strip()
        counter_surface = (counter.get("surface") or "").strip()
        if not self._is_number_like(number_surface) or counter_surface not in ORDINAL_COUNTERS:
            return None
        return {
            "token": self._build_number_counter_token(
                [prefix, number, counter],
                number_surface=number_surface,
                counter_surface=counter_surface,
                prefix_surface="第",
            ),
            "end_index": start_index + 3,
        }

    def _match_number_counter(self, tokens: list[dict], start_index: int) -> dict | None:
        if start_index + 1 >= len(tokens):
            return None
        number = tokens[start_index]
        counter = tokens[start_index + 1]
        number_surface = (number.get("surface") or "").strip()
        counter_surface = (counter.get("surface") or "").strip()
        if not self._is_number_like(number_surface) or counter_surface not in COUNTER_SURFACES:
            return None
        return {
            "token": self._build_number_counter_token(
                [number, counter],
                number_surface=number_surface,
                counter_surface=counter_surface,
            ),
            "end_index": start_index + 2,
        }

    def _build_number_counter_token(
        self,
        component_tokens: list[dict],
        *,
        number_surface: str,
        counter_surface: str,
        prefix_surface: str = "",
    ) -> dict:
        surface = "".join((token.get("surface") or "").strip() for token in component_tokens)
        reading = self._number_counter_reading(
            component_tokens,
            number_surface=number_surface,
            counter_surface=counter_surface,
            prefix_surface=prefix_surface,
        )
        return {
            "surface": surface,
            "reading": reading,
            "romaji": " ".join(
                (token.get("romaji") or "").strip()
                for token in component_tokens
                if (token.get("romaji") or "").strip()
            ),
            "pos": "counter_phrase",
            "highlight": any(bool(token.get("highlight")) for token in component_tokens),
        }

    def _number_counter_reading(
        self,
        component_tokens: list[dict],
        *,
        number_surface: str,
        counter_surface: str,
        prefix_surface: str = "",
    ) -> str:
        prefix_reading = ""
        if prefix_surface == "第":
            prefix_reading = "だい"
        fixed = COUNTER_READINGS.get(counter_surface, {}).get(number_surface)
        if fixed:
            return f"{prefix_reading}{fixed}"

        joined = "".join((token.get("reading") or "").strip() for token in component_tokens)
        if joined:
            return joined
        return "".join((token.get("surface") or "").strip() for token in component_tokens)

    def _is_number_like(self, value: str) -> bool:
        return bool(re.fullmatch(r"\d+|[一二三四五六七八九十百千万]+|何", value or ""))

    def normalize_lines(
        self,
        lines: list[dict],
        vocabulary: list[dict],
        merge_vocabulary: list[dict] | None = None,
    ) -> list[dict]:
        vocab_lookup_map = vocabulary_lookup(vocabulary)
        merge_vocab = merge_vocabulary or vocabulary
        normalized = []
        for index, line in enumerate(lines or [], start=1):
            if not isinstance(line, dict):
                continue
            text = (line.get("text") or line.get("ja") or "").strip()
            if not text:
                continue
            raw_tokens = line.get("tokens") if isinstance(line.get("tokens"), list) else []
            tokens = [
                token
                for token in (
                    self.normalize_token(
                        raw_token,
                        vocab_lookup_map,
                        highlight_terms=set(vocab_lookup_map.keys()),
                    )
                    for raw_token in raw_tokens
                )
                if token
            ]
            if not tokens:
                tokens = self.tokenize_text(text, vocabulary, merge_vocabulary=merge_vocab)
            else:
                tokens = self.merge_tokens(tokens, merge_vocab, highlight_vocabulary=vocabulary)
                tokens = self.merge_number_counter_tokens(tokens)
            reading = (line.get("reading") or "").strip() or self.reading_from_tokens(tokens)
            normalized.append({
                "line_ref": int(line.get("line_ref") or index),
                "speaker": (line.get("speaker") or line.get("role") or "Speaker").strip(),
                "text": text,
                "reading": reading,
                "romaji": (line.get("romaji") or "").strip(),
                "translation": (line.get("translation") or "").strip(),
                "tokens": tokens,
            })
        return normalized

    def normalize_sentence_patterns(
        self,
        items: list[dict],
        vocabulary: list[dict],
        merge_vocabulary: list[dict] | None = None,
    ) -> list[dict]:
        vocab_lookup_map = vocabulary_lookup(vocabulary)
        merge_vocab = merge_vocabulary or vocabulary
        normalized = []
        for index, item in enumerate(items or [], start=1):
            if not isinstance(item, dict):
                continue
            text = (item.get("text") or item.get("pattern") or item.get("ja") or "").strip()
            if not text:
                continue
            raw_tokens = item.get("tokens") if isinstance(item.get("tokens"), list) else []
            tokens = [
                token
                for token in (
                    self.normalize_token(
                        raw_token,
                        vocab_lookup_map,
                        highlight_terms=set(vocab_lookup_map.keys()),
                    )
                    for raw_token in raw_tokens
                )
                if token
            ]
            if not tokens:
                tokens = self.tokenize_text(text, vocabulary, merge_vocabulary=merge_vocab)
            else:
                tokens = self.merge_tokens(tokens, merge_vocab, highlight_vocabulary=vocabulary)
                tokens = self.merge_number_counter_tokens(tokens)
            reading = (item.get("reading") or "").strip() or self.reading_from_tokens(tokens)
            normalized.append({
                "pattern_id": int(item.get("pattern_id") or index),
                "text": text,
                "reading": reading,
                "romaji": (item.get("romaji") or "").strip(),
                "translation": (item.get("translation") or "").strip(),
                "tokens": tokens,
                "grammar_focus": item.get("grammar_focus") if isinstance(item.get("grammar_focus"), list) else [],
            })
        return normalized

    def reading_from_tokens(self, tokens: list[dict]) -> str:
        parts = []
        for token in tokens or []:
            if not isinstance(token, dict):
                continue
            surface = (token.get("surface") or "").strip()
            reading = (token.get("reading") or "").strip()
            if surface and all(char in JA_PUNCTUATION for char in surface):
                parts.append(surface)
            elif surface in PARTICLE_READINGS:
                parts.append(surface)
            elif reading:
                parts.append(reading)
            elif surface:
                parts.append(surface)
        return "".join(parts).strip()
