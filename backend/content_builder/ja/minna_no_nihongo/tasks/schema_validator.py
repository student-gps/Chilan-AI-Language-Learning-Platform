from __future__ import annotations


class MinnaNoNihongoSchemaValidator:
    """Lightweight guardrails for Minna no Nihongo lesson JSON."""

    OLD_KEYS = {"cn", "py", "pinyin"}
    OLD_KEY_SKIP_PREFIXES = ("$.video_render_plan", "$.teaching_slide_deck")
    JA_PUNCTUATION = set("。、！？「」『』（）()[]【】・･…：；,.;!?")
    INVALID_JA_SIMPLIFIED_CHARS = {"话", "愿"}
    REQUIRED_SECTIONS = {
        "sentence_patterns",
        "example_sentences",
        "dialogue",
        "vocabulary",
        "display_only_vocabulary",
        "grammar_sections",
    }

    def validate(self, lesson_data: dict) -> dict:
        print("  ▶️ [MNN Validate] 校验日语课程 schema...")
        if not isinstance(lesson_data, dict):
            raise ValueError("lesson_data must be a dict")

        self._require(lesson_data.get("schema_version") == "1.0", "schema_version must be 1.0")
        self._require(lesson_data.get("pipeline_id") == "minna_no_nihongo", "pipeline_id mismatch")
        self._require(lesson_data.get("target_language") == "ja", "target_language must be ja")

        metadata = lesson_data.get("lesson_metadata")
        self._require(isinstance(metadata, dict), "lesson_metadata missing")
        self._require(bool(metadata.get("lesson_id")), "lesson_id missing")
        self._require(bool(metadata.get("source")), "lesson source missing")

        content = lesson_data.get("course_content")
        self._require(isinstance(content, dict), "course_content missing")
        missing = sorted(section for section in self.REQUIRED_SECTIONS if section not in content)
        self._require(not missing, f"course_content missing sections: {', '.join(missing)}")
        self._require(isinstance(content.get("vocabulary"), list), "vocabulary must be a list")
        self._require(
            isinstance(content.get("display_only_vocabulary"), list),
            "display_only_vocabulary must be a list",
        )
        self._require(isinstance(content.get("grammar_sections"), list), "grammar_sections must be a list")
        self._require_no_display_only_duplicates(content)
        self._require_vocabulary_shape(content)
        self._require_grammar_shape(content)
        self._require_sentence_support(content)
        self._require_teaching_flow(lesson_data)

        old_paths = list(self._find_old_keys(lesson_data))
        if old_paths:
            raise ValueError(f"Old schema keys are not allowed in MNN: {', '.join(old_paths[:8])}")

        self._renumber_questions(lesson_data.get("practice_items", []))
        self._renumber_questions(lesson_data.get("database_items", []))
        print("  ✨ 日语 schema 校验通过。")
        return lesson_data

    def _find_old_keys(self, value, path: str = "$"):
        if any(path == prefix or path.startswith(f"{prefix}.") for prefix in self.OLD_KEY_SKIP_PREFIXES):
            return
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}"
                if key in self.OLD_KEYS:
                    yield child_path
                yield from self._find_old_keys(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                yield from self._find_old_keys(child, f"{path}[{index}]")

    def _renumber_questions(self, items) -> None:
        if not isinstance(items, list):
            return
        for index, item in enumerate(items, start=1):
            if isinstance(item, dict):
                item["question_id"] = index

    def _require_no_display_only_duplicates(self, content: dict) -> None:
        learnable = {
            (item.get("term") or item.get("word") or "").strip().casefold()
            for item in content.get("vocabulary", [])
            if isinstance(item, dict) and (item.get("term") or item.get("word") or "").strip()
        }
        display_only = {
            (item.get("term") or item.get("word") or "").strip().casefold()
            for item in content.get("display_only_vocabulary", [])
            if isinstance(item, dict) and (item.get("term") or item.get("word") or "").strip()
        }
        overlap = sorted(learnable & display_only)
        self._require(not overlap, f"display-only vocabulary duplicated in vocabulary: {', '.join(overlap[:8])}")

    def _require_vocabulary_shape(self, content: dict) -> None:
        for index, item in enumerate(content.get("vocabulary", []), start=1):
            self._require(isinstance(item, dict), f"vocabulary[{index}] must be an object")
            term = (item.get("term") or item.get("word") or "").strip()
            self._require(bool(term), f"vocabulary[{index}] term missing")
            self._require_valid_ja_text(term, f"vocabulary[{index}].term")
            self._require(bool((item.get("reading") or "").strip()), f"vocabulary[{index}] reading missing")
            self._require(
                bool((item.get("translation") or item.get("definition") or "").strip()),
                f"vocabulary[{index}] translation missing",
            )

        for index, item in enumerate(content.get("display_only_vocabulary", []), start=1):
            self._require(isinstance(item, dict), f"display_only_vocabulary[{index}] must be an object")
            self._require(
                bool((item.get("term") or item.get("word") or "").strip()),
                f"display_only_vocabulary[{index}] term missing",
            )
            self._require_valid_ja_text(
                (item.get("term") or item.get("word") or "").strip(),
                f"display_only_vocabulary[{index}].term",
            )
            self._require(
                bool((item.get("translation") or item.get("definition") or "").strip()),
                f"display_only_vocabulary[{index}] translation missing",
            )

    def _require_grammar_shape(self, content: dict) -> None:
        sections = content.get("grammar_sections")
        self._require(isinstance(sections, list) and bool(sections), "grammar_sections missing")
        for index, section in enumerate(sections, start=1):
            path = f"grammar_sections[{index}]"
            self._require(isinstance(section, dict), f"{path} must be an object")
            self._require(bool((section.get("title") or "").strip()), f"{path}.title missing")
            self._require(bool((section.get("explanation") or "").strip()), f"{path}.explanation missing")
            patterns = section.get("patterns") if isinstance(section.get("patterns"), list) else []
            examples = section.get("examples") if isinstance(section.get("examples"), list) else []
            self._require(bool(patterns or examples), f"{path} needs patterns or examples")
            if patterns:
                self._require_line_items(patterns, f"course_content.{path}.patterns")
            if examples:
                self._require_line_items(examples, f"course_content.{path}.examples")

    def _require_sentence_support(self, content: dict) -> None:
        self._require_line_items(content.get("sentence_patterns", []), "course_content.sentence_patterns")
        self._require_line_items(content.get("example_sentences", []), "course_content.example_sentences")
        dialogue = content.get("dialogue") if isinstance(content.get("dialogue"), dict) else {}
        self._require_line_items(dialogue.get("lines", []), "course_content.dialogue.lines")

    def _require_line_items(self, items, path: str) -> None:
        self._require(isinstance(items, list), f"{path} must be a list")
        for index, item in enumerate(items, start=1):
            item_path = f"{path}[{index}]"
            self._require(isinstance(item, dict), f"{item_path} must be an object")
            text = (item.get("text") or "").strip()
            self._require(bool(text), f"{item_path}.text missing")
            self._require_valid_ja_text(text, f"{item_path}.text")
            self._require(bool((item.get("reading") or "").strip()), f"{item_path}.reading missing")
            tokens = item.get("tokens")
            self._require(isinstance(tokens, list) and bool(tokens), f"{item_path}.tokens missing")
            for token_index, token in enumerate(tokens or [], start=1):
                token_path = f"{item_path}.tokens[{token_index}]"
                self._require(isinstance(token, dict), f"{token_path} must be an object")
                surface = (token.get("surface") or "").strip()
                self._require(bool(surface), f"{token_path}.surface missing")
                self._require_valid_ja_text(surface, f"{token_path}.surface")
                if not self._is_punctuation(surface):
                    self._require(bool((token.get("reading") or "").strip()), f"{token_path}.reading missing")

    def _require_teaching_flow(self, lesson_data: dict) -> None:
        teaching_materials = lesson_data.get("teaching_materials")
        self._require(isinstance(teaching_materials, dict), "teaching_materials missing")
        lesson_flow = teaching_materials.get("lesson_flow")
        self._require(isinstance(lesson_flow, list) and bool(lesson_flow), "teaching_materials.lesson_flow missing")

    def _is_punctuation(self, value: str) -> bool:
        return all(char in self.JA_PUNCTUATION for char in value)

    def _require_valid_ja_text(self, value: str, path: str) -> None:
        bad_chars = sorted(set(str(value or "")) & self.INVALID_JA_SIMPLIFIED_CHARS)
        self._require(not bad_chars, f"{path} contains simplified Chinese char in Japanese text: {''.join(bad_chars)}")

    def _require(self, condition: bool, message: str) -> None:
        if not condition:
            raise ValueError(message)
