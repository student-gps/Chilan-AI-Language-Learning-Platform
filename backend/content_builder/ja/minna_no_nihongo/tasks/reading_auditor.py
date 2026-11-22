from __future__ import annotations

import json
from copy import deepcopy

try:
    from content_builder.core.llm_providers import BaseLLMProvider
    from content_builder.ja.minna_no_nihongo.tasks.reading_annotator import (
        JA_PUNCTUATION,
        PARTICLE_READINGS,
        JapaneseReadingAnnotator,
        default_reading_for_surface,
        vocabulary_lookup,
    )
except ImportError:
    from content_builder.core.llm_providers import BaseLLMProvider
    from content_builder.ja.minna_no_nihongo.tasks.reading_annotator import (
        JA_PUNCTUATION,
        PARTICLE_READINGS,
        JapaneseReadingAnnotator,
        default_reading_for_surface,
        vocabulary_lookup,
    )


class MinnaNoNihongoReadingAuditor:
    """Repair readings and tokens after normalization."""

    AUDIT_BATCH_SIZE = 4

    def __init__(self, annotator: JapaneseReadingAnnotator | None = None):
        self.annotator = annotator or JapaneseReadingAnnotator()

    def run(
        self,
        lesson_data: dict,
        llm_provider: BaseLLMProvider | None = None,
        lesson_id: int | None = None,
        token_merge_vocabulary: list[dict] | None = None,
    ) -> dict:
        audited = deepcopy(lesson_data if isinstance(lesson_data, dict) else {})
        deterministic = self._apply_deterministic_repairs(audited, token_merge_vocabulary=token_merge_vocabulary)
        llm_corrections = []
        if llm_provider is not None:
            llm_corrections = self._apply_llm_audit(audited, llm_provider, lesson_id=lesson_id)
            post_llm_deterministic = self._apply_deterministic_repairs(
                audited,
                token_merge_vocabulary=token_merge_vocabulary,
            )
            for correction in post_llm_deterministic:
                correction["phase"] = "post_llm"
            if post_llm_deterministic:
                print(f"     🧩 [MNN Task 5B] 本地 reading/tokens 收口: {len(post_llm_deterministic)} 处。")
            deterministic.extend(post_llm_deterministic)

        if deterministic or llm_corrections:
            diagnostics = audited.setdefault("pipeline_diagnostics", {})
            diagnostics["reading_audit"] = {
                "deterministic_corrections": deterministic,
                "llm_corrections": llm_corrections,
            }
        return audited

    def _apply_deterministic_repairs(
        self,
        lesson_data: dict,
        token_merge_vocabulary: list[dict] | None = None,
    ) -> list[dict]:
        content = lesson_data.get("course_content") or {}
        vocabulary = content.get("vocabulary") or []
        token_vocabulary = (token_merge_vocabulary or []) + vocabulary + (content.get("display_only_vocabulary") or [])
        token_lookup = vocabulary_lookup(token_vocabulary)
        corrections = []
        for item in self._iter_sentence_items(lesson_data):
            path = item["_path"]
            line = item["line"]
            tokens = line.get("tokens") if isinstance(line.get("tokens"), list) else []
            if not tokens:
                tokens = self.annotator.tokenize_text(
                    line.get("text") or "",
                    vocabulary,
                    merge_vocabulary=token_vocabulary,
                )
                line["tokens"] = tokens
                corrections.append({"path": path, "field": "tokens", "reason": "tokens_missing"})
            else:
                merged_tokens = self._merge_existing_tokens(tokens, vocabulary, token_vocabulary)
                if (
                    merged_tokens
                    and self._token_surfaces_match_text(merged_tokens, line.get("text", ""))
                    and self._token_surfaces(merged_tokens) != self._token_surfaces(tokens)
                ):
                    line["tokens"] = merged_tokens
                    tokens = merged_tokens
                    corrections.append({
                        "path": path,
                        "field": "tokens",
                        "reason": "token_merge_cleanup",
                    })
            if not (line.get("reading") or "").strip():
                synthesized_reading = self.annotator.reading_from_tokens(tokens)
                if synthesized_reading:
                    line["reading"] = synthesized_reading
                    corrections.append({
                        "path": path,
                        "field": "reading",
                        "to": synthesized_reading,
                        "reason": "reading_missing_from_tokens",
                    })
            for token in tokens:
                if not isinstance(token, dict):
                    continue
                surface = (token.get("surface") or "").strip()
                if not surface:
                    continue
                expected = ""
                if surface in PARTICLE_READINGS:
                    expected = PARTICLE_READINGS[surface]
                elif surface in token_lookup and token_lookup[surface].get("reading"):
                    expected = token_lookup[surface]["reading"]
                elif not (token.get("reading") or "").strip():
                    expected = default_reading_for_surface(surface)
                if expected and token.get("reading") != expected:
                    corrections.append({
                        "path": path,
                        "surface": surface,
                        "from": token.get("reading", ""),
                        "to": expected,
                        "reason": "deterministic_token_reading",
                    })
                    token["reading"] = expected
            inferred = self._infer_missing_token_readings(line)
            for correction in inferred:
                correction["path"] = path
            corrections.extend(inferred)
            closed = self._close_line_schema_support(line, vocabulary, token_vocabulary)
            for correction in closed:
                correction["path"] = path
            corrections.extend(closed)
        return corrections

    def _merge_existing_tokens(
        self,
        tokens: list[dict],
        vocabulary: list[dict],
        merge_vocabulary: list[dict],
    ) -> list[dict]:
        merged = self.annotator.merge_tokens(
            tokens,
            merge_vocabulary=merge_vocabulary,
            highlight_vocabulary=vocabulary,
        )
        return self.annotator.merge_number_counter_tokens(merged)

    def _apply_llm_audit(
        self,
        lesson_data: dict,
        llm_provider: BaseLLMProvider,
        lesson_id: int | None = None,
    ) -> list[dict]:
        all_items = self._compact_sentence_items(lesson_data)
        if not all_items:
            return []
        compact_items = [item for item in all_items if self._needs_llm_audit(item)]
        skipped_count = len(all_items) - len(compact_items)
        print(
            "     🔎 [MNN Task 5A] reading/tokens 风险筛选: "
            f"total={len(all_items)}, audit={len(compact_items)}, skipped={skipped_count}"
        )
        if not compact_items:
            return []

        lookup = {
            (item["source_section"], int(item["source_ref"])): item["line"]
            for item in self._iter_sentence_items(lesson_data)
        }
        applied = []
        batches = list(self._chunks(compact_items, self.AUDIT_BATCH_SIZE))
        print(
            "     📦 [MNN Task 5A] reading/tokens 分批审校: "
            f"{len(compact_items)} 句, {len(batches)} 批, 最多 {self.AUDIT_BATCH_SIZE} 句/批。"
        )
        for index, batch in enumerate(batches, start=1):
            print(f"        ▶️ Task 5A.{index} 审校 {len(batch)} 句。")
            corrections = self._generate_batch_corrections(
                llm_provider,
                lesson_id=lesson_id,
                batch=batch,
                batch_label=f"Task 5A.{index}",
            )
            batch_applied = self._apply_corrections(corrections, lookup)
            print(f"        ✨ Task 5A.{index} applied={len(batch_applied)}")
            applied.extend(batch_applied)
        return applied

    def _generate_batch_corrections(
        self,
        llm_provider: BaseLLMProvider,
        *,
        lesson_id: int | None,
        batch: list[dict],
        batch_label: str,
    ) -> list[dict]:
        for attempt in range(1, 3):
            result = llm_provider.generate_structured_json(
                self._audit_prompt(lesson_id=lesson_id, items=batch),
                file_path=None,
            )
            corrections = result.get("reading_corrections") if isinstance(result, dict) else []
            if isinstance(corrections, list):
                return corrections
            print(f"        ⚠️ {batch_label} 返回结构异常，正在重试该小批次 ({attempt}/2)。")
        print(f"        ⚠️ {batch_label} 二次返回仍异常，跳过该批 LLM 修正，保留本地 fallback。")
        return []

    def _apply_corrections(self, corrections: list[dict], lookup: dict) -> list[dict]:
        applied = []
        for correction in corrections:
            if not isinstance(correction, dict):
                continue
            source_section = (correction.get("source_section") or "").strip()
            try:
                source_ref = int(correction.get("source_ref"))
            except (TypeError, ValueError):
                continue
            line = lookup.get((source_section, source_ref))
            if not line:
                continue

            changed = False
            if isinstance(correction.get("reading"), str) and correction["reading"].strip():
                new_reading = correction["reading"].strip()
                if line.get("reading") != new_reading:
                    line["reading"] = new_reading
                    changed = True
            if isinstance(correction.get("romaji"), str):
                new_romaji = correction["romaji"].strip()
                if new_romaji and line.get("romaji") != new_romaji:
                    line["romaji"] = new_romaji
                    changed = True
            if isinstance(correction.get("tokens"), list) and correction["tokens"]:
                normalized_tokens = self._normalize_tokens(correction["tokens"])
                if normalized_tokens and self._token_surfaces_match_text(normalized_tokens, line.get("text", "")):
                    line["tokens"] = normalized_tokens
                    changed = True
            if changed:
                applied.append({
                    "source_section": source_section,
                    "source_ref": source_ref,
                    "reason": (correction.get("reason") or "llm_reading_audit").strip(),
                })
        return applied

    def _chunks(self, items: list, batch_size: int):
        for start in range(0, len(items), batch_size):
            yield items[start:start + batch_size]

    def _infer_missing_token_readings(self, line: dict) -> list[dict]:
        tokens = line.get("tokens") if isinstance(line.get("tokens"), list) else []
        reading = self._compact_text(line.get("reading") or "")
        if not tokens or not reading:
            return []

        corrections = []
        cursor = 0
        for index, token in enumerate(tokens):
            if not isinstance(token, dict):
                continue
            surface = (token.get("surface") or "").strip()
            if not surface:
                continue
            token_reading = (token.get("reading") or "").strip()
            if self._is_punctuation(surface):
                cursor = self._consume_anchor(reading, cursor, [surface])
                continue
            if token_reading:
                cursor = self._consume_anchor(reading, cursor, self._anchor_candidates(surface, token_reading))
                continue

            next_anchor = self._next_anchor(tokens, index + 1)
            inferred = ""
            if next_anchor:
                next_position = self._find_next_anchor(reading, cursor, next_anchor)
                if next_position is not None:
                    inferred = reading[cursor:next_position]
                    cursor = next_position
            else:
                inferred = reading[cursor:]
                cursor = len(reading)

            inferred = inferred.strip()
            if inferred and not self._contains_cjk(inferred):
                token["reading"] = inferred
                corrections.append({
                    "surface": surface,
                    "to": inferred,
                    "reason": "token_reading_inferred_from_sentence_reading",
                })
        return corrections

    def _close_line_schema_support(
        self,
        line: dict,
        vocabulary: list[dict],
        merge_vocabulary: list[dict] | None = None,
    ) -> list[dict]:
        tokens = line.get("tokens") if isinstance(line.get("tokens"), list) else []
        quality_issues = self._tokenization_quality_issues({"tokens": tokens})
        if (
            not self._has_missing_token_reading(tokens)
            and not self._has_mixed_script_cjk_token(tokens)
            and not quality_issues
        ):
            return []

        corrections = []
        text = line.get("text") or ""
        retokenized = self.annotator.tokenize_text(
            text,
            vocabulary,
            merge_vocabulary=merge_vocabulary or vocabulary,
        )
        retokenized_quality_issues = self._tokenization_quality_issues({"tokens": retokenized})
        if (
            retokenized
            and self._token_surfaces_match_text(retokenized, text)
            and (
                self._missing_token_reading_count(retokenized) < self._missing_token_reading_count(tokens)
                or self._has_mixed_script_cjk_token(tokens)
                or len(retokenized_quality_issues) < len(quality_issues)
            )
        ):
            line["tokens"] = retokenized
            tokens = retokenized
            corrections.append({
                "field": "tokens",
                "reason": "retokenized_for_local_quality_gate",
            })
            inferred = self._infer_missing_token_readings(line)
            corrections.extend(inferred)

        for token in tokens:
            if not isinstance(token, dict):
                continue
            surface = (token.get("surface") or "").strip()
            if not surface or self._is_punctuation(surface) or (token.get("reading") or "").strip():
                continue
            fallback = default_reading_for_surface(surface) or surface
            token["reading"] = fallback
            corrections.append({
                "surface": surface,
                "to": fallback,
                "reason": "last_resort_token_reading_fallback",
            })
        return corrections

    def _has_missing_token_reading(self, tokens: list[dict]) -> bool:
        return self._missing_token_reading_count(tokens) > 0

    def _missing_token_reading_count(self, tokens: list[dict]) -> int:
        count = 0
        for token in tokens or []:
            if not isinstance(token, dict):
                continue
            surface = (token.get("surface") or "").strip()
            if surface and not self._is_punctuation(surface) and not (token.get("reading") or "").strip():
                count += 1
        return count

    def _has_mixed_script_cjk_token(self, tokens: list[dict]) -> bool:
        for token in tokens or []:
            if not isinstance(token, dict):
                continue
            surface = (token.get("surface") or "").strip()
            if self._contains_cjk(surface) and self._contains_kana(surface):
                return True
        return False

    def _anchor_candidates(self, surface: str, reading: str = "") -> list[str]:
        candidates = []
        if surface in PARTICLE_READINGS:
            candidates.extend([PARTICLE_READINGS[surface], surface])
        if reading:
            candidates.append(reading)
        if surface and not self._contains_cjk(surface):
            candidates.append(surface)
        return [item for item in candidates if item]

    def _next_anchor(self, tokens: list[dict], start_index: int) -> list[str]:
        for token in tokens[start_index:]:
            if not isinstance(token, dict):
                continue
            surface = (token.get("surface") or "").strip()
            if not surface:
                continue
            if self._is_punctuation(surface):
                return [surface]
            reading = (token.get("reading") or "").strip()
            candidates = self._anchor_candidates(surface, reading)
            if candidates:
                return candidates
        return []

    def _consume_anchor(self, reading: str, cursor: int, candidates: list[str]) -> int:
        for candidate in candidates:
            if candidate and reading.startswith(candidate, cursor):
                return cursor + len(candidate)
        position = self._find_next_anchor(reading, cursor, candidates)
        if position is None:
            return cursor
        return position + len(next(candidate for candidate in candidates if reading.startswith(candidate, position)))

    def _find_next_anchor(self, reading: str, cursor: int, candidates: list[str]) -> int | None:
        positions = [
            position
            for candidate in candidates
            if candidate
            for position in [reading.find(candidate, cursor)]
            if position >= 0
        ]
        return min(positions) if positions else None

    def _audit_prompt(self, *, lesson_id: int | None, items: list[dict]) -> str:
        return f"""
        你是一名日语初学者教材的读音审校员。请检查每个句子的整句 reading、
        romaji 和 tokens 是否正确，特别注意汉字读音和助词读音。

        lesson_id: {lesson_id}

        规则：
        1. reading 使用假名，适合初学者跟读。
        2. 助词读音必须按实际发音：主题 は -> わ，方向 へ -> え，宾格 を -> お。
        3. 有汉字的词必须有正确假名读音，例如 会社員 -> かいしゃいん。
        4. tokens 要适合初学者逐词学习：不要把 わたし、です、ありません、ください、
           すみません、いくら 等常见表达拆成单个假名。
        5. 专名、复合词、数字量词应尽量保持自然整词，例如 新大阪、時計、1階。
        6. 只返回需要修正的句子；没问题的句子不要返回。
        7. tokens 必须保持原文 surface，不要改写日语原文。

        待检查句子：
        {json.dumps(items, ensure_ascii=False, indent=2)}

        输出结构：
        {{
          "reading_corrections": [
            {{
              "source_section": "sentence_patterns",
              "source_ref": 1,
              "reading": "これはじしょです。",
              "romaji": "kore wa jisho desu.",
              "tokens": [
                {{"surface": "これ", "reading": "これ", "romaji": "kore", "pos": "代名詞", "highlight": true}},
                {{"surface": "は", "reading": "わ", "romaji": "wa", "pos": "助詞", "highlight": true}}
              ],
              "reason": "助词 は should be read wa"
            }}
          ]
        }}
        """

    def _compact_sentence_items(self, lesson_data: dict) -> list[dict]:
        compact = []
        for item in self._iter_sentence_items(lesson_data):
            line = item["line"]
            compact.append({
                "source_section": item["source_section"],
                "source_ref": item["source_ref"],
                "text": line.get("text", ""),
                "reading": line.get("reading", ""),
                "romaji": line.get("romaji", ""),
                "tokens": [
                    {
                        "surface": token.get("surface", ""),
                        "reading": token.get("reading", ""),
                        "romaji": token.get("romaji", ""),
                    }
                    for token in (line.get("tokens") or [])
                    if isinstance(token, dict)
                ],
            })
            quality_issues = self._tokenization_quality_issues(compact[-1])
            if quality_issues:
                compact[-1]["tokenization_quality_issues"] = quality_issues
        return compact

    def _needs_llm_audit(self, item: dict) -> bool:
        text = item.get("text") or ""
        reading = item.get("reading") or ""
        tokens = item.get("tokens") if isinstance(item.get("tokens"), list) else []
        if not reading.strip() or self._contains_cjk(reading):
            return True
        if not tokens:
            return True
        if not self._token_surfaces_match_text(tokens, text):
            return True
        if self._tokenization_quality_issues(item):
            return True
        for token in tokens:
            if not isinstance(token, dict):
                return True
            surface = (token.get("surface") or "").strip()
            token_reading = (token.get("reading") or "").strip()
            if not surface:
                return True
            if self._is_punctuation(surface):
                continue
            if not token_reading:
                return True
            if surface in PARTICLE_READINGS and token_reading != PARTICLE_READINGS[surface]:
                return True
            if self._contains_cjk(surface) and self._contains_cjk(token_reading):
                return True
        return False

    def _tokenization_quality_issues(self, item: dict) -> list[str]:
        tokens = item.get("tokens") if isinstance(item.get("tokens"), list) else []
        lexical_tokens = [
            (token.get("surface") or "").strip()
            for token in tokens
            if isinstance(token, dict)
            and (token.get("surface") or "").strip()
            and not self._is_punctuation((token.get("surface") or "").strip())
        ]
        if len(lexical_tokens) < 3:
            return []

        issues = []
        max_single_kana_run = self._max_single_kana_run(lexical_tokens)
        if max_single_kana_run >= 3:
            issues.append(f"consecutive_single_kana_tokens={max_single_kana_run}")
        if self._has_split_small_kana(lexical_tokens):
            issues.append("split_small_kana_token")
        max_single_kanji_run = self._max_single_kanji_run(lexical_tokens)
        if max_single_kanji_run >= 2:
            issues.append(f"consecutive_single_kanji_tokens={max_single_kanji_run}")

        single_kana_count = sum(1 for surface in lexical_tokens if self._is_single_kana(surface))
        single_kana_ratio = single_kana_count / len(lexical_tokens)
        average_length = sum(len(surface) for surface in lexical_tokens) / len(lexical_tokens)
        if len(lexical_tokens) >= 5 and single_kana_ratio >= 0.55:
            issues.append(f"single_kana_ratio={single_kana_ratio:.2f}")
        if len(lexical_tokens) >= 6 and average_length < 1.45:
            issues.append(f"avg_token_length={average_length:.2f}")
        return issues

    def _max_single_kana_run(self, surfaces: list[str]) -> int:
        longest = 0
        current = 0
        for surface in surfaces:
            if self._is_single_kana(surface):
                current += 1
                longest = max(longest, current)
            else:
                current = 0
        return longest

    def _has_split_small_kana(self, surfaces: list[str]) -> bool:
        small_kana = set("ぁぃぅぇぉゃゅょっァィゥェォャュョッ")
        previous_was_single_kana = False
        for surface in surfaces:
            if len(surface) == 1 and surface in small_kana and previous_was_single_kana:
                return True
            previous_was_single_kana = self._is_single_kana(surface)
        return False

    def _max_single_kanji_run(self, surfaces: list[str]) -> int:
        longest = 0
        current = 0
        for surface in surfaces:
            if len(surface) == 1 and self._contains_cjk(surface):
                current += 1
                longest = max(longest, current)
            else:
                current = 0
        return longest

    def _is_single_kana(self, value: str) -> bool:
        return len(value) == 1 and self._contains_kana(value)

    def _iter_sentence_items(self, lesson_data: dict):
        content = lesson_data.get("course_content") if isinstance(lesson_data.get("course_content"), dict) else {}
        for index, item in enumerate(content.get("sentence_patterns") or [], start=1):
            if isinstance(item, dict):
                yield {
                    "_path": f"course_content.sentence_patterns[{index}]",
                    "source_section": "sentence_patterns",
                    "source_ref": int(item.get("pattern_id") or index),
                    "line": item,
                }
        for index, item in enumerate(content.get("example_sentences") or [], start=1):
            if isinstance(item, dict):
                yield {
                    "_path": f"course_content.example_sentences[{index}]",
                    "source_section": "example_sentences",
                    "source_ref": int(item.get("line_ref") or index),
                    "line": item,
                }
        dialogue = content.get("dialogue") if isinstance(content.get("dialogue"), dict) else {}
        for index, item in enumerate(dialogue.get("lines") or [], start=1):
            if isinstance(item, dict):
                yield {
                    "_path": f"course_content.dialogue.lines[{index}]",
                    "source_section": "dialogue",
                    "source_ref": int(item.get("line_ref") or index),
                    "line": item,
                }
        for section_index, section in enumerate(content.get("grammar_sections") or [], start=1):
            if not isinstance(section, dict):
                continue
            for index, item in enumerate(section.get("patterns") or [], start=1):
                if isinstance(item, dict):
                    yield {
                        "_path": f"course_content.grammar_sections[{section_index}].patterns[{index}]",
                        "source_section": "grammar_patterns",
                        "source_ref": section_index * 100 + index,
                        "line": item,
                    }
            for index, item in enumerate(section.get("examples") or [], start=1):
                if isinstance(item, dict):
                    yield {
                        "_path": f"course_content.grammar_sections[{section_index}].examples[{index}]",
                        "source_section": "grammar_examples",
                        "source_ref": section_index * 100 + index,
                        "line": item,
                    }

    def _normalize_tokens(self, tokens: list[dict]) -> list[dict]:
        normalized = []
        for token in tokens:
            if not isinstance(token, dict):
                continue
            surface = (token.get("surface") or "").strip()
            if not surface:
                continue
            reading = (token.get("reading") or "").strip()
            if surface in PARTICLE_READINGS:
                reading = PARTICLE_READINGS[surface]
            elif not reading and not self._is_punctuation(surface):
                reading = default_reading_for_surface(surface)
            normalized.append({
                "surface": surface,
                "reading": reading,
                "romaji": (token.get("romaji") or "").strip(),
                "pos": (token.get("pos") or token.get("part_of_speech") or "").strip(),
                "highlight": bool(token.get("highlight")),
            })
        return normalized

    def _token_surfaces_match_text(self, tokens: list[dict], text: str) -> bool:
        if not text:
            return True
        token_text = "".join((token.get("surface") or "") for token in tokens)
        return self._compact_text(token_text) == self._compact_text(text)

    def _token_surfaces(self, tokens: list[dict]) -> list[str]:
        return [(token.get("surface") or "") for token in tokens if isinstance(token, dict)]

    def _compact_text(self, value: str) -> str:
        return "".join(str(value or "").split())

    def _is_punctuation(self, value: str) -> bool:
        return all(char in JA_PUNCTUATION for char in value)

    def _contains_cjk(self, value: str) -> bool:
        return any("\u4e00" <= char <= "\u9fff" for char in str(value or ""))

    def _contains_kana(self, value: str) -> bool:
        return any("\u3040" <= char <= "\u30ff" or char == "ー" for char in str(value or ""))
