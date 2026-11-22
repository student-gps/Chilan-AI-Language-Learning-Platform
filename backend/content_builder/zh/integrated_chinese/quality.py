"""Read-only quality gates for Integrated Chinese content and deliverable media."""
from __future__ import annotations

import json
import hashlib
import math
import re
import subprocess
from collections import Counter
from pathlib import Path

from content_builder.core.artifacts import file_digest, fingerprint, resolve_artifact_path

SUPPORTED_TEMPLATES = {"line_focus", "vocab_spotlight", "grammar_pattern", "grammar_table", "usage_note", "lesson_recap", "pinyin_tones", "pinyin_grid"}
QUESTION_TYPES = {"CN_TO_EN", "EN_TO_CN", "EN_TO_CN_SPEAK", "CN_LISTEN_WRITE"}


def compact(text) -> str:
    return re.sub(r"[\W_]+", "", str(text), flags=re.UNICODE).casefold()


def dialogue_lines(data: dict) -> list[dict]:
    lines = []
    for block in data.get("course_content", {}).get("dialogues", []):
        for line in block.get("lines", [block]):
            words = line.get("words") or line.get("tokens") or []
            lines.append({"line_ref": len(lines) + 1, "text": line.get("chinese") or "".join(w.get("cn", "") for w in words),
                          "pinyin": line.get("pinyin") or " ".join(w.get("py", "") for w in words),
                          "translation": line.get("translation") or line.get("english") or "", "role": line.get("role", "")})
    return lines


def _number(value) -> float:
    try:
        parsed = float(value)
        return parsed if math.isfinite(parsed) else -1
    except (ValueError, TypeError):
        return -1


def audit_lesson(data: dict, *, artifact_root: Path, lang: str = "en", media: bool = False, deep: bool = False) -> dict:
    issues = []
    metrics = {}

    def issue(code, path, message, severity="error"):
        issues.append({"severity": severity, "code": code, "path": path, "message": message})

    if not isinstance(data, dict):
        return {"ok": False, "issues": [{"severity": "error", "code": "json", "path": "$", "message": "Lesson must be an object"}], "metrics": {}}
    metadata = data.get("lesson_metadata") or {}
    lesson_id, course_id = metadata.get("lesson_id"), metadata.get("course_id")
    if not isinstance(lesson_id, int) or isinstance(lesson_id, bool) or lesson_id <= 0 or not course_id or not metadata.get("title"):
        issue("identity", "lesson_metadata", "Positive lesson_id, course_id and title are required")
    try:
        lines = dialogue_lines(data)
    except (AttributeError, TypeError):
        lines = []
        issue("dialogue_shape", "course_content.dialogues", "Malformed dialogue structure")
    metrics["source_line_count"] = len(lines)
    if not lines:
        issue("empty_source", "course_content.dialogues", "No textbook lines were extracted")
    for i, line in enumerate(lines):
        if not line["text"] or not line["translation"] or not line["pinyin"].strip():
            issue("line_support", f"course_content.dialogues[{i}]", "Text, pinyin and translation must all be present")

    vocabulary = data.get("course_content", {}).get("vocabulary") or []
    metrics["vocabulary_count"] = len(vocabulary)
    if not vocabulary:
        issue("empty_vocabulary", "course_content.vocabulary", "No learnable vocabulary")
    for i, word in enumerate(vocabulary):
        if not isinstance(word, dict) or not all(word.get(key) for key in ("word", "pinyin", "definition")):
            issue("vocabulary_shape", f"course_content.vocabulary[{i}]", "word, pinyin and definition are required")
            continue
        example = word.get("example_sentence") or {}
        if not isinstance(example, dict) or not (example.get("cn") or example.get("hanzi")) or not (example.get("py") or example.get("pinyin")) or not example.get("translation"):
            issue("vocabulary_example", f"course_content.vocabulary[{i}].example_sentence", "Example needs Chinese, pinyin and translation")

    materials = data.get("teaching_materials") or {}
    grammar = materials.get("grammar_sections") or []
    metrics["grammar_count"] = len(grammar)
    if not grammar:
        issue("no_grammar", "teaching_materials.grammar_sections", "No grammar extracted; verify the source PDF scope", "warning")
    for i, section in enumerate(grammar):
        if not isinstance(section, dict) or not section.get("title") or not section.get("explanation_en") or not (section.get("patterns") or section.get("examples")):
            issue("grammar_skeleton", f"teaching_materials.grammar_sections[{i}]", "Grammar must include explanation and patterns/examples")

    questions = data.get("database_items") or []
    metrics["question_types"] = dict(Counter(q.get("question_type") for q in questions if isinstance(q, dict)))
    metrics["question_count"] = len(questions)
    if not questions:
        issue("empty_practice", "database_items", "Practice questions are required")
    ids, seen = set(), set()
    for i, question in enumerate(questions):
        path = f"database_items[{i}]"
        if not isinstance(question, dict):
            issue("question_shape", path, "Question must be an object")
            continue
        qid = question.get("question_id")
        if not isinstance(qid, int) or qid <= 0 or qid in ids:
            issue("question_id", path, "Question IDs must be positive and unique")
        ids.add(qid)
        if question.get("lesson_id") != lesson_id or question.get("course_id") != course_id:
            issue("question_identity", path, "Question belongs to a different lesson/course")
        answers = question.get("standard_answers")
        if not question.get("original_text") or not isinstance(answers, list) or not answers or any(not isinstance(a, str) or not a.strip() for a in answers):
            issue("answer", path, "Prompt and nonempty text reference answers are required")
        qtype = question.get("question_type")
        localized_types = {f"CN_TO_{lang.upper()}", f"{lang.upper()}_TO_CN", f"{lang.upper()}_TO_CN_SPEAK"}
        if qtype not in QUESTION_TYPES | localized_types:
            issue("question_type", path, f"Unsupported question type {qtype!r}")
        signature = (qtype, compact(question.get("original_text")), tuple(sorted(compact(a) for a in answers or [])))
        if signature in seen:
            issue("duplicate_question", path, "Duplicate practice question", "warning")
        seen.add(signature)
        if qtype == "CN_LISTEN_WRITE":
            ref = (question.get("metadata") or {}).get("line_ref")
            source = next((line for line in lines if line["line_ref"] == ref), None)
            if not source or not any(compact(answer) == compact(source["text"]) for answer in answers or []):
                issue("listening_source", path, "Dictation must reference a real source line and its exact answer")

    segments = data.get("video_render_plan", {}).get("explanation", {}).get("segments") or []
    metrics["slide_count"] = len(segments)
    if not segments:
        issue("empty_plan", "video_render_plan.explanation.segments", "No teaching plan")
    segment_ids, covered = set(), set()
    walkthrough_texts = {}
    for i, segment in enumerate(segments):
        path = f"video_render_plan.explanation.segments[{i}]"
        if not isinstance(segment, dict):
            issue("segment_shape", path, "Segment must be an object")
            continue
        sid = segment.get("segment_id")
        if not isinstance(sid, int) or sid <= 0 or sid in segment_ids:
            issue("segment_id", path, "Segment IDs must be positive and unique")
        segment_ids.add(sid)
        if segment.get("template_name") not in SUPPORTED_TEMPLATES:
            issue("template", path, f"Unsupported template {segment.get('template_name')!r}")
        if segment.get("template_name") == "grammar_pattern" and len(segment.get("grammar_points") or []) > 4:
            issue("slide_density", path, "Grammar page exceeds four patterns; split before composing the visual blocks")
        if segment.get("template_name") == "vocab_spotlight" and len(segment.get("highlight_words") or []) > 6:
            issue("slide_density", path, "Vocabulary page exceeds six words; split before composing the visual blocks")
        track = segment.get("narration_track") or {}
        text = track.get(f"subtitle_{lang}") or track.get("script") or track.get("subtitle_en") or ""
        if not text.strip():
            issue("empty_narration", path, "Every teaching page requires narration")
        if lang == "en":
            unmarked = re.sub(r"\[zh:[^\]]+\]", "", text)
            if re.search(r"[\u4e00-\u9fff]", unmarked):
                issue("tts_language", path, "Chinese speech in English narration requires [zh:...] markers")
            if re.search(r"[āǎēěīǐōǒūǔǖǘǚǜĀǍĒĚĪǏŌǑŪǓǕǗǙǛ]", unmarked):
                issue("tts_pinyin", path, "Tone-marked pinyin belongs on the teaching board; use [zh:Chinese] for spoken examples")
        if segment.get("segment_type") == "line_walkthrough":
            refs = segment.get("source_line_refs") or []
            # Older artifacts lack refs. Exact visible text is evidence; narration
            # mentioning a line elsewhere is not a substitute for teaching it.
            visible = "".join(str(block.get("content", {}).get("focus_text") or "") for block in segment.get("visual_blocks", []) if isinstance(block, dict))
            for ref in refs:
                if isinstance(ref, int) and 1 <= ref <= len(lines):
                    walkthrough_texts.setdefault(ref, []).append(visible)
            for line in lines:
                if compact(line["text"]) and compact(line["text"]) in compact(visible):
                    covered.add(line["line_ref"])
        for block in segment.get("visual_blocks", []):
            content = block.get("content") or {}
            for key, limit in (("highlight_words", 6), ("items", 12), ("rows", 4), ("patterns", 4)):
                if isinstance(content.get(key), list) and len(content[key]) > limit:
                    issue("slide_density", path, f"{key} exceeds {limit}; split the teaching page")
        if _number(segment.get("duration_seconds")) > 75:
            issue("long_page", path, "Narration exceeds 75 seconds; consider splitting by teaching point", "warning")
    for line in lines:
        if compact(line["text"]) and compact(line["text"]) in compact("".join(walkthrough_texts.get(line["line_ref"], []))):
            covered.add(line["line_ref"])
    metrics["covered_source_lines"] = len(covered)
    missing = [line["line_ref"] for line in lines if line["line_ref"] not in covered]
    if missing:
        issue("teaching_coverage", "video_render_plan.explanation", f"Textbook lines lack walkthrough pages: {missing}")
    source_grammar_ids = {str(g.get("grammar_id")) for g in grammar if isinstance(g, dict) and g.get("grammar_id")}
    taught_grammar = {str(ref) for segment in segments if isinstance(segment, dict) for ref in segment.get("source_grammar_ids", [])}
    if source_grammar_ids - taught_grammar:
        issue("grammar_coverage", "video_render_plan.explanation", f"Grammar coverage is unverified: {sorted(source_grammar_ids - taught_grammar)}", "error" if data.get("workflow_version") else "warning")
    note_ids = {str(note.get("note_id")) for note in materials.get("language_notes", []) if isinstance(note, dict) and note.get("note_id")}
    taught_notes = {str(ref) for segment in segments if isinstance(segment, dict) for ref in segment.get("source_note_ids", [])}
    if note_ids - taught_notes:
        issue("note_coverage", "video_render_plan.explanation", f"Language note coverage is unverified: {sorted(note_ids - taught_notes)}", "error" if data.get("workflow_version") else "warning")

    if media:
        _audit_media(data, artifact_root, lang, segments, lines, issue, metrics, deep)
    return {"version": "1.0", "ok": not any(item["severity"] == "error" for item in issues), "lesson_id": lesson_id,
            "lang": lang, "phase": "media" if media else "content", "issues": issues, "metrics": metrics}


def _audit_media(data, root, lang, segments, lines, issue, metrics, deep):
    checked = {}
    decoded_images = {}
    seen_images = {}

    def asset(value, path, duration=None, image=False, compressed=False):
        try:
            local = resolve_artifact_path(value, root)
            if local.stat().st_size <= 0:
                raise ValueError("Empty file")
            checked[str(local)] = local.stat().st_size
            if deep and image:
                from PIL import Image
                with Image.open(local) as bitmap:
                    if bitmap.size != (1920, 1080):
                        issue("image_dimensions", path, f"Expected 1920x1080, got {bitmap.size}")
                    if bitmap.format != "WEBP":
                        issue("image_encoding", path, f"Expected WebP, decoded {bitmap.format}")
                    bitmap.load()
                    decoded_images[str(local)] = hashlib.sha256(bitmap.convert("RGB").tobytes()).hexdigest()
            elif deep:
                result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,channels,sample_rate,bit_rate", "-of", "json", str(local)], capture_output=True, text=True, timeout=30, check=True)
                probe = json.loads(result.stdout)
                actual = float(probe["format"]["duration"])
                if duration is not None and abs(actual - duration) > 0.3:
                    issue("audio_duration", path, f"Measured {actual:.3f}s, expected {duration:.3f}s")
                stream = next(s for s in probe["streams"] if s.get("codec_type") == "audio")
                if compressed and (int(stream.get("channels", 0)) != 1 or int(stream.get("sample_rate", 0)) != 24000 or int(stream.get("bit_rate", 0)) > 42000):
                    issue("audio_encoding", path, "Delivery audio must be mono, 24kHz, at most 40kbps")
        except (OSError, ValueError, KeyError, StopIteration, subprocess.SubprocessError) as exc:
            issue("asset", path, f"Missing or unreadable media: {exc}")
            return None
        return local

    narration = data.get("explanation_narration_audio") or {}
    if narration.get("status") != "ok":
        issue("narration_status", "explanation_narration_audio", "Narration did not succeed")
    total = sum(max(0, _number(segment.get("duration_seconds"))) for segment in segments if isinstance(segment, dict))
    metrics["duration_seconds"] = round(total, 3)
    try:
        resolve_artifact_path(narration.get("audio_file", ""), root)
    except (OSError, ValueError):
        issue("master_audio", "explanation_narration_audio.audio_file", "Narration master is absent locally; delivery is checked using the per-slide audio", "warning")
    else:
        asset(narration.get("audio_file", ""), "explanation_narration_audio.audio_file", total)
    deck = data.get("teaching_slide_deck") or {}
    slides = deck.get("slides") or []
    if deck.get("lang") != lang or deck.get("lesson_id") != data.get("lesson_metadata", {}).get("lesson_id"):
        issue("deck_identity", "teaching_slide_deck", "Deck identity/language mismatch")
    if len(slides) != len(segments) or deck.get("slide_count") != len(slides):
        issue("slide_count", "teaching_slide_deck", "Every segment must have exactly one slide")
    if deck.get("render_recipe", {}).get("caption_mode") != "external" or _number(deck.get("render_recipe", {}).get("version")) < 3:
        issue("stale_slides", "teaching_slide_deck.render_recipe", "Regenerate using caption-free static renderer")
    cursor = 0
    for i, slide in enumerate(slides):
        path = f"teaching_slide_deck.slides[{i}]"
        duration = _number(slide.get("duration_ms"))
        if duration <= 0:
            issue("slide_duration", path, "Slide duration must be positive")
        if i < len(segments) and (slide.get("segment_id") != segments[i].get("segment_id") or abs(duration - _number(segments[i].get("duration_seconds")) * 1000) > 2):
            issue("slide_segment", path, "Slide does not match its segment/time")
        audio = slide.get("audio") or {}
        if abs(_number(audio.get("source_start_ms")) - cursor) > 2:
            issue("audio_offset", path, "Audio split does not follow the narration timeline")
        cursor += duration
        image = slide.get("image") or {}
        local_image = asset(image.get("local_path", ""), path + ".image", image=True)
        if local_image is not None and i < len(segments):
            segment = segments[i]
            board = {"template": segment.get("template_name"), "title": segment.get("segment_title"),
                "blocks": [{"type": block.get("block_type"), "content": block.get("content")} for block in segment.get("visual_blocks", [])],
                "highlights": segment.get("highlight_words"), "grammar": segment.get("grammar_points")}
            board_hash = fingerprint(board)
            pixels = decoded_images.get(str(local_image)) or file_digest(local_image)
            if pixels in seen_images and seen_images[pixels][0] != board_hash:
                issue("duplicate_slide_image", path, f"Distinct teaching pages share the same image as slide {seen_images[pixels][1]}")
            seen_images[pixels] = (board_hash, i + 1)
        if Path(image.get("local_path", "")).suffix != ".webp":
            issue("image_encoding", path, "Delivery images must be WebP")
        asset(audio.get("local_path", ""), path + ".audio", duration / 1000, compressed=True)
        previous_end = 0
        cues = slide.get("caption_cues") or []
        if not cues:
            issue("captions", path, "Timed captions are required")
        for cue in cues:
            start, end = _number(cue.get("start_ms")), _number(cue.get("end_ms"))
            if not cue.get("text") or start < previous_end or end <= start or end > duration:
                issue("caption_timing", path, "Captions must be ordered, nonoverlapping and inside slide duration")
            previous_end = end
    assets = data.get("lesson_audio_assets") or {}
    full = assets.get("full_audio") or {}
    if full.get("status") == "ready":
        asset(full.get("local_audio_file", ""), "lesson_audio_assets.full_audio")
    items = assets.get("items") or []
    by_ref = {item.get("line_ref"): item for item in items if isinstance(item, dict)}
    for line in lines:
        item = by_ref.get(line["line_ref"], {})
        if item.get("status") != "ready" or compact(item.get("hanzi") or item.get("source_text", "")) != compact(line["text"]):
            issue("source_audio", "lesson_audio_assets", f"Missing/stale audio for textbook line {line['line_ref']}")
        asset(item.get("local_audio_file", ""), f"lesson_audio_assets.items[{line['line_ref']}]")
    metrics["media_bytes"] = sum(checked.values())
    metrics["media_file_count"] = len(checked)
    metrics["unique_slide_images"] = len(seen_images)


def require_quality(report: dict) -> None:
    errors = [f"{item['path']}: {item['message']}" for item in report["issues"] if item["severity"] == "error"]
    if errors:
        raise ValueError("Quality gate failed:\n" + "\n".join(errors))
