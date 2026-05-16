from __future__ import annotations


class Task5PracticeGenerator:
    """Generate small practice sets from source-grounded anchor and drills."""

    def run(
        self,
        lesson_id: str,
        course_id: str,
        anchor: dict,
        pattern_drills: list[dict],
        vocabulary: list[dict],
    ) -> dict:
        print("  ▶️ [NCE Task 5] 生成听说读写练习题...")
        practice_items = []
        question_id = 1

        for item in self._pattern_items(pattern_drills):
            item["question_id"] = question_id
            practice_items.append(item)
            question_id += 1

        for item in self._target_to_support_items(anchor):
            item["question_id"] = question_id
            practice_items.append(item)
            question_id += 1

        for item in self._listen_write_items(anchor):
            item["question_id"] = question_id
            practice_items.append(item)
            question_id += 1

        for item in self._speaking_items(anchor, pattern_drills):
            item["question_id"] = question_id
            practice_items.append(item)
            question_id += 1

        database_items = [
            self._to_database_item(item, lesson_id=lesson_id, course_id=course_id)
            for item in practice_items
        ]
        print(f"  ✨ Task 5 完成，practice_items {len(practice_items)} 条。")
        return {"practice_items": practice_items, "database_items": database_items}

    def _pattern_items(self, pattern_drills: list[dict]) -> list[dict]:
        items = []
        for drill in pattern_drills or []:
            if not isinstance(drill, dict):
                continue
            pattern = (drill.get("pattern") or "").strip()
            if not pattern:
                continue
            for slot in (drill.get("slots") or [])[:6]:
                if not isinstance(slot, dict):
                    continue
                slot_text = (slot.get("text") or "").strip()
                slot_translation = (slot.get("translation") or "").strip()
                if not slot_text:
                    continue
                answer = pattern.replace("{item}", slot_text)
                items.append({
                    "question_type": "PATTERN_DRILL",
                    "prompt": f"请用本课句型表达：{slot_translation}",
                    "standard_answers": [answer],
                    "context": {"pattern": pattern, "slot": slot_text, "source_lesson": drill.get("source_lesson")},
                })
        return items

    def _target_to_support_items(self, anchor: dict) -> list[dict]:
        items = []
        for line in (anchor.get("lines") or [])[:6]:
            if not isinstance(line, dict):
                continue
            text = (line.get("text") or "").strip()
            translation = (line.get("translation") or "").strip()
            if text and translation:
                items.append({
                    "question_type": "TARGET_TO_SUPPORT",
                    "prompt": text,
                    "standard_answers": [translation],
                    "context": {"line_ref": line.get("line_ref")},
                })
        return items

    def _listen_write_items(self, anchor: dict) -> list[dict]:
        items = []
        for line in (anchor.get("lines") or [])[:4]:
            if not isinstance(line, dict):
                continue
            text = (line.get("text") or "").strip()
            if text:
                items.append({
                    "question_type": "TARGET_LISTEN_WRITE",
                    "prompt": "听英文，写出你听到的句子。",
                    "standard_answers": [text],
                    "context": {"line_ref": line.get("line_ref")},
                    "metadata": {"answer_mode": "text"},
                })
        return items

    def _speaking_items(self, anchor: dict, pattern_drills: list[dict]) -> list[dict]:
        items = []
        for drill in pattern_drills or []:
            pattern = (drill.get("pattern") or "").strip() if isinstance(drill, dict) else ""
            first_slot = next((slot for slot in (drill.get("slots") or []) if isinstance(slot, dict) and slot.get("text")), None) if isinstance(drill, dict) else None
            if pattern and first_slot:
                answer = pattern.replace("{item}", first_slot["text"])
                items.append({
                    "question_type": "TARGET_SPEAK",
                    "prompt": f"请用英语说：{first_slot.get('translation', '')}",
                    "standard_answers": [answer],
                    "context": {"pattern": pattern, "slot": first_slot.get("text")},
                    "metadata": {"answer_mode": "speech"},
                })
                break

        if not items:
            for line in anchor.get("lines") or []:
                if isinstance(line, dict) and line.get("text") and line.get("translation"):
                    items.append({
                        "question_type": "TARGET_SPEAK",
                        "prompt": f"请用英语说：{line.get('translation')}",
                        "standard_answers": [line.get("text")],
                        "context": {"line_ref": line.get("line_ref")},
                        "metadata": {"answer_mode": "speech"},
                    })
                    break
        return items

    def _to_database_item(self, item: dict, lesson_id: str, course_id: str) -> dict:
        return {
            "lesson_id": lesson_id,
            "course_id": course_id,
            "question_id": item.get("question_id"),
            "question_type": item.get("question_type"),
            "original_text": item.get("prompt"),
            "standard_answers": item.get("standard_answers", []),
            "context_examples": [],
            "metadata": item.get("metadata", {}) | {"context": item.get("context", {})},
        }
