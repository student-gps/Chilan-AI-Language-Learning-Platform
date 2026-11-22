import argparse
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image as _PilImage
    _PILLOW_AVAILABLE = True
except ImportError:
    _PILLOW_AVAILABLE = False

_WEBP_QUALITY = 85

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[4]
CONTENT_BUILDER_DIR = BACKEND_DIR / "content_builder"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from content_builder.core.artifacts import atomic_write_json, code_digest, file_digest, fingerprint, resolve_artifact_path
from content_builder.core.paths import default_paths
from content_builder.core.pipeline import get_pipeline
from config.env import get_env, get_env_int


_SLIDE_AUDIO_BITRATE = get_env("SLIDE_AUDIO_MP3_BITRATE", default="40k")
_SLIDE_AUDIO_SAMPLE_RATE = get_env_int("SLIDE_AUDIO_SAMPLE_RATE", default=24000)
_SLIDE_AUDIO_CHANNELS = get_env_int("SLIDE_AUDIO_CHANNELS", default=1)


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
        if len(timings) != len(sentences):
            raise ValueError("Caption sentences do not match measured TTS timings")
    else:
        starts = [int(round(duration_ms * i / len(sentences))) for i in range(len(sentences))]

    for index, sentence in enumerate(sentences):
        start_ms = starts[index]
        end_ms = starts[index + 1] if index + 1 < len(starts) else duration_ms
        if not 0 <= start_ms < end_ms <= duration_ms:
            raise ValueError("Caption timestamps must be ordered and within the audio segment")
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
    if not narration_file.is_file():
        raise FileNotFoundError(f"Narration missing: {narration_file}")
    signature = fingerprint({"source": file_digest(narration_file), "start_ms": start_ms,
                             "duration_ms": duration_ms, "bitrate": _SLIDE_AUDIO_BITRATE,
                             "sample_rate": _SLIDE_AUDIO_SAMPLE_RATE, "channels": _SLIDE_AUDIO_CHANNELS})[:16]
    output_file = output_dir / f"lesson{lesson_digits}_slide_{slide_index:03d}{suffix}_{signature}.mp3"
    if output_file.is_file() and output_file.stat().st_size > 0 and not force:
        return output_file

    output_dir.mkdir(parents=True, exist_ok=True)
    start_seconds = max(0, start_ms) / 1000
    duration_seconds = max(0.5, duration_ms / 1000)
    temporary_file = output_file.with_suffix(".tmp.mp3")
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
            "-ac",
            str(_SLIDE_AUDIO_CHANNELS),
            "-ar",
            str(_SLIDE_AUDIO_SAMPLE_RATE),
            "-b:a",
            _SLIDE_AUDIO_BITRATE,
            "-f",
            "mp3",
            str(temporary_file),
        ],
        check=True,
    )
    try:
        probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(temporary_file)], capture_output=True, text=True, check=True)
        actual = float(json.loads(probe.stdout)["format"]["duration"])
        if abs(actual - duration_seconds) > 0.3:
            raise ValueError(f"Slide audio is truncated: expected {duration_seconds:.3f}s, got {actual:.3f}s")
        temporary_file.replace(output_file)
    finally:
        temporary_file.unlink(missing_ok=True)
    return output_file


def _narration_file_candidates(artifact_root: Path, lesson_digits: str, lang: str) -> list[Path]:
    suffix = f"_{lang}" if lang != "en" else ""
    filename = f"lesson{lesson_digits}_narration{suffix}.mp3"
    return [
        artifact_root / "output_audio" / lang / f"lesson{lesson_digits}_narration" / filename,
        artifact_root / "output_audio" / f"lesson{lesson_digits}_narration{suffix}" / filename,
    ]


def _resolve_narration_file(data: dict, artifact_root: Path, lesson_digits: str, lang: str) -> Path:
    recorded = data.get("explanation_narration_audio") or {}
    if recorded.get("audio_file"):
        try:
            return resolve_artifact_path(recorded["audio_file"], artifact_root)
        except FileNotFoundError:
            pass
    for candidate in _narration_file_candidates(artifact_root, lesson_digits, lang):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"Narration not found for lesson{lesson_digits}/{lang}")


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


def _convert_pngs_to_webp(slide_dir: Path, count: int) -> None:
    """Convert slide_001.png … slide_NNN.png to WebP q85 and delete originals."""
    if not _PILLOW_AVAILABLE:
        raise RuntimeError("Pillow is required to produce WebP slide images")
    for index in range(1, count + 1):
        png = slide_dir / f"slide_{index:03d}.png"
        if not png.exists():
            continue
        webp = png.with_suffix(".webp")
        temporary = webp.with_suffix(".tmp.webp")
        try:
            with _PilImage.open(png) as bitmap:
                bitmap.save(temporary, "WEBP", quality=_WEBP_QUALITY, method=6)
            with _PilImage.open(temporary) as bitmap:
                bitmap.verify()
            temporary.replace(webp)
            png.unlink()
        finally:
            temporary.unlink(missing_ok=True)
    print(f"  🗜️ 已转换 {count} 张 PNG → WebP q{_WEBP_QUALITY}")


def _render_remotion_slides(
    *,
    json_path: Path,
    lesson_digits: str,
    pipeline_id: str,
    lang: str,
    expected_count: int,
    output_dir: Path | None = None,
) -> tuple[Path, str]:
    frontend_dir = default_paths().project_root / "frontend"
    render_script = frontend_dir / "scripts" / "render-explanation-slides.mjs"
    if not render_script.exists():
        raise FileNotFoundError(f"Missing Remotion slide render script: {render_script}")

    subprocess.run(
        ["node", str(render_script), lesson_digits, lang, pipeline_id, str(json_path.resolve()), "", str(output_dir.resolve()) if output_dir else ""],
        cwd=str(frontend_dir),
        check=True,
    )

    paths = default_paths()
    pipeline = get_pipeline(pipeline_id)
    slide_dir = output_dir or pipeline.artifact_root(paths) / "output_slides" / lang / f"lesson{lesson_digits}"
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
    images_only: bool = False,
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

    previous_slides = (data.get("teaching_slide_deck") or {}).get("slides") or []
    narration_file = None if images_only else _resolve_narration_file(data, artifact_root, lesson_digits, lang)
    if images_only:
        if len(previous_slides) != len(segments):
            raise ValueError("Image-only refresh requires an existing slide/audio pair for every segment")
        for segment, previous in zip(segments, previous_slides):
            track = segment.get("narration_track") or {}
            text = track.get(f"subtitle_{lang}") or track.get("script") or track.get("subtitle_en") or ""
            captions = "".join(cue.get("text", "") for cue in previous.get("caption_cues", []))
            if (previous.get("segment_id") != segment.get("segment_id") or
                abs(float(previous.get("duration_ms", 0)) - float(segment.get("duration_seconds", 0)) * 1000) > 2 or
                re.sub(r"\s+", "", text) != re.sub(r"\s+", "", captions)):
                raise ValueError("Narration or timing changed; run the narration stage before rebuilding slide audio")
            resolve_artifact_path((previous.get("audio") or {}).get("local_path", ""), artifact_root)

    slide_dir = artifact_root / "output_slides" / lang / f"lesson{lesson_digits}"
    slide_dir.mkdir(parents=True, exist_ok=True)

    static_fields = [{key: value for key, value in segment.items() if key not in {
        "narration_track", "sentence_texts", "sentence_timings_seconds", "visual_notes",
        "duration_seconds", "start_time_seconds", "end_time_seconds",
    }} for segment in segments]
    frontend = paths.project_root / "frontend"
    render_signature = fingerprint({"version": 3, "renderer": renderer, "lang": lang, "boards": static_fields,
        "quality": _WEBP_QUALITY, "code": code_digest([
            Path(__file__), frontend / "src/videoTemplates/explanation",
            frontend / "remotion/ExplanationLessonSlide.jsx", frontend / "scripts/slide-render-utils.mjs",
            frontend / "scripts/render-explanation-slides.mjs", frontend / "package-lock.json",
        ])})
    image_suffix = ".svg"
    image_token = render_signature[:16]
    if renderer == "remotion":
        expected = [slide_dir / f"slide_{i:03d}_{image_token}.webp" for i in range(1, len(segments) + 1)]
        if not force and all(path.is_file() and path.stat().st_size > 0 for path in expected):
            print(f"  Reusing {len(expected)} images with matching teaching data and template recipe.")
        else:
            with tempfile.TemporaryDirectory(prefix=".render_", dir=slide_dir) as temporary:
                staging = Path(temporary).resolve()
                if not staging.is_relative_to(slide_dir.resolve()):
                    raise ValueError("Render staging path must be inside this lesson's slide directory")
                _render_remotion_slides(json_path=json_path, lesson_digits=lesson_digits,
                    pipeline_id=pipeline_id, lang=lang, expected_count=len(segments), output_dir=staging)
                _convert_pngs_to_webp(staging, len(segments))
                for i, destination in enumerate(expected, start=1):
                    (staging / f"slide_{i:03d}.webp").replace(destination)
        image_suffix = ".webp"
    elif renderer != "svg":
        raise ValueError(f"Unsupported slide renderer: {renderer}")

    slides = []
    for index, segment in enumerate(segments, start=1):
        filename = f"slide_{index:03d}_{image_token}{image_suffix}"
        local_path = slide_dir / filename
        if image_suffix == ".svg" and (force or not local_path.exists()):
            local_path.write_text(_svg_for_segment(segment, lesson_title, index, len(segments)), encoding="utf-8")

        start_ms = int(round(float(segment.get("start_time_seconds") or 0) * 1000))
        duration_ms = int(round(float(segment.get("duration_seconds") or 0) * 1000))
        if duration_ms <= 0:
            duration_ms = max(4000, len(_caption_cues(segment)) * 3500)
        slide_audio_file = resolve_artifact_path(previous_slides[index - 1]["audio"]["local_path"], artifact_root) if images_only else _split_narration_audio(
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
        "render_recipe": {"version": 3, "fingerprint": render_signature, "renderer": renderer,
                          "caption_mode": "external", "width": 1920, "height": 1080,
                          "image_format": "webp" if renderer == "remotion" else "svg", "webp_quality": _WEBP_QUALITY},
        "slides": slides,
    }

    data["teaching_slide_deck"] = deck
    data.setdefault("video_render_plan", {})["teaching_slide_deck"] = deck

    atomic_write_json(json_path, data)
    return deck


def main() -> None:
    parser = argparse.ArgumentParser(description="Build static teaching slide deck assets from a lesson JSON.")
    parser.add_argument("json_file", type=Path)
    parser.add_argument("--pipeline", default="integrated_chinese")
    parser.add_argument("--lang", default="en")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--images-only", action="store_true", help="Refresh images while preserving verified existing audio and captions.")
    parser.add_argument(
        "--renderer",
        default="remotion",
        choices=["remotion", "svg"],
        help="Slide image renderer. remotion reuses the existing video templates; svg is a lightweight fallback.",
    )
    args = parser.parse_args()

    deck = build_deck(args.json_file, args.pipeline, args.lang, force=args.force, renderer=args.renderer, images_only=args.images_only)
    print(f"✅ Built {deck['slide_count']} slides for lesson{deck['lesson_id']} ({deck['pipeline_id']}/{deck['lang']}).")


if __name__ == "__main__":
    main()
