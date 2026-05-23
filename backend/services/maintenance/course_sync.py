from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from content_builder.core.paths import default_paths
from content_builder.core.pipeline import get_pipeline
from database.connection import get_connection
from database.sync_to_db import EmbeddingFactory, sync_lesson_data, upload_assets_to_r2
from database.sync_to_db_ja import (
    DEFAULT_COURSE_SLUG as MNN_COURSE_SLUG,
    MNN_PIPELINE_ID,
    ensure_japanese_course,
    prepare_mnn_lesson_data,
)


@dataclass(frozen=True)
class SyncRequest:
    pipeline: str
    course_id: int
    lang: str
    lesson_start: int | None = None
    lesson_end: int | None = None
    dry_run: bool = True
    confirm: bool = False
    confirm_code: str = ""
    include_synced: bool = True
    upload_assets: bool = True
    render_lesson_audio: bool = True


@dataclass
class SyncReport:
    request: dict[str, Any]
    lessons: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    executed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "request": self.request,
            "summary": self.summary,
            "lessons": self.lessons,
            "warnings": self.warnings,
            "executed": self.executed,
        }


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


def build_sync_request(
    *,
    pipeline: str,
    course_id: int,
    lang: str,
    lesson_start: int | None = None,
    lesson_end: int | None = None,
    dry_run: bool = True,
    confirm: bool = False,
    confirm_code: str = "",
    include_synced: bool = True,
    upload_assets: bool = True,
    render_lesson_audio: bool = True,
) -> SyncRequest:
    start, end = _normalize_lesson_bounds(lesson_start, lesson_end)
    pipeline = str(pipeline or "").strip()
    lang = str(lang or "").strip().lower()
    if not pipeline:
        raise ValueError("pipeline is required")
    if not lang:
        raise ValueError("lang is required")
    return SyncRequest(
        pipeline=pipeline,
        course_id=int(course_id),
        lang=lang,
        lesson_start=start,
        lesson_end=end,
        dry_run=bool(dry_run),
        confirm=bool(confirm),
        confirm_code=str(confirm_code or "").strip(),
        include_synced=bool(include_synced),
        upload_assets=bool(upload_assets),
        render_lesson_audio=bool(render_lesson_audio),
    )


def _artifact_root(req: SyncRequest) -> Path:
    return get_pipeline(req.pipeline).artifact_root(default_paths())


def _request_dict(req: SyncRequest) -> dict[str, Any]:
    return {
        "pipeline": req.pipeline,
        "course_id": req.course_id,
        "lang": req.lang,
        "lesson_start": req.lesson_start,
        "lesson_end": req.lesson_end,
        "dry_run": req.dry_run,
        "confirm": req.confirm,
        "include_synced": req.include_synced,
        "upload_assets": req.upload_assets,
        "render_lesson_audio": req.render_lesson_audio,
    }


def _lesson_id_from_value(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return int(digits) if digits else None


def _lesson_id_from_path(path: Path) -> int | None:
    return _lesson_id_from_value(path.stem)


def _in_lesson_range(req: SyncRequest, lesson_id: int | None) -> bool:
    if req.lesson_start is None or req.lesson_end is None:
        return True
    if lesson_id is None:
        return False
    return req.lesson_start <= lesson_id <= req.lesson_end


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


def _deck_from_data(data: dict) -> dict:
    deck = data.get("teaching_slide_deck")
    if isinstance(deck, dict):
        return deck
    render_plan = data.get("video_render_plan")
    if isinstance(render_plan, dict):
        deck = render_plan.get("teaching_slide_deck")
        if isinstance(deck, dict):
            return deck
        explanation = render_plan.get("explanation")
        if isinstance(explanation, dict) and isinstance(explanation.get("teaching_slide_deck"), dict):
            return explanation["teaching_slide_deck"]
    return {}


def _candidate_json_files(req: SyncRequest) -> list[tuple[Path, str]]:
    root = _artifact_root(req)
    output_dir = root / "output_json" / req.lang
    synced_dir = root / "synced_json" / req.lang

    by_name: dict[str, tuple[Path, str]] = {}
    if req.include_synced:
        for path in sorted(synced_dir.glob("*_data*.json")):
            by_name[path.name] = (path, "synced_json")
    for path in sorted(output_dir.glob("*_data*.json")):
        by_name[path.name] = (path, "output_json")

    files = []
    for path, source in by_name.values():
        if _in_lesson_range(req, _lesson_id_from_path(path)):
            files.append((path, source))
    return sorted(files, key=lambda item: _lesson_id_from_path(item[0]) or 0)


def _existing_lessons(req: SyncRequest) -> set[int]:
    conn = get_connection()
    cur = conn.cursor()
    try:
        if req.lesson_start is not None and req.lesson_end is not None:
            cur.execute(
                """
                SELECT lesson_id FROM lessons
                WHERE course_id = %s AND lesson_id BETWEEN %s AND %s
                """,
                (req.course_id, req.lesson_start, req.lesson_end),
            )
        else:
            cur.execute("SELECT lesson_id FROM lessons WHERE course_id = %s", (req.course_id,))
        return {int(row[0]) for row in cur.fetchall()}
    except Exception:
        return set()
    finally:
        cur.close()
        conn.close()


def _summarize_json(path: Path, source: str, existing_ids: set[int], req: SyncRequest) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "path": str(path),
            "source": source,
            "status": "invalid_json",
            "error": str(exc),
        }

    metadata = data.get("lesson_metadata") if isinstance(data.get("lesson_metadata"), dict) else {}
    lesson_id = _lesson_id_from_value(metadata.get("lesson_id")) or _lesson_id_from_path(path)
    deck = _deck_from_data(data)
    slides = deck.get("slides") if isinstance(deck.get("slides"), list) else []
    database_items = data.get("database_items") if isinstance(data.get("database_items"), list) else []
    lesson_audio_items = data.get("lesson_audio_assets", {}).get("items", []) if isinstance(data.get("lesson_audio_assets"), dict) else []
    object_keys = sorted(_extract_object_keys(data))

    return {
        "path": str(path),
        "source": source,
        "status": "ready",
        "lesson_id": lesson_id,
        "title": metadata.get("title_localized") or metadata.get("title") or path.stem,
        "metadata_course_id": metadata.get("course_id"),
        "sync_course_id": req.course_id,
        "course_id_will_be_normalized": _lesson_id_from_value(metadata.get("course_id")) != req.course_id,
        "will_overwrite_db": lesson_id in existing_ids if lesson_id is not None else False,
        "slide_count": len(slides),
        "database_item_count": len(database_items),
        "lesson_audio_item_count": len(lesson_audio_items) if isinstance(lesson_audio_items, list) else 0,
        "object_key_count": len(object_keys),
        "object_keys": object_keys,
    }


def preview_sync(req: SyncRequest) -> dict[str, Any]:
    files = _candidate_json_files(req)
    existing_ids = _existing_lessons(req)
    lessons = [_summarize_json(path, source, existing_ids, req) for path, source in files]
    ready = [item for item in lessons if item.get("status") == "ready"]

    report = SyncReport(
        request=_request_dict(req),
        lessons=lessons,
        summary={
            "json_count": len(lessons),
            "ready_count": len(ready),
            "output_json_count": sum(1 for item in lessons if item.get("source") == "output_json"),
            "synced_json_count": sum(1 for item in lessons if item.get("source") == "synced_json"),
            "will_overwrite_count": sum(1 for item in ready if item.get("will_overwrite_db")),
            "total_database_items": sum(int(item.get("database_item_count") or 0) for item in ready),
            "total_slides": sum(int(item.get("slide_count") or 0) for item in ready),
            "total_object_keys": len({key for item in ready for key in item.get("object_keys", [])}),
        },
        executed=False,
    )
    if not lessons:
        report.warnings.append("No matching lesson JSON files found.")
    return report.to_dict()


def _prepare_data_for_pipeline(req: SyncRequest, data: dict) -> tuple[dict, dict[str, Any]]:
    if req.pipeline == MNN_PIPELINE_ID:
        ensure_japanese_course(req.course_id)
        data = prepare_mnn_lesson_data(data, course_id=req.course_id, lang=req.lang)
        context = {
            "pipeline": req.pipeline,
            "lang": req.lang,
            "course_id": req.course_id,
            "course_slug": MNN_COURSE_SLUG,
            "target_language": "ja",
            "source_language": req.lang,
            "support_language": req.lang,
        }
        return data, context

    metadata = data.get("lesson_metadata")
    if isinstance(metadata, dict):
        old_course_id = metadata.get("course_id")
        if old_course_id not in {None, "", req.course_id} and _lesson_id_from_value(old_course_id) != req.course_id:
            metadata.setdefault("source_course_id", old_course_id)
        metadata["course_id"] = req.course_id
    context = {
        "pipeline": req.pipeline,
        "lang": req.lang,
        "course_id": req.course_id,
        "source_language": req.lang,
    }
    return data, context


def _render_mnn_lesson_audio(req: SyncRequest, data: dict) -> dict:
    """Render real sentence/full lesson audio for Minna no Nihongo before upload."""
    if req.pipeline != MNN_PIPELINE_ID:
        return data

    from content_builder.ja.minna_no_nihongo.tasks.lesson_audio import MinnaNoNihongoLessonAudioRenderer

    metadata = data.get("lesson_metadata") if isinstance(data.get("lesson_metadata"), dict) else {}
    lesson_id = _lesson_id_from_value(metadata.get("lesson_id"))
    if lesson_id is None:
        raise ValueError("Cannot render lesson audio without lesson_metadata.lesson_id")

    artifact_root = _artifact_root(req)
    output_dir = artifact_root / "output_audio" / f"lesson{lesson_id:03d}"
    existing_assets = data.get("lesson_audio_assets") if isinstance(data.get("lesson_audio_assets"), dict) else {}
    renderer = MinnaNoNihongoLessonAudioRenderer()
    audio_result = renderer.render_sentence_audio_assets(
        lesson_data=data,
        output_dir=output_dir,
        dry_run=False,
        existing_assets=existing_assets,
        reuse_existing=True,
        force=False,
    )
    data["lesson_audio_assets"] = audio_result.get("lesson_audio_assets", {})
    return data


def execute_sync(req: SyncRequest) -> dict[str, Any]:
    if req.dry_run:
        return preview_sync(req)
    validate_sync_execute_request(req)

    files = _candidate_json_files(req)
    synced_dir = _artifact_root(req) / "synced_json" / req.lang
    synced_dir.mkdir(parents=True, exist_ok=True)
    provider = EmbeddingFactory.create_provider()
    existing_ids = _existing_lessons(req)
    lessons = []

    for path, source in files:
        before = _summarize_json(path, source, existing_ids, req)
        item = {**before, "sync_status": "pending"}
        if before.get("status") != "ready":
            item["sync_status"] = "skipped"
            lessons.append(item)
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data, context = _prepare_data_for_pipeline(req, data)
            if req.render_lesson_audio:
                data = _render_mnn_lesson_audio(req, data)
            if req.upload_assets:
                data = upload_assets_to_r2(data)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            ok = sync_lesson_data(str(path), provider, sync_context=context)
            if not ok:
                raise RuntimeError("sync_lesson_data returned false")
            destination = synced_dir / path.name
            if path.resolve() != destination.resolve():
                shutil.move(str(path), str(destination))
                item["archived_to"] = str(destination)
            item["sync_status"] = "success"
        except Exception as exc:
            item["sync_status"] = "failed"
            item["error"] = str(exc)
        lessons.append(item)

    report = SyncReport(
        request=_request_dict(req),
        lessons=lessons,
        summary={
            "json_count": len(lessons),
            "success_count": sum(1 for item in lessons if item.get("sync_status") == "success"),
            "failed_count": sum(1 for item in lessons if item.get("sync_status") == "failed"),
            "skipped_count": sum(1 for item in lessons if item.get("sync_status") == "skipped"),
        },
        executed=True,
    )
    return report.to_dict()


def validate_sync_execute_request(req: SyncRequest) -> None:
    if not req.confirm:
        raise ValueError("confirmation required: set confirm=true")


def iter_sync_progress(req: SyncRequest) -> Iterator[dict[str, Any]]:
    """Yield progress events for dev UI streaming sync execution."""
    if req.dry_run:
        yield {"type": "report", "message": "已生成入库预览。", "report": preview_sync(req)}
        return
    validate_sync_execute_request(req)

    yield {
        "type": "start",
        "message": f"开始入库: pipeline={req.pipeline}, course_id={req.course_id}, lang={req.lang}",
        "request": _request_dict(req),
    }

    files = _candidate_json_files(req)
    yield {"type": "scan", "message": f"扫描到 {len(files)} 个 lesson JSON。", "count": len(files)}

    synced_dir = _artifact_root(req) / "synced_json" / req.lang
    synced_dir.mkdir(parents=True, exist_ok=True)
    provider = EmbeddingFactory.create_provider()
    existing_ids = _existing_lessons(req)
    lessons = []

    for index, (path, source) in enumerate(files, start=1):
        before = _summarize_json(path, source, existing_ids, req)
        item = {**before, "sync_status": "pending"}
        lesson_label = f"lesson{str(before.get('lesson_id') or index).zfill(3)}"
        yield {
            "type": "lesson_start",
            "message": f"[{index}/{len(files)}] {lesson_label}: 准备入库。",
            "lesson": item,
            "index": index,
            "total": len(files),
        }
        if before.get("status") != "ready":
            item["sync_status"] = "skipped"
            lessons.append(item)
            yield {"type": "lesson_skipped", "message": f"{lesson_label}: JSON 不可用，已跳过。", "lesson": item}
            continue
        try:
            yield {"type": "lesson_step", "message": f"{lesson_label}: 读取并规范化 JSON。", "lesson_id": before.get("lesson_id")}
            data = json.loads(path.read_text(encoding="utf-8"))
            data, context = _prepare_data_for_pipeline(req, data)

            if req.render_lesson_audio:
                yield {
                    "type": "lesson_step",
                    "message": f"{lesson_label}: 生成缺失的课文逐句音频和整课音频。",
                    "lesson_id": before.get("lesson_id"),
                }
                data = _render_mnn_lesson_audio(req, data)
            else:
                yield {"type": "lesson_step", "message": f"{lesson_label}: 跳过课文音频生成。", "lesson_id": before.get("lesson_id")}

            if req.upload_assets:
                yield {
                    "type": "lesson_step",
                    "message": f"{lesson_label}: 上传/确认 R2 媒体对象。",
                    "lesson_id": before.get("lesson_id"),
                }
                data = upload_assets_to_r2(data)
            else:
                yield {"type": "lesson_step", "message": f"{lesson_label}: 跳过 R2 媒体上传。", "lesson_id": before.get("lesson_id")}

            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            yield {"type": "lesson_step", "message": f"{lesson_label}: 写入数据库。", "lesson_id": before.get("lesson_id")}
            ok = sync_lesson_data(str(path), provider, sync_context=context)
            if not ok:
                raise RuntimeError("sync_lesson_data returned false")

            destination = synced_dir / path.name
            if path.resolve() != destination.resolve():
                yield {"type": "lesson_step", "message": f"{lesson_label}: 归档 JSON 到 synced_json。", "lesson_id": before.get("lesson_id")}
                shutil.move(str(path), str(destination))
                item["archived_to"] = str(destination)
            item["sync_status"] = "success"
            yield {"type": "lesson_success", "message": f"{lesson_label}: 入库完成。", "lesson": item}
        except Exception as exc:
            item["sync_status"] = "failed"
            item["error"] = str(exc)
            yield {"type": "lesson_failed", "message": f"{lesson_label}: 入库失败 - {exc}", "lesson": item}
        lessons.append(item)

    report = SyncReport(
        request=_request_dict(req),
        lessons=lessons,
        summary={
            "json_count": len(lessons),
            "success_count": sum(1 for item in lessons if item.get("sync_status") == "success"),
            "failed_count": sum(1 for item in lessons if item.get("sync_status") == "failed"),
            "skipped_count": sum(1 for item in lessons if item.get("sync_status") == "skipped"),
        },
        executed=True,
    )
    yield {"type": "complete", "message": "入库流程结束。", "report": report.to_dict()}
