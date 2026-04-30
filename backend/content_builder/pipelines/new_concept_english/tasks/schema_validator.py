from __future__ import annotations


class NewConceptEnglishSchemaValidator:
    """Lightweight guardrails for New Concept English schema v2 lesson JSON."""

    OLD_KEYS = {"cn", "py", "pinyin", "chinese"}

    def validate(self, lesson_data: dict) -> dict:
        print("  ▶️ [NCE Validate] 校验 schema v2...")
        if not isinstance(lesson_data, dict):
            raise ValueError("lesson_data must be a dict")

        self._require(lesson_data.get("schema_version") == "2.0", "schema_version must be 2.0")
        self._require(lesson_data.get("pipeline_id") == "new_concept_english", "pipeline_id mismatch")
        self._require(lesson_data.get("target_language") == "en", "target_language must be en")

        metadata = lesson_data.get("lesson_metadata")
        self._require(isinstance(metadata, dict), "lesson_metadata missing")
        self._require(bool(metadata.get("lesson_id")), "lesson_id missing")
        self._require(bool(metadata.get("source")), "lesson source missing")

        content = lesson_data.get("course_content")
        self._require(isinstance(content, dict), "course_content missing")
        anchor = content.get("anchor")
        self._require(isinstance(anchor, dict), "anchor missing")
        self._require(bool(anchor.get("lines")), "anchor.lines missing")
        self._require(isinstance(content.get("vocabulary"), list), "vocabulary must be a list")
        self._require(isinstance(content.get("pattern_drills"), list), "pattern_drills must be a list")

        old_paths = list(self._find_old_keys(lesson_data))
        if old_paths:
            raise ValueError(f"Old Chinese schema keys are not allowed in NCE v2: {', '.join(old_paths[:8])}")

        self._renumber_questions(lesson_data.get("practice_items", []))
        self._renumber_questions(lesson_data.get("database_items", []))
        print("  ✨ schema v2 校验通过。")
        return lesson_data

    def _find_old_keys(self, value, path: str = "$"):
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

    def _require(self, condition: bool, message: str) -> None:
        if not condition:
            raise ValueError(message)
