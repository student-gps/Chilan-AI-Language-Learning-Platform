"""Small, dependency-free primitives for reproducible offline builds."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import tempfile
from pathlib import Path


def fingerprint(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def file_digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def code_digest(paths: list[Path]) -> str:
    files = []
    for path in paths:
        files.extend(sorted(path.rglob("*.jsx")) + sorted(path.rglob("*.js")) + sorted(path.rglob("*.py")) if path.is_dir() else [path])
    return fingerprint([(path.name, file_digest(path)) for path in files if path.is_file()])


def atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def resolve_artifact_path(value: str, root: Path) -> Path:
    """Relocate exported absolute paths after a checkout moves computers."""
    if not value:
        raise ValueError("Empty artifact path")
    raw = Path(value)
    if raw.is_file():
        return raw.resolve()
    parts = value.replace("\\", "/").split("/")
    if "artifacts" in parts:
        tail = parts[parts.index("artifacts") + 1:]
        if tail and tail[0] in {"integrated_chinese", "new_concept_english", "minna_no_nihongo"}:
            tail = tail[1:]
        candidate = root.joinpath(*tail)
        if candidate.is_file():
            return candidate.resolve()
        if len(tail) >= 3 and tail[0] == "output_audio" and "narration" in tail[1]:
            match = re.search(r"_(ar|de|es|fr|id|it|ja|ko|ms|pt|ru|th|vi|zh)$", tail[1])
            lang = match.group(1) if match else "en"
            folder = tail[1][:match.start()] if match else tail[1]
            candidate = root / "output_audio" / lang / folder / Path(*tail[2:])
            if candidate.is_file():
                return candidate.resolve()
    raise FileNotFoundError(value)


def narration_fingerprint(data: dict, lang: str) -> str:
    segments = data.get("video_render_plan", {}).get("explanation", {}).get("segments", [])
    texts = []
    for segment in segments:
        track = segment.get("narration_track") or {}
        text = track.get(f"subtitle_{lang}") or track.get("script") or track.get("subtitle_en") or track.get("subtitle_zh") or ""
        texts.append({"id": segment.get("segment_id"), "text": text})
    # Persist only a digest; credentials never enter a manifest or log.
    settings = {key: value for key, value in os.environ.items() if key.startswith("TTS_") and not any(token in key for token in ("KEY", "SECRET", "TOKEN", "PASSWORD"))}
    narrator_code = Path(__file__).resolve().parents[1] / "zh/integrated_chinese/tasks/narration_audio.py"
    return fingerprint({"recipe": 2, "lang": lang, "texts": texts, "settings": settings, "code": file_digest(narrator_code)})


def apply_narration_timings(data: dict, result: dict) -> None:
    """Require complete measured timings; never manufacture an 'ok' audio track."""
    if result.get("status") != "ok" or not Path(result.get("audio_file") or "").is_file():
        raise ValueError(f"Narration is not ready: {result.get('reason', 'audio missing')}")
    plan = data["video_render_plan"]["explanation"]
    segments = plan["segments"]
    if result.get("segment_count") != len(segments):
        raise ValueError("Narration segment_count does not match render plan")
    cursor = 0.0
    for segment in segments:
        key = str(segment.get("segment_id") or segment.get("segment_order", ""))
        duration = float(result.get("segment_actual_durations", {}).get(key) or 0)
        sentences = result.get("segment_sentences", {}).get(key, [])
        starts = result.get("segment_timings", {}).get(key, [])
        if not math.isfinite(duration) or duration <= 0 or not sentences or len(sentences) != len(starts):
            raise ValueError(f"Incomplete narration timing for segment {key}")
        if starts[0] != 0 or any(not math.isfinite(float(t)) or t < 0 or t >= duration for t in starts) or any(a >= b for a, b in zip(starts, starts[1:])):
            raise ValueError(f"Invalid narration timing for segment {key}")
        segment.update(duration_seconds=duration, sentence_texts=sentences, sentence_timings_seconds=starts,
                       start_time_seconds=round(cursor, 3), end_time_seconds=round(cursor + duration, 3))
        cursor += duration
    plan["timeline"] = {"segment_count": len(segments), "total_duration_seconds": round(cursor, 3)}
