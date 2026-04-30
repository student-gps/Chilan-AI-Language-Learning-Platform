from __future__ import annotations


class Task6LessonVideoPlanner:
    """Plan the explanation video in the same high-level order as the app page."""

    def run(self, lesson_data: dict) -> dict:
        print("  ▶️ [NCE Task 6] 生成教学视频脚本...")
        metadata = lesson_data.get("lesson_metadata", {})
        content = lesson_data.get("course_content", {})
        anchor = content.get("anchor", {})
        vocabulary = content.get("vocabulary", [])
        pattern_drills = content.get("pattern_drills", [])
        teaching_materials = lesson_data.get("teaching_materials", {})

        lines = anchor.get("lines") if isinstance(anchor.get("lines"), list) else []
        first_line = (lines[0].get("text") if lines else "") or metadata.get("title", "")
        first_translation = (lines[0].get("translation") if lines else "") or metadata.get("title_localized", "")
        first_drill = pattern_drills[0] if pattern_drills else {}
        pattern = (first_drill.get("pattern") or "").strip()
        slots = first_drill.get("slots") if isinstance(first_drill.get("slots"), list) else []
        slot_preview = " / ".join(
            slot.get("text", "")
            for slot in slots[:6]
            if isinstance(slot, dict) and slot.get("text")
        )
        vocab_preview = " / ".join(
            item.get("term", "")
            for item in vocabulary[:6]
            if isinstance(item, dict) and item.get("term")
        )
        notes = teaching_materials.get("notes_on_text") if isinstance(teaching_materials.get("notes_on_text"), list) else []
        grammar = teaching_materials.get("grammar_sections") if isinstance(teaching_materials.get("grammar_sections"), list) else []

        segments = [
            {
                "segment_id": 1,
                "segment_type": "scene_setup",
                "title": "场景导入",
                "goal": "建立本课交际场景和学习目标。",
                "on_screen": {"focus_text": first_line, "translation": first_translation},
                "narration": self._narration("先看本课场景。", first_line, first_translation),
            },
            {
                "segment_id": 2,
                "segment_type": "line_walkthrough",
                "title": "课文讲解",
                "goal": "逐句理解主课文/对话。",
                "source_line_refs": [line.get("line_ref") for line in lines if isinstance(line, dict)],
                "on_screen": {"focus_text": anchor.get("title", ""), "translation": metadata.get("title_localized", "")},
                "narration": "这一段我们按原文顺序拆解课文，先听懂意思，再注意英语表达的固定搭配。",
            },
            {
                "segment_id": 3,
                "segment_type": "pattern_focus",
                "title": "句型讲解",
                "goal": "掌握偶数课提供的可替换句型。",
                "on_screen": {"focus_text": pattern, "translation": first_drill.get("translation_pattern", "") if isinstance(first_drill, dict) else ""},
                "narration": f"偶数课的重点是句型操练。保留 {pattern or '核心句型'} 的结构，再替换关键词，就能说出一组新句子。",
            },
            {
                "segment_id": 4,
                "segment_type": "vocabulary_focus",
                "title": "词汇带入",
                "goal": "把新词放进句型和课文语境。",
                "on_screen": {"focus_text": slot_preview or vocab_preview, "translation": ""},
                "narration": "这些词不要孤立背。更好的方式是直接放进刚才的句型里，一边换词，一边练完整句。",
            },
            {
                "segment_id": 5,
                "segment_type": "guided_practice",
                "title": "跟读操练",
                "goal": "完成看图替换、跟读和开口练习。",
                "on_screen": {"focus_text": pattern or first_line, "translation": ""},
                "narration": "最后进入跟读操练。先看提示，再说完整英文句子，注意语调和停顿。",
            },
        ]

        if notes or grammar:
            segments.insert(3, {
                "segment_id": 4,
                "segment_type": "grammar_focus",
                "title": "语法补充",
                "goal": "解释本课必须掌握的用法和易错点。",
                "on_screen": {
                    "focus_text": (grammar[0].get("title") if grammar and isinstance(grammar[0], dict) else ""),
                    "translation": "",
                },
                "narration": "这里补充本课最关键的语法和用法。理解规则之后，再回到课文里看它是怎么自然出现的。",
            })
            for index, segment in enumerate(segments, start=1):
                segment["segment_id"] = index

        video_plan = {
            "lesson_video_plan": {
                "lesson_id": metadata.get("lesson_id"),
                "course_id": metadata.get("course_id"),
                "lesson_title": metadata.get("title", ""),
                "target_audience": "Chinese speakers learning English",
                "primary_language": "en",
                "support_language": lesson_data.get("support_language", "zh"),
                "subtitle_options": {"target_text": True, "support_translation": True},
            },
            "dramatization": {"global_config": {}, "scenes": []},
            "explanation": {
                "global_config": {
                    "target_audience": "Chinese speakers learning English",
                    "presenter_mode": "voice_over",
                    "teaching_style": "clear, structured, practice-first",
                    "visual_style": "textbook-focused motion graphics",
                },
                "segments": segments,
            },
            "production_notes": {
                "recommended_workflow": [
                    "render anchor text",
                    "render vocabulary cards",
                    "render pattern drill",
                    "render guided practice",
                ],
                "remarks": "New Concept English Book 1 combines odd text lessons with even pattern drills.",
            },
        }
        print(f"  ✨ Task 6 完成，讲解段落 {len(segments)} 段。")
        return {
            "video_plan": video_plan,
            "explanation_plan": {
                "target_audience": "Chinese speakers learning English",
                "segments": segments,
            },
        }

    def _narration(self, prefix: str, text: str, translation: str) -> str:
        pieces = [prefix]
        if text:
            pieces.append(f"英语原句是：{text}。")
        if translation:
            pieces.append(f"意思是：{translation}。")
        return "".join(pieces)


class Task7RenderPlanComposer:
    TEMPLATE_BY_SEGMENT_TYPE = {
        "scene_setup": "scene_setup",
        "line_walkthrough": "line_focus",
        "pattern_focus": "grammar_pattern",
        "grammar_focus": "grammar_pattern",
        "vocabulary_focus": "vocab_spotlight",
        "guided_practice": "guided_practice",
        "recap": "lesson_recap",
    }

    def run(self, lesson_data: dict) -> dict:
        print("  ▶️ [NCE Task 7] 生成讲解视频渲染计划...")
        metadata = lesson_data.get("lesson_metadata", {})
        explanation_plan = lesson_data.get("explanation_plan", {})
        segments = explanation_plan.get("segments") if isinstance(explanation_plan.get("segments"), list) else []
        lesson_number = self._lesson_number(metadata.get("lesson_id"))

        composed_segments = []
        cursor = 0.0
        for order, segment in enumerate(segments, start=1):
            duration = self._duration_for(segment)
            composed = self._compose_segment(segment, order, cursor, duration, metadata)
            composed_segments.append(composed)
            cursor += duration

        render_plan = {
            "lesson_id": lesson_number,
            "course_id": metadata.get("course_id"),
            "lesson_title": metadata.get("title", ""),
            "target_audience": "Chinese speakers learning English",
            "video_style": {
                "presenter_mode": "voice_over",
                "teaching_style": "clear, structured, practice-first",
                "visual_style": "textbook-focused motion graphics",
                "aspect_ratio": "16:9",
                "safe_area": "title_safe",
            },
            "segments": composed_segments,
            "timeline": {
                "total_duration_seconds": round(cursor, 2),
                "segment_count": len(composed_segments),
            },
            "renderer_notes": {
                "recommended_renderer": "template_video",
                "recommended_stack": ["react_templates", "motion_graphics", "ffmpeg_or_remotion"],
                "remarks": "Narration text is stored in narration_track.subtitle_en for compatibility with the existing narrator.",
            },
        }
        print(f"  ✨ Task 7 完成，渲染段落 {len(composed_segments)} 段。")
        return {"explanation": render_plan}

    def _compose_segment(self, segment: dict, order: int, start: float, duration: float, metadata: dict) -> dict:
        segment_type = (segment.get("segment_type") or "line_walkthrough").strip()
        on_screen = segment.get("on_screen") if isinstance(segment.get("on_screen"), dict) else {}
        narration = (segment.get("narration") or segment.get("narration_zh") or "").strip()
        title = (segment.get("title") or "").strip()
        goal = (segment.get("goal") or "").strip()

        return {
            "segment_id": segment.get("segment_id") or order,
            "segment_order": order,
            "segment_type": segment_type,
            "template_name": self.TEMPLATE_BY_SEGMENT_TYPE.get(segment_type, "line_focus"),
            "source_line_refs": segment.get("source_line_refs") if isinstance(segment.get("source_line_refs"), list) else [],
            "segment_title": title,
            "teaching_goal": goal,
            "narration_track": {
                "mode": "voice_over",
                "subtitle_en": narration,
                "subtitle_support": narration,
            },
            "visual_blocks": self._visual_blocks(on_screen, metadata, duration),
            "highlight_words": segment.get("highlight_words") if isinstance(segment.get("highlight_words"), list) else [],
            "grammar_points": segment.get("grammar_points") if isinstance(segment.get("grammar_points"), list) else [],
            "visual_notes": (segment.get("visual_notes") or "").strip(),
            "start_time_seconds": round(start, 2),
            "duration_seconds": duration,
            "end_time_seconds": round(start + duration, 2),
        }

    def _visual_blocks(self, on_screen: dict, metadata: dict, duration: float) -> list[dict]:
        return [
            {
                "block_order": 1,
                "block_type": "hero_line",
                "start_time_seconds": 0.0,
                "end_time_seconds": round(duration * 0.55, 2),
                "duration_seconds": round(duration * 0.55, 2),
                "content": {
                    "main_title": metadata.get("title", ""),
                    "focus_text": (on_screen.get("focus_text") or "").strip(),
                    "focus_gloss_en": (on_screen.get("translation") or "").strip(),
                },
            },
            {
                "block_order": 2,
                "block_type": "teaching_points",
                "start_time_seconds": round(duration * 0.55, 2),
                "end_time_seconds": duration,
                "duration_seconds": round(duration * 0.45, 2),
                "content": {
                    "notes": (on_screen.get("translation") or "").strip(),
                },
            },
        ]

    def _duration_for(self, segment: dict) -> float:
        try:
            value = float(segment.get("estimated_duration_seconds") or 14.0)
        except (TypeError, ValueError):
            value = 14.0
        return round(max(8.0, min(value, 40.0)), 2)

    def _lesson_number(self, lesson_id) -> int:
        text = str(lesson_id or "")
        digits = "".join(ch for ch in text if ch.isdigit())
        return int(digits or 0)
