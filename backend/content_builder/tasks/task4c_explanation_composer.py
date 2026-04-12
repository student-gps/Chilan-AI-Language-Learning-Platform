class Task4CExplanationComposer:
    TEMPLATE_BY_SEGMENT_TYPE = {
        "line_walkthrough": "line_focus",
        "vocabulary_focus": "vocab_spotlight",
        "grammar_focus": "grammar_pattern",
        "usage_focus": "usage_note",
        "recap": "lesson_recap",
    }

    def run(self, metadata: dict, explanation: dict) -> dict:
        metadata = metadata if isinstance(metadata, dict) else {}
        explanation = explanation if isinstance(explanation, dict) else {}

        lesson_id = metadata.get("lesson_id")
        course_id = metadata.get("course_id")
        lesson_title = metadata.get("title", "")
        global_config = explanation.get("global_config", {}) if isinstance(explanation.get("global_config"), dict) else {}
        segments = explanation.get("segments", []) if isinstance(explanation.get("segments"), list) else []

        composed_segments = []
        cursor_seconds = 0.0

        for index, segment in enumerate(segments, start=1):
            if not isinstance(segment, dict):
                continue

            composed_segment = self._compose_segment(
                segment=segment,
                lesson_title=lesson_title,
                order=index,
                start_time_seconds=cursor_seconds,
            )
            duration_seconds = composed_segment.get("duration_seconds", 0.0)
            cursor_seconds += duration_seconds
            composed_segments.append(composed_segment)

        return {
            "lesson_id": lesson_id,
            "course_id": course_id,
            "lesson_title": lesson_title,
            "target_audience": global_config.get("target_audience") or "English native speakers learning Chinese",
            "video_style": {
                "presenter_mode": global_config.get("presenter_mode") or "voice_over",
                "teaching_style": global_config.get("teaching_style") or "",
                "visual_style": global_config.get("visual_style") or "",
                "aspect_ratio": "16:9",
                "safe_area": "title_safe",
            },
            "segments": composed_segments,
            "timeline": {
                "total_duration_seconds": round(cursor_seconds, 2),
                "segment_count": len(composed_segments),
            },
            "renderer_notes": {
                "recommended_renderer": "template_video",
                "recommended_stack": ["react_templates", "motion_graphics", "ffmpeg_or_remotion"],
                "remarks": "This plan is intended for explanation-video composition, not direct AIGC generation."
            }
        }

    def _compose_segment(self, segment: dict, lesson_title: str, order: int, start_time_seconds: float) -> dict:
        segment_type = (segment.get("segment_type") or "line_walkthrough").strip() or "line_walkthrough"
        duration_seconds = self._normalize_duration(segment.get("estimated_duration_seconds", 12))
        on_screen_text = segment.get("on_screen_text", {}) if isinstance(segment.get("on_screen_text"), dict) else {}
        narration = segment.get("narration", {}) if isinstance(segment.get("narration"), dict) else {}
        highlight_words = segment.get("highlight_words", []) if isinstance(segment.get("highlight_words"), list) else []
        grammar_points = segment.get("grammar_points", []) if isinstance(segment.get("grammar_points"), list) else []

        # If the AI explicitly set template_name="grammar_table", pass through its visual_blocks directly
        raw_template_name = (segment.get("template_name") or "").strip()
        raw_visual_blocks = segment.get("visual_blocks")
        if raw_template_name == "grammar_table" and isinstance(raw_visual_blocks, list) and raw_visual_blocks:
            template_name = "grammar_table"
            cards = self._timeline_blocks(
                duration_seconds,
                [{"block_type": b.get("block_type", "content"), "content": b.get("content", {}), "weight": 1.0 / len(raw_visual_blocks)}
                 for b in raw_visual_blocks if isinstance(b, dict)],
            )
        else:
            template_name = self.TEMPLATE_BY_SEGMENT_TYPE.get(segment_type, "line_focus")
            cards = self._build_cards(
                segment_type=segment_type,
                lesson_title=lesson_title,
                on_screen_text=on_screen_text,
                highlight_words=highlight_words,
                grammar_points=grammar_points,
                duration_seconds=duration_seconds,
            )

        return {
            "segment_id": segment.get("segment_id", order),
            "segment_order": order,
            "segment_type": segment_type,
            "template_name": template_name,
            "source_line_refs": segment.get("source_line_refs", []) if isinstance(segment.get("source_line_refs"), list) else [],
            "segment_title": (segment.get("segment_title") or "").strip(),
            "teaching_goal": (segment.get("teaching_goal") or "").strip(),
            "narration_track": {
                "mode": "voice_over",
                "subtitle_en": (narration.get("subtitle_en") or "").strip(),
            },
            "visual_blocks": cards,
            "highlight_words": highlight_words,
            "grammar_points": grammar_points,
            "visual_notes": (segment.get("visual_notes") or "").strip(),
            "start_time_seconds": round(start_time_seconds, 2),
            "duration_seconds": duration_seconds,
            "end_time_seconds": round(start_time_seconds + duration_seconds, 2),
        }

    def _normalize_duration(self, value) -> float:
        try:
            duration = float(value)
        except (TypeError, ValueError):
            duration = 10.0
        return round(max(6.0, min(duration, 45.0)), 2)

    def _build_cards(
        self,
        segment_type: str,
        lesson_title: str,
        on_screen_text: dict,
        highlight_words: list,
        grammar_points: list,
        duration_seconds: float,
    ) -> list:
        focus_text = (on_screen_text.get("focus_text") or "").strip()
        focus_pinyin = (on_screen_text.get("focus_pinyin") or "").strip()
        focus_gloss_en = (on_screen_text.get("focus_gloss_en") or "").strip()
        notes = (on_screen_text.get("notes") or "").strip()

        if segment_type == "line_walkthrough":
            return self._timeline_blocks(
                duration_seconds,
                [
                    {
                        "block_type": "hero_line",
                        "content": {
                            "main_title": lesson_title,
                            "focus_text": focus_text,
                            "focus_pinyin": focus_pinyin,
                            "focus_gloss_en": focus_gloss_en,
                        },
                        "weight": 0.44,
                    },
                    {
                        "block_type": "teaching_points",
                        "content": {
                            "notes": notes,
                            "highlight_words": highlight_words[:3],
                        },
                        "weight": 0.56,
                    },
                ],
            )

        if segment_type == "vocabulary_focus":
            return self._timeline_blocks(
                duration_seconds,
                [
                    {
                        "block_type": "vocab_grid",
                        "content": {
                            "main_title": lesson_title,
                            "focus_text": focus_text,
                            "focus_gloss_en": focus_gloss_en,
                            "highlight_words": highlight_words[:6],
                        },
                        "weight": 0.7,
                    },
                    {
                        "block_type": "micro_note",
                        "content": {
                            "notes": notes,
                        },
                        "weight": 0.3,
                    },
                ],
            )

        if segment_type == "grammar_focus":
            return self._timeline_blocks(
                duration_seconds,
                [
                    {
                        "block_type": "pattern_hero",
                        "content": {
                            "main_title": lesson_title,
                            "focus_text": focus_text,
                            "focus_pinyin": focus_pinyin,
                            "focus_gloss_en": focus_gloss_en,
                        },
                        "weight": 0.42,
                    },
                    {
                        "block_type": "pattern_breakdown",
                        "content": {
                            "grammar_points": grammar_points[:4],
                            "notes": notes,
                        },
                        "weight": 0.58,
                    },
                ],
            )

        if segment_type == "usage_focus":
            return self._timeline_blocks(
                duration_seconds,
                [
                    {
                        "block_type": "usage_context",
                        "content": {
                            "focus_text": focus_text,
                            "focus_pinyin": focus_pinyin,
                            "focus_gloss_en": focus_gloss_en,
                            "notes": notes,
                        },
                        "weight": 1.0,
                    }
                ],
            )

        return self._timeline_blocks(
            duration_seconds,
            [
                {
                    "block_type": "recap_summary",
                    "content": {
                        "main_title": lesson_title,
                        "focus_text": focus_text,
                        "highlight_words": highlight_words[:6],
                        "grammar_points": grammar_points[:6],
                        "notes": notes,
                    },
                    "weight": 1.0,
                }
            ],
        )

    def _timeline_blocks(self, duration_seconds: float, blocks: list) -> list:
        normalized_blocks = []
        if not blocks:
            return normalized_blocks

        total_weight = sum(max(0.0, float(block.get("weight", 0.0))) for block in blocks) or 1.0
        cursor = 0.0

        for index, block in enumerate(blocks, start=1):
            weight = max(0.0, float(block.get("weight", 0.0)))
            block_duration = duration_seconds * (weight / total_weight)
            start = round(cursor, 2)
            if index == len(blocks):
                end = round(duration_seconds, 2)
            else:
                end = round(cursor + block_duration, 2)
            normalized_blocks.append({
                "block_order": index,
                "block_type": block.get("block_type") or "content",
                "start_time_seconds": start,
                "end_time_seconds": end,
                "duration_seconds": round(end - start, 2),
                "content": block.get("content", {}),
            })
            cursor = end

        return normalized_blocks
