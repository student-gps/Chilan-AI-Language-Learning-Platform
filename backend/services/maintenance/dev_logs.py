from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Iterator


BACKEND_DIR = Path(__file__).resolve().parents[2]


def make_dev_log_path(
    *,
    kind: str,
    pipeline: str,
    lang: str = "",
    lesson_start: int | None = None,
    lesson_end: int | None = None,
    course_id: int | str | None = None,
) -> Path:
    if pipeline == "minna_no_nihongo":
        root = BACKEND_DIR / "content_builder" / "ja" / "minna_no_nihongo" / "artifacts" / "logs"
    else:
        root = BACKEND_DIR / "artifacts" / "logs"
    root.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pieces = [safe_log_piece(kind), safe_log_piece(pipeline)]
    if lang:
        pieces.append(safe_log_piece(lang))
    if course_id not in {None, ""}:
        pieces.append(f"course{safe_log_piece(course_id)}")
    if lesson_start is not None:
        if lesson_end is not None and lesson_end != lesson_start:
            pieces.append(f"lesson{int(lesson_start):03d}-{int(lesson_end):03d}")
        else:
            pieces.append(f"lesson{int(lesson_start):03d}")
    pieces.append(timestamp)
    return root / f"{'_'.join(piece for piece in pieces if piece)}.log"


def safe_log_piece(value: Any) -> str:
    text = str(value or "").strip()
    return "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in text)


def stream_events_with_log(
    events: Iterable[dict[str, Any]],
    *,
    log_path: Path,
    start_message: str,
) -> Iterator[dict[str, Any]]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8", newline="\n") as handle:
        meta_event = {
            "type": "log_file",
            "message": start_message,
            "log_path": str(log_path),
            "log_dir": str(log_path.parent),
        }
        _write_event(handle, meta_event)
        yield meta_event
        for event in events:
            _write_event(handle, event)
            yield event


def _write_event(handle, event: dict[str, Any]) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    event_type = event.get("type") or "info"
    message = event.get("message") or ""
    handle.write(f"[{timestamp}] [{event_type}] {message}\n")
    if event.get("argv"):
        handle.write(f"  command: {_command_for_log(event.get('argv'))}\n")
    if event.get("log_path") and event_type != "log_file":
        handle.write(f"  log_path: {event.get('log_path')}\n")
    if event_type in {"fatal", "command_failed", "lesson_failed"}:
        handle.write(f"  event: {json.dumps(event, ensure_ascii=False, default=str)}\n")
    handle.flush()


def _command_for_log(argv: Any) -> str:
    if not isinstance(argv, list):
        return str(argv or "")
    return " ".join(_quote_arg(str(arg)) for arg in argv)


def _quote_arg(arg: str) -> str:
    if not arg:
        return '""'
    if any(char.isspace() for char in arg):
        return f'"{arg}"'
    return arg
