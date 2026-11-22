from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[4]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from config.env import get_env, get_env_int
from content_builder.core.paths import default_paths
from content_builder.core.pipeline import get_pipeline


_SLIDE_AUDIO_BITRATE = get_env("SLIDE_AUDIO_MP3_BITRATE", default="40k")
_SLIDE_AUDIO_SAMPLE_RATE = get_env_int("SLIDE_AUDIO_SAMPLE_RATE", default=24000)
_SLIDE_AUDIO_CHANNELS = get_env_int("SLIDE_AUDIO_CHANNELS", default=1)


def _lesson_digits(value) -> str:
    digits = re.findall(r"\d+", str(value or ""))
    if not digits:
        raise ValueError(f"Cannot parse lesson id from {value!r}")
    return f"{int(digits[0]):03d}"


def _narration_text(segment: dict, lang: str) -> str:
    track = segment.get("narration_track") if isinstance(segment.get("narration_track"), dict) else {}
    return (
        track.get(f"subtitle_{lang}")
        or track.get("script")
        or track.get("subtitle_zh")
        or track.get("subtitle_en")
        or ""
    ).strip()


def _split_sentences(text: str) -> list[str]:
    if not text:
        return []
    parts = re.findall(r"[^。！？!?]+[。！？!?]?", text.strip())
    return [part.strip() for part in parts if part.strip()]


_CAPTION_ORPHAN_PUNCT_RE = re.compile(r"^[\s'\"“”‘’「」『』（）()［］\[\]{}，,。.!！？?；;：:、…·・~-]+$")


def _normalize_caption_sentences(sentences: list[str]) -> list[str]:
    normalized: list[str] = []
    for raw in sentences:
        sentence = str(raw or "").strip()
        if not sentence:
            continue
        if _CAPTION_ORPHAN_PUNCT_RE.fullmatch(sentence):
            if normalized:
                normalized[-1] = f"{normalized[-1]}{sentence}"
            continue
        normalized.append(sentence)
    return normalized


def _caption_cues(segment: dict, lang: str) -> list[dict]:
    sentences = segment.get("sentence_texts")
    if isinstance(sentences, list):
        sentence_texts = [str(item).strip() for item in sentences if str(item).strip()]
    else:
        sentence_texts = _split_sentences(_narration_text(segment, lang))
    sentence_texts = _normalize_caption_sentences(sentence_texts)
    if not sentence_texts:
        return []

    duration_ms = int(round(float(segment.get("duration_seconds") or 0) * 1000))
    if duration_ms <= 0:
        duration_ms = max(4000, len(sentence_texts) * 3000)
    timings = segment.get("sentence_timings_seconds")
    if isinstance(timings, list) and timings:
        starts = [max(0, int(round(float(item or 0) * 1000))) for item in timings[: len(sentence_texts)]]
        while len(starts) < len(sentence_texts):
            starts.append(int(round(duration_ms * len(starts) / len(sentence_texts))))
    else:
        starts = [int(round(duration_ms * index / len(sentence_texts))) for index in range(len(sentence_texts))]

    cues = []
    for index, sentence in enumerate(sentence_texts):
        start_ms = min(starts[index], max(duration_ms - 300, 0))
        end_ms = starts[index + 1] if index + 1 < len(starts) else duration_ms
        end_ms = max(start_ms + 500, min(end_ms, duration_ms))
        cues.append({"start_ms": start_ms, "end_ms": end_ms, "text": sentence})
    return cues


def _wrap_cjk(text: str, max_chars: int) -> list[str]:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if not text:
        return []
    lines = []
    current = ""
    for char in text:
        candidate = f"{current}{char}"
        if current and len(candidate) > max_chars:
            lines.append(current)
            current = char
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _text_lines(lines: list[str], x: int, y: int, size: int, color: str, weight: int = 700, gap: int | None = None) -> str:
    gap = gap or int(size * 1.45)
    return "\n".join(
        f'<text x="{x}" y="{y + offset * gap}" fill="{color}" font-size="{size}" '
        f'font-weight="{weight}" font-family="Yu Gothic, Meiryo, Noto Sans JP, Segoe UI, sans-serif">{html.escape(line)}</text>'
        for offset, line in enumerate(lines)
    )


def _items_from_first_block(segment: dict) -> dict:
    blocks = segment.get("visual_blocks") if isinstance(segment.get("visual_blocks"), list) else []
    for block in blocks:
        if isinstance(block, dict) and isinstance(block.get("content"), dict):
            return block["content"]
    return {}


def _line_text(item: dict) -> tuple[str, str, str]:
    return (
        str(item.get("text") or item.get("term") or item.get("title") or "").strip(),
        str(item.get("reading") or item.get("romaji") or "").strip(),
        str(item.get("translation") or item.get("definition") or "").strip(),
    )


def _select_rows(segment: dict) -> list[tuple[str, str, str]]:
    content = _items_from_first_block(segment)
    block_items = content.get("items") or content.get("lines") or content.get("sections") or []
    rows: list[tuple[str, str, str]] = []
    for item in block_items if isinstance(block_items, list) else []:
        if not isinstance(item, dict):
            continue
        if segment.get("segment_type") == "grammar_focus":
            examples = item.get("examples") if isinstance(item.get("examples"), list) else []
            example = examples[0] if examples and isinstance(examples[0], dict) else {}
            rows.append((
                str(item.get("title") or "").strip(),
                str(example.get("text") or "").strip(),
                str(item.get("explanation") or example.get("translation") or "").strip(),
            ))
        elif "vocabulary" in str(segment.get("segment_type") or ""):
            rows.append(_line_text(item))
        else:
            rows.append(_line_text(item))
    return [row for row in rows if any(row)][:8]


def _svg_for_segment(segment: dict, lesson_title: str, slide_index: int, total: int) -> str:
    title = str(segment.get("segment_title") or f"Slide {slide_index}").strip()
    goal = str(segment.get("teaching_goal") or "").strip()
    rows = _select_rows(segment)
    title_lines = _wrap_cjk(title, 28)[:2]
    goal_lines = _wrap_cjk(goal, 44)[:2]
    row_svg = []
    start_y = 250
    for index, (primary, reading, translation) in enumerate(rows):
        y = start_y + index * 78
        row_svg.append(
            f'<rect x="92" y="{y - 44}" width="1096" height="64" rx="14" fill="rgba(255,255,255,0.72)" '
            f'stroke="rgba(15,23,42,0.08)"/>'
            f'<text x="118" y="{y - 10}" fill="#111827" font-size="30" font-weight="900" '
            f'font-family="Yu Gothic, Meiryo, Noto Sans JP, sans-serif">{html.escape(primary[:46])}</text>'
            f'<text x="118" y="{y + 16}" fill="#0f766e" font-size="18" font-weight="800" '
            f'font-family="Yu Gothic, Meiryo, Noto Sans JP, sans-serif">{html.escape(reading[:70])}</text>'
            f'<text x="740" y="{y + 2}" fill="#475569" font-size="22" font-weight="700" '
            f'font-family="Microsoft YaHei, Segoe UI, sans-serif">{html.escape(translation[:28])}</text>'
        )
    if not row_svg:
        row_svg.append(
            '<text x="92" y="304" fill="#334155" font-size="34" font-weight="800" '
            'font-family="Microsoft YaHei, Segoe UI, sans-serif">本页内容来自当前课程段落。</text>'
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <rect width="1280" height="720" fill="#f8fafc"/>
  <rect x="0" y="0" width="1280" height="154" fill="#0f766e"/>
  <rect x="0" y="154" width="1280" height="18" fill="#f59e0b"/>
  <text x="72" y="66" fill="#ccfbf1" font-size="18" font-weight="900" letter-spacing="3"
    font-family="Inter, Segoe UI, sans-serif">MINNA NO NIHONGO · {html.escape(lesson_title)} · {slide_index}/{total}</text>
  {_text_lines(title_lines, 72, 118, 42, "#ffffff", 900, 48)}
  {_text_lines(goal_lines, 72, 208, 24, "#334155", 700, 34)}
  {"".join(row_svg)}
</svg>'''


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


def _resolve_narration_file(data: dict, artifact_root: Path, lesson_digits: str, lang: str) -> Path:
    suffix = f"_{lang}" if lang != "en" else ""
    expected = artifact_root / "output_audio" / lang / f"lesson{lesson_digits}_narration" / f"lesson{lesson_digits}_narration{suffix}.mp3"
    legacy_expected = artifact_root / "output_audio" / f"lesson{lesson_digits}_narration{suffix}" / f"lesson{lesson_digits}_narration{suffix}.mp3"
    recorded = data.get("explanation_narration_audio") if isinstance(data.get("explanation_narration_audio"), dict) else {}
    audio_file = recorded.get("audio_file") if isinstance(recorded, dict) else ""
    if audio_file and Path(audio_file).exists():
        return Path(audio_file)
    if expected.exists():
        return expected
    if legacy_expected.exists():
        return legacy_expected
    return expected


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
    if not narration_file.exists():
        return narration_file
    if output_file.exists() and not force:
        try:
            if output_file.stat().st_mtime >= narration_file.stat().st_mtime:
                return output_file
        except OSError:
            pass

    output_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{max(0, start_ms) / 1000:.3f}",
            "-t",
            f"{max(0.5, duration_ms / 1000):.3f}",
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
            str(output_file),
        ],
        check=True,
    )
    return output_file


def _cleanup_stale_slide_assets(*, slide_dir: Path, audio_dir: Path, lesson_digits: str, lang: str, slide_count: int) -> None:
    valid_image_names = {f"slide_{index:03d}.png" for index in range(1, slide_count + 1)}
    valid_image_names.update(f"slide_{index:03d}.svg" for index in range(1, slide_count + 1))
    for path in list(slide_dir.glob("slide_*.png")) + list(slide_dir.glob("slide_*.svg")):
        if path.name not in valid_image_names:
            path.unlink(missing_ok=True)

    suffix = f"_{lang}" if lang != "en" else ""
    valid_audio_names = {
        f"lesson{lesson_digits}_slide_{index:03d}{suffix}.mp3"
        for index in range(1, slide_count + 1)
    }
    for path in audio_dir.glob(f"lesson{lesson_digits}_slide_*{suffix}.mp3"):
        if path.name not in valid_audio_names:
            path.unlink(missing_ok=True)


def _render_remotion_slides(
    *,
    json_path: Path,
    lesson_digits: str,
    pipeline_id: str,
    lang: str,
    expected_count: int,
    only_slide: int | None = None,
) -> tuple[Path, str]:
    frontend_dir = default_paths().project_root / "frontend"
    render_script = frontend_dir / "scripts" / "render-explanation-slides.mjs"
    if not render_script.exists():
        raise FileNotFoundError(f"Missing Remotion slide render script: {render_script}")

    command = ["node", str(render_script), lesson_digits, lang, pipeline_id, str(json_path.resolve())]
    if only_slide is not None:
        command.append(str(only_slide))

    subprocess.run(
        command,
        cwd=str(frontend_dir),
        check=True,
    )

    paths = default_paths()
    pipeline = get_pipeline(pipeline_id)
    slide_dir = pipeline.artifact_root(paths) / "output_slides" / lang / f"lesson{lesson_digits}"
    expected_indexes = [only_slide] if only_slide is not None else list(range(1, expected_count + 1))
    missing = [
        slide_dir / f"slide_{index:03d}.png"
        for index in expected_indexes
        if not (slide_dir / f"slide_{index:03d}.png").exists()
    ]
    if missing:
        raise FileNotFoundError(f"Remotion did not create expected slide(s): {missing[:3]}")
    return slide_dir, ".png"


def build_deck(
    json_path: Path,
    pipeline_id: str = "minna_no_nihongo",
    lang: str = "zh",
    force: bool = False,
    renderer: str = "remotion",
    write_json: bool = True,
    refresh_render_plan: bool = False,
    only_slide: int | None = None,
) -> dict:
    paths = default_paths()
    load_dotenv(paths.backend_dir / ".env")
    pipeline = get_pipeline(pipeline_id)
    artifact_root = pipeline.artifact_root(paths)

    with json_path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    if refresh_render_plan:
        if pipeline_id != "minna_no_nihongo":
            raise ValueError("--refresh-render-plan is only supported for minna_no_nihongo")
        from content_builder.ja.minna_no_nihongo.tasks.render_plan_builder import MinnaNoNihongoRenderPlanBuilder

        metadata = data.get("lesson_metadata") if isinstance(data.get("lesson_metadata"), dict) else {}
        course_content = data.get("course_content") if isinstance(data.get("course_content"), dict) else {}
        data["video_render_plan"] = MinnaNoNihongoRenderPlanBuilder().run(
            metadata,
            course_content,
            existing_plan=None,
        )

    _normalize_explanation_timeline(data)
    metadata = data.get("lesson_metadata") if isinstance(data.get("lesson_metadata"), dict) else {}
    lesson_digits = _lesson_digits(metadata.get("lesson_id") or json_path.stem)
    lesson_title = metadata.get("title_localized") or metadata.get("title") or f"lesson{lesson_digits}"
    plan = ((data.get("video_render_plan") or {}).get("explanation") or {})
    segments = [segment for segment in plan.get("segments") or [] if isinstance(segment, dict)]
    if not segments:
        raise ValueError("video_render_plan.explanation.segments is empty")
    if only_slide is not None and not (1 <= only_slide <= len(segments)):
        raise ValueError(f"--only-slide must be between 1 and {len(segments)}")

    slide_dir = artifact_root / "output_slides" / lang / f"lesson{lesson_digits}"
    slide_dir.mkdir(parents=True, exist_ok=True)
    narration_file = _resolve_narration_file(data, artifact_root, lesson_digits, lang)
    image_suffix = ".svg"
    render_json_path = json_path
    temporary_render_json: Path | None = None

    if renderer == "remotion":
        expected_indexes = [only_slide] if only_slide is not None else list(range(1, len(segments) + 1))
        expected_pngs = [slide_dir / f"slide_{index:03d}.png" for index in expected_indexes]
        if not force and all(path.exists() for path in expected_pngs):
            print(f"  ⏭️ 复用已有 Remotion PNG 幻灯片（共 {len(segments)} 张）")
            image_suffix = ".png"
        else:
            try:
                if refresh_render_plan:
                    handle = tempfile.NamedTemporaryFile(
                        mode="w",
                        encoding="utf-8",
                        suffix=".json",
                        prefix=f"lesson{lesson_digits}_render_plan_",
                        delete=False,
                    )
                    with handle:
                        json.dump(data, handle, ensure_ascii=False, indent=2)
                    temporary_render_json = Path(handle.name)
                    render_json_path = temporary_render_json
                slide_dir, image_suffix = _render_remotion_slides(
                    json_path=render_json_path,
                    lesson_digits=lesson_digits,
                    pipeline_id=pipeline_id,
                    lang=lang,
                    expected_count=len(segments),
                    only_slide=only_slide,
                )
            except Exception as exc:
                print(f"⚠️ Remotion 静态幻灯片导出失败，回退到简易 SVG: {exc}")
                image_suffix = ".svg"
            finally:
                if temporary_render_json and temporary_render_json.exists():
                    try:
                        temporary_render_json.unlink()
                    except OSError:
                        pass
    elif renderer != "svg":
        raise ValueError(f"Unsupported slide renderer: {renderer}")

    slides = []
    for index, segment in enumerate(segments, start=1):
        filename = f"slide_{index:03d}{image_suffix}"
        local_path = slide_dir / filename
        if image_suffix == ".svg" and (force or not local_path.exists()):
            local_path.write_text(_svg_for_segment(segment, lesson_title, index, len(segments)), encoding="utf-8")

        start_ms = int(round(float(segment.get("start_time_seconds") or 0) * 1000))
        duration_ms = int(round(float(segment.get("duration_seconds") or 0) * 1000))
        if duration_ms <= 0:
            duration_ms = max(4000, len(_caption_cues(segment, lang)) * 3000)
        slide_audio_file = _split_narration_audio(
            narration_file=narration_file,
            output_dir=narration_file.parent,
            lesson_digits=lesson_digits,
            lang=lang,
            slide_index=index,
            start_ms=start_ms,
            duration_ms=duration_ms,
            force=force and (only_slide is None or index == only_slide),
        )
        audio_name = slide_audio_file.name

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
                "object_key": f"{pipeline.target_language}/audio/narration/{lang}/lesson{lesson_digits}/{audio_name}",
                "media_path": f"/media/teaching-audio/{pipeline.pipeline_id}/{lang}/{lesson_digits}/{audio_name}",
                "media_url": "",
                "source_start_ms": start_ms,
                "start_ms": 0,
                "end_ms": duration_ms,
            },
            "caption_cues": _caption_cues(segment, lang),
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
    _cleanup_stale_slide_assets(
        slide_dir=slide_dir,
        audio_dir=narration_file.parent,
        lesson_digits=lesson_digits,
        lang=lang,
        slide_count=len(slides),
    )
    data["teaching_slide_deck"] = deck
    data.setdefault("video_render_plan", {})["teaching_slide_deck"] = deck
    if write_json:
        with json_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
    return deck


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Minna no Nihongo static teaching slide deck assets.")
    parser.add_argument("json_file", type=Path)
    parser.add_argument("--pipeline", default="minna_no_nihongo")
    parser.add_argument("--lang", default="zh")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--renderer", default="remotion", choices=["remotion", "svg"])
    parser.add_argument("--no-write-json", action="store_true")
    parser.add_argument(
        "--refresh-render-plan",
        action="store_true",
        help="Rebuild the render plan in memory before rendering; combine with --no-write-json to leave source JSON untouched.",
    )
    parser.add_argument("--only-slide", type=int, default=None, help="Render only one slide image by 1-based index.")
    args = parser.parse_args()

    deck = build_deck(
        args.json_file,
        pipeline_id=args.pipeline,
        lang=args.lang,
        force=args.force,
        renderer=args.renderer,
        write_json=not args.no_write_json,
        refresh_render_plan=args.refresh_render_plan,
        only_slide=args.only_slide,
    )
    print(f"✅ Built {deck['slide_count']} slides for lesson{deck['lesson_id']:03d} ({deck['pipeline_id']}/{deck['lang']}).")


if __name__ == "__main__":
    main()
