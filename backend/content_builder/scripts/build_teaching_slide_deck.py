import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

CONTENT_BUILDER_DIR = Path(__file__).resolve().parents[1]
if str(CONTENT_BUILDER_DIR) not in sys.path:
    sys.path.insert(0, str(CONTENT_BUILDER_DIR))

from core.paths import default_paths
from core.pipeline import get_pipeline


def _lesson_digits(value) -> str:
    digits = re.findall(r"\d+", str(value or ""))
    if not digits:
        raise ValueError(f"Cannot parse lesson id from {value!r}")
    return str(int(digits[0]))


_ABBREV_RE = re.compile(
    r"\b(Mr|Mrs|Ms|Dr|Prof|Sr|Jr|St|vs|etc|e\.g|i\.e|approx|dept|fig|govt|ca|cf|vol|no)\.",
    re.IGNORECASE,
)
_PLACEHOLDER = "\x00"


def _split_sentences(text: str) -> list[str]:
    if not text:
        return []

    ellipsis_placeholder = "\x01"
    protected = text.strip().replace("…", ellipsis_placeholder)
    protected = re.sub(r"\.{2,}", ellipsis_placeholder, protected)
    protected = _ABBREV_RE.sub(lambda m: m.group(0)[:-1] + _PLACEHOLDER, protected)

    terminators = ".!?。！？"
    trailing_closers = "\"”')]}」』"
    sentences: list[str] = []
    start = 0
    quote_stack: list[str] = []
    quote_pairs = {
        "«": "»",
        "»": "«",
        "„": "“",
        "“": "”",
        "「": "」",
        "『": "』",
    }
    i = 0

    def restore(value: str) -> str:
        return value.replace(_PLACEHOLDER, ".").replace(ellipsis_placeholder, "...").strip()

    def prev_non_space(index: int) -> str:
        j = index
        while j >= 0 and protected[j].isspace():
            j -= 1
        return protected[j] if j >= 0 else ""

    def is_boundary(next_index: int, terminator: str) -> bool:
        return (
            next_index == len(protected)
            or protected[next_index].isspace()
            or terminator in "。！？"
        )

    while i < len(protected):
        ch = protected[i]

        if protected.startswith("[zh:", i):
            end = protected.find("]", i + 4)
            if end != -1:
                i = end + 1
                continue

        if quote_stack and ch == quote_stack[-1]:
            quote_stack.pop()
            if not quote_stack and prev_non_space(i - 1) in terminators:
                j = i + 1
                while j < len(protected) and protected[j] in trailing_closers:
                    j += 1
                if j == len(protected) or protected[j].isspace():
                    sentence = restore(protected[start:j])
                    if sentence:
                        sentences.append(sentence)
                    while j < len(protected) and protected[j].isspace():
                        j += 1
                    start = j
                    i = j
                    continue
        elif ch in quote_pairs:
            quote_stack.append(quote_pairs[ch])
        elif ch in terminators and not quote_stack:
            j = i + 1
            while j < len(protected) and protected[j] in trailing_closers:
                j += 1
            if is_boundary(j, ch):
                sentence = restore(protected[start:j])
                if sentence:
                    sentences.append(sentence)
                while j < len(protected) and protected[j].isspace():
                    j += 1
                start = j
                i = j
                continue

        i += 1

    tail = restore(protected[start:])
    if tail:
        sentences.append(tail)
    return sentences


def _caption_cues(segment: dict) -> list[dict]:
    narration = ((segment.get("narration_track") or {}).get("subtitle_en") or "").strip()
    sentence_texts = segment.get("sentence_texts")
    sentences = [str(item).strip() for item in sentence_texts if str(item).strip()] if isinstance(sentence_texts, list) else []
    if not sentences:
        sentences = _split_sentences(narration)
    if not sentences:
        return []

    duration_ms = int(round(float(segment.get("duration_seconds") or 0) * 1000))
    if duration_ms <= 0:
        duration_ms = max(4000, len(sentences) * 3500)

    timings = segment.get("sentence_timings_seconds")
    cues = []
    if isinstance(timings, list) and timings:
        starts = [max(0, int(round(float(t or 0) * 1000))) for t in timings[: len(sentences)]]
        while len(starts) < len(sentences):
            starts.append(int(round(duration_ms * len(starts) / len(sentences))))
    else:
        starts = [int(round(duration_ms * i / len(sentences))) for i in range(len(sentences))]

    for index, sentence in enumerate(sentences):
        start_ms = min(starts[index], max(duration_ms - 300, 0))
        end_ms = starts[index + 1] if index + 1 < len(starts) else duration_ms
        end_ms = max(start_ms + 500, min(end_ms, duration_ms))
        cues.append({"start_ms": start_ms, "end_ms": end_ms, "text": sentence})
    return cues


def _normalize_lookup_text(value: str) -> str:
    return re.sub(r"[\s,，。.!?！？；;：:、“”\"'‘’()\[\]（）]", "", str(value or ""))


def _iter_translation_examples(value):
    if isinstance(value, dict):
        cn = value.get("cn")
        translation = value.get("translation")
        if isinstance(cn, str) and isinstance(translation, str) and len(_normalize_lookup_text(cn)) >= 8:
            yield cn, translation
        for child in value.values():
            yield from _iter_translation_examples(child)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_translation_examples(item)


def _join_line_words(line: dict) -> str:
    words = line.get("words")
    if not isinstance(words, list):
        return ""
    parts = []
    for item in words:
        if isinstance(item, dict):
            parts.append(str(item.get("cn") or ""))
    return "".join(parts)


def _translation_candidates(data: dict) -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []

    # Prefer exact example-sentence translations anywhere in the payload. They are
    # usually sentence-level, while course_content translations can be paragraph-level.
    for top_key in ("database_items", "teaching_materials", "course_content"):
        for cn, translation in _iter_translation_examples(data.get(top_key) or {}):
            candidates.append((cn, translation))

    for section in ((data.get("course_content") or {}).get("dialogues") or []):
        for line in section.get("lines") or []:
            if not isinstance(line, dict):
                continue
            line_cn = _join_line_words(line)
            translation = line.get("translation")
            if line_cn and isinstance(translation, str):
                candidates.append((line_cn, translation))

    return candidates


def _best_translation_for(text: str, candidates: list[tuple[str, str]]) -> str:
    target = _normalize_lookup_text(text)
    if not target:
        return ""

    exact_matches = []
    loose_matches = []
    for cn, translation in candidates:
        normalized = _normalize_lookup_text(cn)
        if not normalized or not translation:
            continue
        if normalized == target:
            exact_matches.append((cn, translation))
        elif target in normalized or normalized in target:
            loose_matches.append((cn, translation))

    matches = exact_matches or loose_matches
    if not matches:
        return ""
    matches.sort(key=lambda item: (
        abs(len(_normalize_lookup_text(item[0])) - len(target)),
        abs(len(item[1]) - max(24, len(target) * 0.9)),
        len(item[1]),
    ))
    return matches[0][1].strip()


def _hydrate_missing_line_glosses(data: dict) -> int:
    candidates = _translation_candidates(data)
    if not candidates:
        return 0

    updated = 0
    segments = (((data.get("video_render_plan") or {}).get("explanation") or {}).get("segments") or [])
    for segment in segments:
        if not isinstance(segment, dict) or segment.get("template_name") != "line_focus":
            continue
        for block in segment.get("visual_blocks") or []:
            if not isinstance(block, dict) or block.get("block_type") != "hero_line":
                continue
            content = block.get("content")
            if not isinstance(content, dict):
                continue
            focus_text = content.get("focus_text") or content.get("main_title") or ""
            translation = _best_translation_for(focus_text, candidates)
            current = str(content.get("focus_gloss_en") or "").strip()
            if translation and (not current or len(current) > len(translation) * 1.35):
                content["focus_gloss_en"] = translation
                updated += 1
    return updated


def _normalize_explanation_timeline(data: dict) -> None:
    plan = ((data.get("video_render_plan") or {}).get("explanation") or {})
    segments = plan.get("segments") if isinstance(plan, dict) else []
    if not isinstance(segments, list):
        return

    cursor = 0.0
    count = 0
    for segment in segments:
        if not isinstance(segment, dict):
            continue
        duration = float(segment.get("duration_seconds") or segment.get("estimated_duration_seconds") or 0)
        segment["start_time_seconds"] = round(cursor, 3)
        cursor += max(0.0, duration)
        segment["end_time_seconds"] = round(cursor, 3)
        count += 1

    timeline = plan.setdefault("timeline", {})
    timeline["total_duration_seconds"] = round(cursor, 3)
    timeline["segment_count"] = count


def _split_narration_audio(
    *,
    narration_file: Path,
    output_dir: Path,
    lesson_digits: str,
    lang: str,
    slide_index: int,
    start_ms: int,
    duration_ms: int,
    force: bool,
) -> Path:
    suffix = f"_{lang}" if lang != "en" else ""
    output_file = output_dir / f"lesson{lesson_digits}_slide_{slide_index:03d}{suffix}.mp3"
    if output_file.exists() and not force:
        return output_file
    if not narration_file.exists():
        return narration_file

    output_dir.mkdir(parents=True, exist_ok=True)
    start_seconds = max(0, start_ms) / 1000
    duration_seconds = max(0.5, duration_ms / 1000)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{start_seconds:.3f}",
            "-t",
            f"{duration_seconds:.3f}",
            "-i",
            str(narration_file),
            "-vn",
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "4",
            str(output_file),
        ],
        check=True,
    )
    return output_file


def _wrap(text: str, max_chars: int) -> list[str]:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if not text:
        return []
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > max_chars:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _text_lines(lines: list[str], x: int, y: int, size: int, color: str, weight: int = 600, line_gap: int | None = None) -> str:
    line_gap = line_gap or int(size * 1.45)
    output = []
    for offset, line in enumerate(lines):
        output.append(
            f'<text x="{x}" y="{y + offset * line_gap}" fill="{color}" '
            f'font-size="{size}" font-weight="{weight}" font-family="Inter, Segoe UI, Arial, sans-serif">'
            f"{html.escape(line)}</text>"
        )
    return "\n".join(output)


def _first_block(segment: dict, block_type: str) -> dict:
    for block in segment.get("visual_blocks") or []:
        if isinstance(block, dict) and block.get("block_type") == block_type:
            content = block.get("content")
            return content if isinstance(content, dict) else {}
    return {}


def _svg_for_segment(segment: dict, lesson_title: str, slide_index: int, total: int) -> str:
    hero = _first_block(segment, "hero_line")
    title = segment.get("segment_title") or f"Slide {slide_index}"
    goal = segment.get("teaching_goal") or ""
    focus_text = hero.get("focus_text") or hero.get("main_title") or lesson_title
    focus_pinyin = hero.get("focus_pinyin") or ""
    focus_gloss = hero.get("focus_gloss_en") or ""
    words = segment.get("highlight_words") or hero.get("highlight_words") or []
    words = [w for w in words if isinstance(w, dict)][:4]

    title_lines = _wrap(title, 42)[:2]
    goal_lines = _wrap(goal, 72)[:3]
    gloss_lines = _wrap(focus_gloss, 36)[:2]

    cards = []
    card_y = 470
    card_w = 250
    for i, word in enumerate(words):
        x = 72 + i * (card_w + 24)
        cards.append(
            f'<rect x="{x}" y="{card_y}" width="{card_w}" height="126" rx="18" fill="rgba(15,23,42,0.60)" stroke="rgba(241,245,249,0.18)"/>'
            f'<text x="{x + 22}" y="{card_y + 42}" fill="#facc15" font-size="34" font-weight="900" font-family="KaiTi, SimSun, serif">{html.escape(str(word.get("word") or ""))}</text>'
            f'<text x="{x + 22}" y="{card_y + 72}" fill="#67e8f9" font-size="20" font-weight="800" font-family="Inter, Segoe UI, Arial, sans-serif">{html.escape(str(word.get("pinyin") or ""))}</text>'
            f'<text x="{x + 22}" y="{card_y + 102}" fill="#cbd5e1" font-size="18" font-weight="700" font-family="Inter, Segoe UI, Arial, sans-serif">{html.escape(str(word.get("translation") or ""))}</text>'
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="52%" stop-color="#164e63"/>
      <stop offset="100%" stop-color="#111827"/>
    </linearGradient>
    <radialGradient id="glow" cx="68%" cy="32%" r="52%">
      <stop offset="0%" stop-color="#facc15" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="#facc15" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="1280" height="720" fill="url(#bg)"/>
  <rect width="1280" height="720" fill="url(#glow)"/>
  <rect x="28" y="28" width="1224" height="664" rx="28" fill="none" stroke="rgba(241,245,249,0.20)" stroke-width="2"/>
  <text x="72" y="84" fill="#93c5fd" font-size="18" font-weight="900" letter-spacing="5" font-family="Inter, Segoe UI, Arial, sans-serif">LESSON {html.escape(str(lesson_title))} · {slide_index}/{total}</text>
  {_text_lines(title_lines, 72, 142, 42, "#f8fafc", 900)}
  <rect x="72" y="230" width="520" height="178" rx="24" fill="rgba(248,250,252,0.10)" stroke="rgba(248,250,252,0.18)"/>
  <text x="332" y="314" text-anchor="middle" fill="#facc15" font-size="74" font-weight="900" font-family="KaiTi, STKaiti, SimSun, serif">{html.escape(str(focus_text))}</text>
  <text x="332" y="358" text-anchor="middle" fill="#67e8f9" font-size="28" font-weight="800" font-family="Inter, Segoe UI, Arial, sans-serif">{html.escape(str(focus_pinyin))}</text>
  {_text_lines(gloss_lines, 650, 286, 34, "#f8fafc", 900, 44)}
  {_text_lines(goal_lines, 650, 388, 22, "#cbd5e1", 600, 34)}
  {"".join(cards)}
</svg>'''


def _render_remotion_slides(
    *,
    json_path: Path,
    lesson_digits: str,
    pipeline_id: str,
    lang: str,
    expected_count: int,
) -> tuple[Path, str]:
    frontend_dir = default_paths().project_root / "frontend"
    render_script = frontend_dir / "scripts" / "render-explanation-slides.mjs"
    if not render_script.exists():
        raise FileNotFoundError(f"Missing Remotion slide render script: {render_script}")

    subprocess.run(
        ["node", str(render_script), lesson_digits, lang, pipeline_id, str(json_path.resolve())],
        cwd=str(frontend_dir),
        check=True,
    )

    paths = default_paths()
    pipeline = get_pipeline(pipeline_id)
    slide_dir = pipeline.artifact_root(paths) / "output_slides" / lang / f"lesson{lesson_digits}"
    missing = [
        slide_dir / f"slide_{index:03d}.png"
        for index in range(1, expected_count + 1)
        if not (slide_dir / f"slide_{index:03d}.png").exists()
    ]
    if missing:
        raise FileNotFoundError(f"Remotion did not create expected slide(s): {missing[:3]}")
    return slide_dir, ".png"


def build_deck(
    json_path: Path,
    pipeline_id: str,
    lang: str,
    force: bool = False,
    renderer: str = "remotion",
) -> dict:
    paths = default_paths()
    load_dotenv(paths.backend_dir / ".env")
    pipeline = get_pipeline(pipeline_id)
    artifact_root = pipeline.artifact_root(paths)

    with json_path.open(encoding="utf-8") as f:
        data = json.load(f)

    hydrated_glosses = _hydrate_missing_line_glosses(data)
    _normalize_explanation_timeline(data)
    if hydrated_glosses:
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  🧩 已从现有例句/课文翻译回填 line_focus 翻译: {hydrated_glosses} 条")
    else:
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    metadata = data.get("lesson_metadata") or {}
    lesson_digits = _lesson_digits(metadata.get("lesson_id") or json_path.stem)
    lesson_title = metadata.get("title") or f"lesson{lesson_digits}"
    plan = ((data.get("video_render_plan") or {}).get("explanation") or {})
    segments = [s for s in plan.get("segments") or [] if isinstance(s, dict)]
    if not segments:
        raise ValueError("video_render_plan.explanation.segments is empty")

    slide_dir = artifact_root / "output_slides" / lang / f"lesson{lesson_digits}"
    slide_dir.mkdir(parents=True, exist_ok=True)

    image_suffix = ".svg"
    if renderer == "remotion":
        try:
            slide_dir, image_suffix = _render_remotion_slides(
                json_path=json_path,
                lesson_digits=lesson_digits,
                pipeline_id=pipeline_id,
                lang=lang,
                expected_count=len(segments),
            )
        except Exception as exc:
            print(f"⚠️ Remotion 静态幻灯片导出失败，回退到简易 SVG: {exc}")
            image_suffix = ".svg"
    elif renderer != "svg":
        raise ValueError(f"Unsupported slide renderer: {renderer}")

    suffix = f"_{lang}" if lang != "en" else ""
    narration_file = (
        artifact_root / "output_audio" / f"lesson{lesson_digits}_narration{suffix}" / f"lesson{lesson_digits}_narration{suffix}.mp3"
    )
    recorded = data.get("explanation_narration_audio") or {}
    if recorded.get("status") == "ok" and recorded.get("audio_file"):
        candidate = Path(recorded["audio_file"])
        if candidate.exists():
            narration_file = candidate

    slides = []
    for index, segment in enumerate(segments, start=1):
        filename = f"slide_{index:03d}{image_suffix}"
        local_path = slide_dir / filename
        if image_suffix == ".svg" and (force or not local_path.exists()):
            local_path.write_text(_svg_for_segment(segment, lesson_title, index, len(segments)), encoding="utf-8")

        start_ms = int(round(float(segment.get("start_time_seconds") or 0) * 1000))
        duration_ms = int(round(float(segment.get("duration_seconds") or 0) * 1000))
        if duration_ms <= 0:
            duration_ms = max(4000, len(_caption_cues(segment)) * 3500)
        slide_audio_file = _split_narration_audio(
            narration_file=narration_file,
            output_dir=narration_file.parent,
            lesson_digits=lesson_digits,
            lang=lang,
            slide_index=index,
            start_ms=start_ms,
            duration_ms=duration_ms,
            force=force,
        )
        audio_name = slide_audio_file.name
        audio_object_key = f"{pipeline.target_language}/audio/narration/{lang}/lesson{lesson_digits}/{audio_name}"
        audio_media_path = f"/media/teaching-audio/{pipeline.pipeline_id}/{lang}/{lesson_digits}/{audio_name}"

        slides.append({
            "id": f"seg_{index:03d}",
            "segment_id": segment.get("segment_id") or index,
            "title": segment.get("segment_title") or f"Slide {index}",
            "duration_ms": duration_ms,
            "image": {
                "local_path": str(local_path),
                "object_key": f"{pipeline.target_language}/slides/{lang}/lesson{lesson_digits}/{filename}",
                "media_path": f"/media/teaching-slide/{pipeline.pipeline_id}/{lang}/{lesson_digits}/{filename}",
                "media_url": "",
            },
            "audio": {
                "local_path": str(slide_audio_file),
                "object_key": audio_object_key,
                "media_path": audio_media_path,
                "media_url": "",
                "source_start_ms": start_ms,
                "start_ms": 0,
                "end_ms": duration_ms,
            },
            "caption_cues": _caption_cues(segment),
        })

    deck = {
        "version": "1.0",
        "kind": "static_slide_deck",
        "pipeline_id": pipeline.pipeline_id,
        "lesson_id": int(lesson_digits),
        "lang": lang,
        "slide_count": len(slides),
        "slides": slides,
    }

    data["teaching_slide_deck"] = deck
    data.setdefault("video_render_plan", {})["teaching_slide_deck"] = deck

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return deck


def main() -> None:
    parser = argparse.ArgumentParser(description="Build static teaching slide deck assets from a lesson JSON.")
    parser.add_argument("json_file", type=Path)
    parser.add_argument("--pipeline", default="integrated_chinese")
    parser.add_argument("--lang", default="en")
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--renderer",
        default="remotion",
        choices=["remotion", "svg"],
        help="Slide image renderer. remotion reuses the existing video templates; svg is a lightweight fallback.",
    )
    args = parser.parse_args()

    deck = build_deck(args.json_file, args.pipeline, args.lang, force=args.force, renderer=args.renderer)
    print(f"✅ Built {deck['slide_count']} slides for lesson{deck['lesson_id']} ({deck['pipeline_id']}/{deck['lang']}).")


if __name__ == "__main__":
    main()
