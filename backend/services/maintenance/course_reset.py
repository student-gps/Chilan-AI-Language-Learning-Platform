from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from content_builder.core.paths import default_paths
from content_builder.core.pipeline import get_pipeline
from database.connection import get_connection
from services.storage.media_storage import get_media_storage


VALID_ACTIONS = {"db", "r2", "restore_synced", "local_stage2"}


@dataclass(frozen=True)
class ResetRequest:
    pipeline: str
    course_id: int
    lang: str
    actions: tuple[str, ...]
    lesson_start: int | None = None
    lesson_end: int | None = None
    dry_run: bool = True
    confirm: bool = False
    confirm_code: str = ""


@dataclass
class ResetReport:
    request: dict[str, Any]
    db: dict[str, Any] = field(default_factory=dict)
    r2: dict[str, Any] = field(default_factory=dict)
    local: dict[str, Any] = field(default_factory=dict)
    restore_synced: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    executed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "request": self.request,
            "db": self.db,
            "r2": self.r2,
            "local": self.local,
            "restore_synced": self.restore_synced,
            "warnings": self.warnings,
            "executed": self.executed,
        }


def _lesson_slug(lesson_id: int) -> str:
    return f"lesson{lesson_id:03d}"


def _normalize_lesson_bounds(start: int | None, end: int | None) -> tuple[int | None, int | None]:
    if start is None and end is None:
        return None, None
    if start is None:
        start = end
    if end is None:
        end = start
    start = int(start)
    end = int(end)
    if start <= 0 or end <= 0:
        raise ValueError("lesson range must be positive")
    if start > end:
        raise ValueError("lesson_start must be <= lesson_end")
    return start, end


def normalize_actions(actions: list[str] | tuple[str, ...] | str | None) -> tuple[str, ...]:
    if actions is None:
        return tuple()
    if isinstance(actions, str):
        values = [part.strip() for part in actions.split(",")]
    else:
        values = [str(part).strip() for part in actions]
    normalized = tuple(part for part in values if part)
    invalid = sorted(set(normalized) - VALID_ACTIONS)
    if invalid:
        raise ValueError(f"unsupported reset action(s): {', '.join(invalid)}")
    return normalized


def build_request(
    *,
    pipeline: str,
    course_id: int,
    lang: str,
    actions: list[str] | tuple[str, ...] | str | None,
    lesson_start: int | None = None,
    lesson_end: int | None = None,
    dry_run: bool = True,
    confirm: bool = False,
    confirm_code: str = "",
) -> ResetRequest:
    start, end = _normalize_lesson_bounds(lesson_start, lesson_end)
    normalized_actions = normalize_actions(actions)
    if not normalized_actions:
        raise ValueError("at least one reset action is required")
    return ResetRequest(
        pipeline=str(pipeline or "").strip(),
        course_id=int(course_id),
        lang=str(lang or "").strip().lower(),
        actions=normalized_actions,
        lesson_start=start,
        lesson_end=end,
        dry_run=bool(dry_run),
        confirm=bool(confirm),
        confirm_code=str(confirm_code or "").strip(),
    )


def _artifact_root(pipeline_id: str) -> Path:
    return get_pipeline(pipeline_id).artifact_root(default_paths())


def _request_dict(req: ResetRequest) -> dict[str, Any]:
    return {
        "pipeline": req.pipeline,
        "course_id": req.course_id,
        "lang": req.lang,
        "actions": list(req.actions),
        "lesson_start": req.lesson_start,
        "lesson_end": req.lesson_end,
        "dry_run": req.dry_run,
        "confirm": req.confirm,
    }


def _lesson_filter_sql(req: ResetRequest, column: str = "lesson_id") -> tuple[str, list[Any]]:
    if req.lesson_start is None or req.lesson_end is None:
        return "", []
    return f" AND {column} BETWEEN %s AND %s", [req.lesson_start, req.lesson_end]


def _collect_db_counts(req: ResetRequest) -> dict[str, Any]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        lesson_clause, lesson_params = _lesson_filter_sql(req, "lesson_id")
        params = [req.course_id, *lesson_params]

        counts: dict[str, int] = {}
        for name, table in (
            ("lessons", "lessons"),
            ("language_items", "language_items"),
            ("vocabulary_knowledge", "vocabulary_knowledge"),
        ):
            cur.execute(f"SELECT COUNT(*) FROM {table} WHERE course_id = %s{lesson_clause}", params)
            counts[name] = int(cur.fetchone()[0])

        cur.execute("SELECT COUNT(*) FROM user_progress_of_lessons WHERE course_id = %s", (req.course_id,))
        counts["user_progress_of_lessons"] = int(cur.fetchone()[0])

        li_lesson_clause, li_lesson_params = _lesson_filter_sql(req, "li.lesson_id")
        cur.execute(
            f"""
            SELECT COUNT(*)
            FROM user_progress_of_language_items p
            JOIN language_items li ON li.item_id = p.item_id
            WHERE li.course_id = %s{li_lesson_clause}
            """,
            [req.course_id, *li_lesson_params],
        )
        counts["user_progress_of_language_items"] = int(cur.fetchone()[0])

        cur.execute(
            f"""
            SELECT lesson_id, title
            FROM lessons
            WHERE course_id = %s{lesson_clause}
            ORDER BY lesson_id ASC
            """,
            params,
        )
        lessons = [{"lesson_id": int(row[0]), "title": row[1]} for row in cur.fetchall()]
        return {"counts": counts, "lessons": lessons}
    finally:
        cur.close()
        conn.close()


def _extract_object_keys(payload: Any) -> set[str]:
    keys: set[str] = set()

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            object_key = value.get("object_key")
            if isinstance(object_key, str) and object_key.strip():
                keys.add(object_key.strip())
            for nested in value.values():
                walk(nested)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)
    return keys


def _json_lesson_id(path: Path) -> int | None:
    digits = "".join(ch for ch in path.stem if ch.isdigit())
    return int(digits) if digits else None


def _in_lesson_range(req: ResetRequest, lesson_id: int | None) -> bool:
    if req.lesson_start is None or req.lesson_end is None:
        return True
    if lesson_id is None:
        return False
    return req.lesson_start <= lesson_id <= req.lesson_end


def _json_files(req: ResetRequest) -> dict[str, list[Path]]:
    root = _artifact_root(req.pipeline)
    result = {
        "output_json": sorted((root / "output_json" / req.lang).glob("*_data*.json")),
        "synced_json": sorted((root / "synced_json" / req.lang).glob("*_data*.json")),
    }
    return {
        key: [path for path in paths if _in_lesson_range(req, _json_lesson_id(path))]
        for key, paths in result.items()
    }


def _collect_local_json_object_keys(req: ResetRequest) -> set[str]:
    keys: set[str] = set()
    for paths in _json_files(req).values():
        for path in paths:
            try:
                keys.update(_extract_object_keys(json.loads(path.read_text(encoding="utf-8"))))
            except Exception:
                continue
    return keys


def _collect_db_object_keys(req: ResetRequest) -> set[str]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        lesson_clause, lesson_params = _lesson_filter_sql(req, "lesson_id")
        cur.execute(
            f"""
            SELECT lesson_audio_assets, explanation_video_urls, video_render_plan, video_plan
            FROM lessons
            WHERE course_id = %s{lesson_clause}
            """,
            [req.course_id, *lesson_params],
        )
        keys: set[str] = set()
        for row in cur.fetchall():
            for payload in row:
                keys.update(_extract_object_keys(payload))
        return keys
    finally:
        cur.close()
        conn.close()


def _collect_restore_pairs(req: ResetRequest) -> list[dict[str, Any]]:
    root = _artifact_root(req.pipeline)
    output_dir = root / "output_json" / req.lang
    synced_dir = root / "synced_json" / req.lang
    pairs = []
    for src in sorted(synced_dir.glob("*_data*.json")):
        lesson_id = _json_lesson_id(src)
        if not _in_lesson_range(req, lesson_id):
            continue
        dst = output_dir / src.name
        pairs.append({
            "lesson_id": lesson_id,
            "source": str(src),
            "destination": str(dst),
            "destination_exists": dst.exists(),
        })
    return pairs


def _collect_local_stage2(req: ResetRequest) -> list[dict[str, Any]]:
    root = _artifact_root(req.pipeline)
    candidates: list[Path] = []
    if req.lesson_start is None or req.lesson_end is None:
        candidates.extend(p for p in (root / "output_slides" / req.lang).glob("lesson*") if p.is_dir())
        audio_lang_dir = root / "output_audio" / req.lang
        candidates.extend(p for p in audio_lang_dir.glob("lesson*_narration") if p.is_dir())
        candidates.extend(p for p in (root / "output_audio").glob(f"lesson*_narration_{req.lang}") if p.is_dir())
    else:
        for lesson_id in range(req.lesson_start, req.lesson_end + 1):
            slug = _lesson_slug(lesson_id)
            candidates.append(root / "output_slides" / req.lang / slug)
            candidates.append(root / "output_audio" / req.lang / f"{slug}_narration")
            candidates.append(root / "output_audio" / f"{slug}_narration_{req.lang}")
    seen: set[Path] = set()
    entries = []
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen or not path.exists():
            continue
        seen.add(resolved)
        file_count = len([p for p in path.rglob("*") if p.is_file()]) if path.is_dir() else 1
        entries.append({"path": str(path), "type": "dir" if path.is_dir() else "file", "file_count": file_count})
    return entries


def _delete_db_rows(req: ResetRequest) -> dict[str, Any]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        lesson_clause, lesson_params = _lesson_filter_sql(req, "lesson_id")
        params = [req.course_id, *lesson_params]
        deleted: dict[str, int] = {}

        li_lesson_clause, li_lesson_params = _lesson_filter_sql(req, "li.lesson_id")
        cur.execute(
            f"""
            DELETE FROM user_progress_of_language_items p
            USING language_items li
            WHERE li.item_id = p.item_id
              AND li.course_id = %s{li_lesson_clause}
            """,
            [req.course_id, *li_lesson_params],
        )
        deleted["user_progress_of_language_items"] = cur.rowcount

        cur.execute("DELETE FROM user_progress_of_lessons WHERE course_id = %s", (req.course_id,))
        deleted["user_progress_of_lessons"] = cur.rowcount

        for name, table in (
            ("vocabulary_knowledge", "vocabulary_knowledge"),
            ("language_items", "language_items"),
            ("lessons", "lessons"),
        ):
            cur.execute(f"DELETE FROM {table} WHERE course_id = %s{lesson_clause}", params)
            deleted[name] = cur.rowcount

        conn.commit()
        return {"deleted": deleted}
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def _delete_r2_keys(keys: list[str]) -> dict[str, Any]:
    storage = get_media_storage(optional=True)
    if not storage:
        return {"deleted": 0, "failed": 0, "errors": [], "warning": "R2 storage is not configured."}
    deleted = 0
    errors = []
    for key in keys:
        try:
            storage.delete_object(key)
            deleted += 1
        except Exception as exc:
            errors.append({"object_key": key, "error": str(exc)})
    return {"deleted": deleted, "failed": len(errors), "errors": errors}


def _restore_synced_files(pairs: list[dict[str, Any]]) -> dict[str, Any]:
    moved = []
    skipped = []
    for pair in pairs:
        src = Path(pair["source"])
        dst = Path(pair["destination"])
        if dst.exists():
            skipped.append({**pair, "reason": "destination_exists"})
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        moved.append(pair)
    return {"moved": moved, "skipped": skipped}


def _delete_local_entries(entries: list[dict[str, Any]]) -> dict[str, Any]:
    deleted = []
    failed = []
    for entry in entries:
        path = Path(entry["path"])
        try:
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()
            deleted.append(entry)
        except Exception as exc:
            failed.append({**entry, "error": str(exc)})
    return {"deleted": deleted, "failed": failed}


def preview_reset(req: ResetRequest) -> dict[str, Any]:
    report = ResetReport(request=_request_dict(req), executed=False)
    if "db" in req.actions and req.lesson_start is not None:
        report.warnings.append("user_progress_of_lessons is course-scoped; DB reset will affect the course progress row for this course.")

    if "db" in req.actions:
        report.db = _collect_db_counts(req)
    if "r2" in req.actions:
        keys = sorted(_collect_local_json_object_keys(req).union(_collect_db_object_keys(req)))
        report.r2 = {"object_count": len(keys), "object_keys": keys}
    if "restore_synced" in req.actions:
        pairs = _collect_restore_pairs(req)
        report.restore_synced = {"file_count": len(pairs), "files": pairs}
    if "local_stage2" in req.actions:
        entries = _collect_local_stage2(req)
        report.local = {"entry_count": len(entries), "entries": entries}

    return report.to_dict()


def execute_reset(req: ResetRequest) -> dict[str, Any]:
    if req.dry_run:
        return preview_reset(req)
    if not req.confirm:
        raise ValueError("confirmation required: set confirm=true")

    report = ResetReport(request=_request_dict(req), executed=True)
    if "db" in req.actions and req.lesson_start is not None:
        report.warnings.append("user_progress_of_lessons is course-scoped; DB reset affected the course progress row for this course.")

    if "r2" in req.actions:
        keys = sorted(_collect_local_json_object_keys(req).union(_collect_db_object_keys(req)))
        report.r2 = {"object_count": len(keys), "object_keys": keys, "result": _delete_r2_keys(keys)}
    if "local_stage2" in req.actions:
        entries = _collect_local_stage2(req)
        report.local = {"entry_count": len(entries), "entries": entries, "result": _delete_local_entries(entries)}
    if "restore_synced" in req.actions:
        pairs = _collect_restore_pairs(req)
        report.restore_synced = {"file_count": len(pairs), "files": pairs, "result": _restore_synced_files(pairs)}
    if "db" in req.actions:
        before = _collect_db_counts(req)
        report.db = {"before": before, "result": _delete_db_rows(req)}

    return report.to_dict()
