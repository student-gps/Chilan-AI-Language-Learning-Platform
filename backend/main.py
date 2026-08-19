import os
import json
import tempfile
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, StreamingResponse
from pydantic import BaseModel
from typing import List

# 🌟 1. 挂载路由（所有的 /study/... 和 /auth/... 逻辑都已移入这两个文件）
from routers import auth, study
from database.connection import get_connection
from dependencies.auth import require_current_user_id, require_matching_user_id
from config.env import get_env
from services.course_enrollment_service import (
    ACTIVE_COURSE_STATUS,
    COMPLETED_COURSE_STATUS,
    MAX_ACTIVE_COURSES,
    PAUSED_COURSE_STATUS,
)
from services.course_registry import public_course_definition
from services.maintenance.dev_logs import make_dev_log_path, stream_events_with_log

# ── Vertex AI Service Account：支持部署环境通过 JSON 内容写临时文件 ──────────
_sa_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON", "").strip()
if _sa_json and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
    try:
        _tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        _tmp.write(_sa_json)
        _tmp.flush()
        _tmp.close()
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _tmp.name
        print(f"[startup] Vertex SA key written to {_tmp.name}")
    except Exception as _e:
        print(f"[startup] Failed to write Vertex SA key: {_e}")

app = FastAPI(title="Chilan LRS - Core Service")


@app.get("/health")
async def health_check():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return {"status": "ok", "db": "ok"}
    except Exception:
        return {"status": "ok", "db": "unavailable"}

# 1. 从环境变量读取线上地址
cors_origins_str = get_env("APP_CORS_ORIGINS", default="")
# 2. 将字符串转为列表，并去掉多余空格
origins = [o.strip() for o in cors_origins_str.split(",") if o.strip()]

# 线上常用域名兜底，避免部署环境漏配 APP_CORS_ORIGINS 时注册/登录直接被浏览器拦截
production_origins = [
    "https://www.chilanlearning.com",
    "https://chilanlearning.com",
]

# 3. 强行加入本地开发地址（确保本地开发永远可用）
local_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

for origin in production_origins + local_origins:
    if origin not in origins:
        origins.append(origin)

# 🌟 最终的 origins 列表会包含线上所有域名 + 本地 5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 🚀 挂载路由模块 ---
app.include_router(auth.router)
app.include_router(study.router)

# --- 🔊 拼音音频代理（本地文件优先，R2 presigned URL 兜底）---
from fastapi.responses import FileResponse
from services.media_pipeline_registry import get_media_pipeline, list_media_pipelines
from services.storage.media_storage import get_media_storage as _get_media_storage
_pinyin_storage = _get_media_storage(optional=True)
_BACKEND_DIR = Path(__file__).resolve().parent
_PINYIN_LOCAL_DIR = Path(__file__).resolve().parent / "pinyin_audio"
_INTRO_LOCAL_DIR = Path(__file__).resolve().parent.parent / "frontend" / "public" / "audio" / "intro"

def _safe_asset_filename(filename: str, allowed_suffixes: set[str]) -> str:
    name = Path(filename).name
    suffix = Path(name).suffix.lower()
    if not name or name != filename or suffix not in allowed_suffixes:
        raise HTTPException(status_code=400, detail="Invalid asset filename")
    return name

def _safe_lesson_digits(lesson_id: str) -> str:
    digits = "".join(ch for ch in str(lesson_id or "") if ch.isdigit())
    if not digits:
        raise HTTPException(status_code=400, detail="Invalid lesson id")
    return str(int(digits))

def _safe_lesson_slug(lesson_id: str) -> str:
    return f"lesson{_safe_lesson_digits(lesson_id).zfill(3)}"

def _attach_lesson_audio_preview_urls(
    lesson_data: dict,
    *,
    pipeline_id: str,
    lesson_slug: str,
    artifact_root: Path,
) -> None:
    """Attach local media URLs for generated lesson sentence audio in dev preview."""
    assets = lesson_data.get("lesson_audio_assets")
    if not isinstance(assets, dict):
        return

    local_audio_dir = artifact_root / "output_audio" / lesson_slug
    allowed_suffixes = {".mp3", ".wav", ".m4a"}

    def patch_asset(asset: dict) -> None:
        if not isinstance(asset, dict):
            return
        filename = Path(str(asset.get("local_audio_file") or "")).name
        if not filename:
            return
        try:
            safe_filename = _safe_asset_filename(filename, allowed_suffixes)
        except HTTPException:
            return
        if not (local_audio_dir / safe_filename).exists():
            return

        media_path = f"/media/lesson-audio/{pipeline_id}/{lesson_slug}/{safe_filename}"
        asset["media_path"] = media_path
        if not asset.get("audio_url"):
            asset["audio_url"] = media_path

    patch_asset(assets.get("full_audio"))
    for item in assets.get("items") or []:
        patch_asset(item)

@app.get("/media/pinyin/{filename}")
async def get_pinyin_audio(filename: str):
    """Serve pinyin audio: local file first (dev), then R2 presigned URL (prod)."""
    local_file = _PINYIN_LOCAL_DIR / filename
    if local_file.exists():
        return FileResponse(str(local_file), media_type="audio/wav")
    if not _pinyin_storage:
        raise HTTPException(status_code=404, detail=f"{filename} not found locally and storage not configured")
    object_key = f"zh/audio/pinyin/{filename}"
    try:
        url = _pinyin_storage.resolve_url(object_key)
        return RedirectResponse(url=url, status_code=302)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dev/lesson-artifact-options")
async def get_lesson_artifact_options():
    """Dev-only: list generated lesson artifacts available for local preview."""
    pipeline_options = []

    for pipeline in list_media_pipelines():
        artifact_root = pipeline.artifact_root(_BACKEND_DIR)
        lessons_by_lang: dict[str, set[int]] = {}

        for stage in ("output_json", "synced_json"):
            stage_dir = artifact_root / stage
            if not stage_dir.is_dir():
                continue

            for lang_dir in stage_dir.iterdir():
                if not lang_dir.is_dir():
                    continue
                lesson_ids = lessons_by_lang.setdefault(lang_dir.name, set())
                for artifact_path in lang_dir.glob("lesson*_data.json"):
                    digits = artifact_path.name[len("lesson"):-len("_data.json")]
                    if digits.isdigit():
                        lesson_ids.add(int(digits))

        languages = [
            {
                "lang": lang,
                "lessons": [str(lesson_id).zfill(3) for lesson_id in sorted(lesson_ids)],
            }
            for lang, lesson_ids in sorted(lessons_by_lang.items())
            if lesson_ids
        ]
        pipeline_options.append(
            {
                "pipeline_id": pipeline.pipeline_id,
                "display_name": pipeline.display_name,
                "target_language": pipeline.target_language,
                "languages": languages,
            }
        )

    return {"pipelines": pipeline_options}


@app.get("/dev/lesson-artifact-preview")
async def get_lesson_artifact_preview(
    pipeline_id: str = "minna_no_nihongo",
    lang: str = "zh",
    lesson_id: str = "001",
):
    """Dev-only: read a generated lesson artifact without syncing it to DB/R2."""
    pipeline = get_media_pipeline(pipeline_id)
    safe_lesson_id = _safe_lesson_digits(lesson_id)
    lesson_slug = f"lesson{safe_lesson_id.zfill(3)}"
    safe_lang = "".join(ch for ch in str(lang or "") if ch.isalnum() or ch in {"-", "_"})
    if not safe_lang:
        raise HTTPException(status_code=400, detail="Invalid lang")

    artifact_root = pipeline.artifact_root(_BACKEND_DIR)
    candidates = [
        artifact_root / "output_json" / safe_lang / f"{lesson_slug}_data.json",
        artifact_root / "synced_json" / safe_lang / f"{lesson_slug}_data.json",
        artifact_root / "output_json" / safe_lang / f"lesson{safe_lesson_id}_data.json",
        artifact_root / "synced_json" / safe_lang / f"lesson{safe_lesson_id}_data.json",
    ]
    artifact_path = next((path for path in candidates if path.exists()), None)
    if not artifact_path:
        searched = [str(path.relative_to(_BACKEND_DIR)) for path in candidates]
        raise HTTPException(
            status_code=404,
            detail={"message": "Lesson artifact not found", "searched": searched},
        )

    try:
        with artifact_path.open(encoding="utf-8") as f:
            lesson_data = json.load(f)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON artifact: {e}") from e

    _attach_lesson_audio_preview_urls(
        lesson_data,
        pipeline_id=pipeline.pipeline_id,
        lesson_slug=lesson_slug,
        artifact_root=artifact_root,
    )

    deck = lesson_data.get("teaching_slide_deck")
    if not isinstance(deck, dict):
        render_plan = lesson_data.get("video_render_plan")
        if isinstance(render_plan, dict):
            deck = render_plan.get("teaching_slide_deck")
    if not isinstance(deck, dict):
        explanation = lesson_data.get("video_render_plan", {}).get("explanation")
        if isinstance(explanation, dict):
            deck = explanation.get("teaching_slide_deck")

    return {
        "pipeline_id": pipeline.pipeline_id,
        "lang": safe_lang,
        "lesson_id": int(safe_lesson_id),
        "lesson_slug": lesson_slug,
        "artifact_path": str(artifact_path.relative_to(_BACKEND_DIR)),
        "lesson_content": lesson_data,
        "teaching_slide_deck": deck if isinstance(deck, dict) else None,
    }

@app.get("/media/intro/{filename}")
async def get_intro_audio(filename: str):
    """Serve course-intro narration audio: local file first (dev), then R2 (prod)."""
    local_file = _INTRO_LOCAL_DIR / filename
    if local_file.exists():
        return FileResponse(str(local_file), media_type="audio/mpeg")
    if not _pinyin_storage:
        raise HTTPException(status_code=404, detail=f"{filename} not found locally and storage not configured")
    object_key = f"zh/audio/intro/{filename}"
    try:
        url = _pinyin_storage.resolve_url(object_key)
        return RedirectResponse(url=url, status_code=302)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/media/teaching-slide/{pipeline_id}/{lang}/{lesson_id}/{filename}")
async def get_teaching_slide(pipeline_id: str, lang: str, lesson_id: str, filename: str):
    """Serve static teaching slide images: local file first, then R2."""
    safe_filename = _safe_asset_filename(filename, {".svg", ".webp", ".png", ".jpg", ".jpeg"})
    safe_lesson_slug = _safe_lesson_slug(lesson_id)
    pipeline = get_media_pipeline(pipeline_id)
    artifact_root = pipeline.artifact_root(_BACKEND_DIR)
    local_file = artifact_root / "output_slides" / lang / safe_lesson_slug / safe_filename
    if local_file.exists():
        media_type = "image/svg+xml" if local_file.suffix.lower() == ".svg" else None
        return FileResponse(str(local_file), media_type=media_type)
    if not _pinyin_storage:
        raise HTTPException(status_code=404, detail=f"{safe_filename} not found locally and storage not configured")
    object_key = f"{pipeline.target_language}/slides/{lang}/{safe_lesson_slug}/{safe_filename}"
    try:
        url = _pinyin_storage.resolve_url(object_key)
        return RedirectResponse(url=url, status_code=302)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/media/teaching-audio/{pipeline_id}/{lang}/{lesson_id}/{filename}")
async def get_teaching_audio(pipeline_id: str, lang: str, lesson_id: str, filename: str):
    """Serve teaching narration audio used by static slide decks."""
    safe_filename = _safe_asset_filename(filename, {".mp3", ".wav", ".m4a"})
    safe_lesson_slug = _safe_lesson_slug(lesson_id)
    pipeline = get_media_pipeline(pipeline_id)
    artifact_root = pipeline.artifact_root(_BACKEND_DIR)
    suffix = f"_{lang}" if lang != "en" else ""
    local_candidates = [
        artifact_root / "output_audio" / lang / f"{safe_lesson_slug}_narration" / safe_filename,
        artifact_root / "output_audio" / f"{safe_lesson_slug}_narration{suffix}" / safe_filename,
    ]
    local_file = next((path for path in local_candidates if path.exists()), None)
    if local_file:
        return FileResponse(str(local_file), media_type="audio/mpeg")
    if not _pinyin_storage:
        raise HTTPException(status_code=404, detail=f"{safe_filename} not found locally and storage not configured")
    object_key = f"{pipeline.target_language}/audio/narration/{lang}/{safe_lesson_slug}/{safe_filename}"
    try:
        url = _pinyin_storage.resolve_url(object_key)
        return RedirectResponse(url=url, status_code=302)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/media/lesson-audio/{pipeline_id}/{lesson_id}/{filename}")
async def get_lesson_audio(pipeline_id: str, lesson_id: str, filename: str):
    """Serve generated lesson sentence/dialogue audio for local artifact previews."""
    safe_filename = _safe_asset_filename(filename, {".mp3", ".wav", ".m4a"})
    safe_lesson_slug = _safe_lesson_slug(lesson_id)
    pipeline = get_media_pipeline(pipeline_id)
    artifact_root = pipeline.artifact_root(_BACKEND_DIR)
    local_file = artifact_root / "output_audio" / safe_lesson_slug / safe_filename
    if local_file.exists():
        return FileResponse(str(local_file), media_type="audio/mpeg")
    if not _pinyin_storage:
        raise HTTPException(status_code=404, detail=f"{safe_filename} not found locally and storage not configured")
    bucket = "full" if "_full_" in safe_filename else "sentences"
    object_key = f"{pipeline.target_language}/audio/{safe_lesson_slug}/{bucket}/{safe_filename}"
    try:
        url = _pinyin_storage.resolve_url(object_key)
        return RedirectResponse(url=url, status_code=302)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 🧪 数据库依赖 ---
def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

# --- 📦 业务请求模型 ---
class EnrollReq(BaseModel):
    user_id: str | None = None
    course_id: int
    action: str = "pause"


def get_lesson_id_bounds(cur, course_id: int) -> tuple[int, int] | None:
    cur.execute(
        "SELECT MIN(lesson_id), MAX(lesson_id) FROM lessons WHERE course_id = %s",
        (course_id,),
    )
    first_lesson_id, last_lesson_id = cur.fetchone()
    if first_lesson_id is None or last_lesson_id is None:
        return None
    return int(first_lesson_id), int(last_lesson_id)


class DevCourseResetRequest(BaseModel):
    pipeline: str = "minna_no_nihongo"
    course_id: int = 303
    lang: str = "zh"
    actions: List[str]
    lesson_start: int | None = None
    lesson_end: int | None = None
    dry_run: bool = True
    confirm: bool = False
    confirm_code: str = ""


class DevCourseSyncRequest(BaseModel):
    pipeline: str = "minna_no_nihongo"
    course_id: int = 303
    lang: str = "zh"
    lesson_start: int | None = None
    lesson_end: int | None = None
    dry_run: bool = True
    confirm: bool = False
    confirm_code: str = ""
    include_synced: bool = True
    upload_assets: bool = True
    render_lesson_audio: bool = True


class DevContentBuilderRequest(BaseModel):
    pipeline: str = "minna_no_nihongo"
    lang: str = "zh"
    lesson_start: int | None = 1
    lesson_end: int | None = 1
    run_stage1: bool = True
    run_stage2: bool = True
    stage2_mode: str = "full"
    force_stage1: bool = True
    force_narration: bool = True
    force_slides: bool = True
    refresh_render_plan: bool = False
    lesson_audio_metadata_only: bool = False
    only_slide: int | None = None
    confirm: bool = False
    confirm_code: str = ""


def _dev_reset_request(payload: DevCourseResetRequest, *, dry_run: bool):
    build_request, _, _ = _load_course_reset_tools()
    try:
        return build_request(
            pipeline=payload.pipeline,
            course_id=payload.course_id,
            lang=payload.lang,
            actions=payload.actions,
            lesson_start=payload.lesson_start,
            lesson_end=payload.lesson_end,
            dry_run=dry_run,
            confirm=payload.confirm,
            confirm_code=payload.confirm_code,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


def _dev_sync_request(payload: DevCourseSyncRequest, *, dry_run: bool):
    build_sync_request, _, _, _, _ = _load_course_sync_tools()
    try:
        return build_sync_request(
            pipeline=payload.pipeline,
            course_id=payload.course_id,
            lang=payload.lang,
            lesson_start=payload.lesson_start,
            lesson_end=payload.lesson_end,
            dry_run=dry_run,
            confirm=payload.confirm,
            confirm_code=payload.confirm_code,
            include_synced=payload.include_synced,
            upload_assets=payload.upload_assets,
            render_lesson_audio=payload.render_lesson_audio,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


def _dev_tool_unavailable(exc: Exception):
    raise HTTPException(
        status_code=503,
        detail=f"Dev content-builder tooling is not available in this environment: {exc}",
    ) from exc


def _load_course_reset_tools():
    try:
        from services.maintenance.course_reset import build_request, execute_reset, preview_reset
    except ModuleNotFoundError as exc:
        _dev_tool_unavailable(exc)
    return build_request, execute_reset, preview_reset


def _load_course_sync_tools():
    try:
        from services.maintenance.course_sync import (
            build_sync_request,
            execute_sync,
            iter_sync_progress,
            preview_sync,
            validate_sync_execute_request,
        )
    except ModuleNotFoundError as exc:
        _dev_tool_unavailable(exc)
    return build_sync_request, execute_sync, iter_sync_progress, preview_sync, validate_sync_execute_request


def _load_content_builder_tools():
    try:
        from services.maintenance.content_builder_runner import (
            build_content_builder_request,
            iter_content_builder_progress,
            preview_content_builder,
            validate_content_builder_execution,
        )
    except ModuleNotFoundError as exc:
        _dev_tool_unavailable(exc)
    return (
        build_content_builder_request,
        iter_content_builder_progress,
        preview_content_builder,
        validate_content_builder_execution,
    )


def _dev_content_builder_request(payload: DevContentBuilderRequest):
    build_content_builder_request, _, _, _ = _load_content_builder_tools()
    try:
        return build_content_builder_request(
            pipeline=payload.pipeline,
            lang=payload.lang,
            lesson_start=payload.lesson_start,
            lesson_end=payload.lesson_end,
            run_stage1=payload.run_stage1,
            run_stage2=payload.run_stage2,
            stage2_mode=payload.stage2_mode,
            force_stage1=payload.force_stage1,
            force_narration=payload.force_narration,
            force_slides=payload.force_slides,
            refresh_render_plan=payload.refresh_render_plan,
            lesson_audio_metadata_only=payload.lesson_audio_metadata_only,
            only_slide=payload.only_slide,
            confirm=payload.confirm,
            confirm_code=payload.confirm_code,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/dev/content-builder/preview")
async def dev_content_builder_preview(payload: DevContentBuilderRequest):
    """Dev-only: preview the content-builder commands that would run."""
    req = _dev_content_builder_request(payload)
    _, _, preview_content_builder, _ = _load_content_builder_tools()
    try:
        return preview_content_builder(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/dev/content-builder/run-stream")
async def dev_content_builder_run_stream(payload: DevContentBuilderRequest):
    """Dev-only: run selected content-builder stages and stream logs as NDJSON."""
    req = _dev_content_builder_request(payload)
    _, iter_content_builder_progress, _, validate_content_builder_execution = _load_content_builder_tools()
    try:
        validate_content_builder_execution(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    def event_stream():
        log_path = make_dev_log_path(
            kind="content_builder",
            pipeline=req.pipeline,
            lang=req.lang,
            lesson_start=req.lesson_start,
            lesson_end=req.lesson_end,
        )

        def events():
            try:
                for event in iter_content_builder_progress(req):
                    yield event
            except Exception as e:
                yield {"type": "fatal", "message": str(e)}

        try:
            for event in stream_events_with_log(
                events(),
                log_path=log_path,
                start_message=f"日志文件: {log_path}",
            ):
                yield json.dumps(event, ensure_ascii=False) + "\n"
        except Exception as e:
            yield json.dumps({"type": "fatal", "message": str(e)}, ensure_ascii=False) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


@app.post("/dev/course-reset/preview")
async def dev_course_reset_preview(payload: DevCourseResetRequest):
    """Dev-only: preview course-scoped reset impact without mutating DB/R2/local files."""
    req = _dev_reset_request(payload, dry_run=True)
    _, _, preview_reset = _load_course_reset_tools()
    try:
        report = preview_reset(req)
        log_path = make_dev_log_path(
            kind="course_reset_preview",
            pipeline=req.pipeline,
            lang=req.lang,
            course_id=req.course_id,
            lesson_start=req.lesson_start,
            lesson_end=req.lesson_end,
        )
        list(stream_events_with_log(
            [{"type": "report", "message": "删除 / 回退预览完成。"}],
            log_path=log_path,
            start_message=f"日志文件: {log_path}",
        ))
        report["_dev_log"] = {"log_path": str(log_path), "log_dir": str(log_path.parent)}
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/dev/course-sync/preview")
async def dev_course_sync_preview(payload: DevCourseSyncRequest):
    """Dev-only: preview generated lesson JSON sync impact without DB/R2 mutation."""
    req = _dev_sync_request(payload, dry_run=True)
    _, _, _, preview_sync, _ = _load_course_sync_tools()
    try:
        return preview_sync(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/dev/course-sync/execute")
async def dev_course_sync_execute(payload: DevCourseSyncRequest):
    """Dev-only: execute a confirmed course sync."""
    req = _dev_sync_request(payload, dry_run=False)
    _, execute_sync, _, _, _ = _load_course_sync_tools()
    try:
        return execute_sync(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/dev/course-sync/execute-stream")
async def dev_course_sync_execute_stream(payload: DevCourseSyncRequest):
    """Dev-only: execute a confirmed course sync and stream progress events as NDJSON."""
    req = _dev_sync_request(payload, dry_run=False)
    _, _, iter_sync_progress, _, validate_sync_execute_request = _load_course_sync_tools()
    try:
        validate_sync_execute_request(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    def event_stream():
        log_path = make_dev_log_path(
            kind="course_sync",
            pipeline=req.pipeline,
            lang=req.lang,
            course_id=req.course_id,
            lesson_start=req.lesson_start,
            lesson_end=req.lesson_end,
        )

        def events():
            try:
                for event in iter_sync_progress(req):
                    yield event
            except Exception as e:
                yield {"type": "fatal", "message": str(e)}

        try:
            for event in stream_events_with_log(
                events(),
                log_path=log_path,
                start_message=f"日志文件: {log_path}",
            ):
                yield json.dumps(event, ensure_ascii=False) + "\n"
        except Exception as e:
            yield json.dumps({"type": "fatal", "message": str(e)}, ensure_ascii=False) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


@app.post("/dev/course-reset/execute")
async def dev_course_reset_execute(payload: DevCourseResetRequest):
    """Dev-only: execute a confirmed course-scoped reset action."""
    req = _dev_reset_request(payload, dry_run=False)
    _, execute_reset, _ = _load_course_reset_tools()
    log_path = make_dev_log_path(
        kind="course_reset",
        pipeline=req.pipeline,
        lang=req.lang,
        course_id=req.course_id,
        lesson_start=req.lesson_start,
        lesson_end=req.lesson_end,
    )
    try:
        report = execute_reset(req)
        list(stream_events_with_log(
            [{"type": "complete", "message": "删除 / 回退执行完成。"}],
            log_path=log_path,
            start_message=f"日志文件: {log_path}",
        ))
        report["_dev_log"] = {"log_path": str(log_path), "log_dir": str(log_path.parent)}
        return report
    except ValueError as e:
        list(stream_events_with_log(
            [{"type": "fatal", "message": str(e)}],
            log_path=log_path,
            start_message=f"日志文件: {log_path}",
        ))
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        list(stream_events_with_log(
            [{"type": "fatal", "message": str(e)}],
            log_path=log_path,
            start_message=f"日志文件: {log_path}",
        ))
        raise HTTPException(status_code=500, detail=str(e)) from e

# ==========================================
# 2. 课程管理系统 (核心业务：保留)
# ==========================================

def _serialize_course(row) -> dict:
    """将课程查询结果行转为统一的 JSON 字典（含课时数和词汇数）。"""
    definition = public_course_definition(
        course_id=row[0],
        category=row[2],
        target_language=row[3],
        source_language=row[4],
    )
    return {
        "id": row[0],
        "name": row[1],
        "category": row[2],
        "target_language": row[3],
        "source_language": row[4],
        "lesson_total": row[5],
        "total_items": row[6],
        **definition,
    }

_COURSE_CATALOG_QUERY = """
    WITH lesson_counts AS (
        SELECT course_id, COUNT(DISTINCT lesson_id) AS lesson_total
        FROM lessons
        GROUP BY course_id
    ),
    item_counts AS (
        SELECT course_id, COUNT(*) AS total_items
        FROM language_items
        GROUP BY course_id
    )
    SELECT
        c.course_id,
        c.name,
        c.category,
        c.target_language,
        c.source_language,
        COALESCE(lc.lesson_total, 0) AS lesson_total,
        COALESCE(ic.total_items, 0) AS total_items
    FROM courses c
    LEFT JOIN lesson_counts lc ON lc.course_id = c.course_id
    LEFT JOIN item_counts ic ON ic.course_id = c.course_id
"""


_COURSE_DETAIL_QUERY = """
    SELECT
        c.course_id,
        c.name,
        c.category,
        c.target_language,
        c.source_language,
        COALESCE(lc.lesson_total, 0) AS lesson_total,
        COALESCE(ic.total_items, 0) AS total_items
    FROM courses c
    LEFT JOIN LATERAL (
        SELECT COUNT(DISTINCT l.lesson_id) AS lesson_total
        FROM lessons l
        WHERE l.course_id = c.course_id
    ) lc ON TRUE
    LEFT JOIN LATERAL (
        SELECT COUNT(*) AS total_items
        FROM language_items li
        WHERE li.course_id = c.course_id
    ) ic ON TRUE
    WHERE c.course_id = %s
"""


@app.get("/courses")
async def list_all_courses(db=Depends(get_db)):
    cur = db.cursor()
    cur.execute(_COURSE_CATALOG_QUERY + " ORDER BY c.course_id")
    return [_serialize_course(r) for r in cur.fetchall()]


@app.get("/courses/by-slug/{course_slug}")
async def get_course_by_slug(course_slug: str, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute(_COURSE_CATALOG_QUERY + " ORDER BY c.course_id")
    for row in cur.fetchall():
        course = _serialize_course(row)
        if course["slug"] == course_slug:
            return course
    raise HTTPException(status_code=404, detail="Course not found")


@app.get("/courses/by-slug/{course_slug}/foundations")
async def get_course_foundations_by_slug(course_slug: str, db=Depends(get_db)):
    course = await get_course_by_slug(course_slug, db)
    return course["foundations"]


@app.get("/courses/by-slug/{course_slug}/foundations/{module_key}")
async def get_course_foundation_by_slug(course_slug: str, module_key: str, db=Depends(get_db)):
    course = await get_course_by_slug(course_slug, db)
    module = next((item for item in course["foundations"] if item["key"] == module_key), None)
    if module is None:
        raise HTTPException(status_code=404, detail="Foundation module not found")
    return module


@app.get("/courses/{course_id}")
async def get_course(course_id: int, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute(_COURSE_DETAIL_QUERY, (course_id,))
    row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return _serialize_course(row)

@app.get("/my-courses/{user_id}")
async def get_my_courses(
    user_id: str,
    current_user_id: str = Depends(require_current_user_id),
    db=Depends(get_db),
):
    require_matching_user_id(user_id, current_user_id)
    cur = db.cursor()
    # 活跃报名、题目进度与课时进度分开汇总，避免多张事实表相乘后再去重。
    query = """
        WITH active_courses AS (
            SELECT DISTINCT uc.course_id
            FROM user_courses uc
            WHERE uc.user_id::text = %s
              AND uc.status = %s
        ),
        item_progress AS (
            SELECT
                li.course_id,
                COUNT(DISTINCT li.item_id) AS total_item_count,
                COUNT(DISTINCT p.item_id) FILTER (WHERE p.is_mastered = TRUE) AS mastered_count
            FROM language_items li
            JOIN active_courses ac ON ac.course_id = li.course_id
            LEFT JOIN user_progress_of_language_items p
              ON p.item_id = li.item_id
             AND p.user_id::text = %s
            GROUP BY li.course_id
        ),
        lesson_rollup AS (
            SELECT
                l.course_id,
                COUNT(DISTINCT l.lesson_id) AS lesson_total,
                COUNT(DISTINCT l.lesson_id) FILTER (
                    WHERE l.lesson_id <= COALESCE(progress.last_completed_lesson_id, 0)
                ) AS completed_lesson_count
            FROM lessons l
            JOIN active_courses ac ON ac.course_id = l.course_id
            LEFT JOIN LATERAL (
                SELECT last_completed_lesson_id
                FROM user_progress_of_lessons lp
                WHERE lp.course_id = l.course_id
                  AND lp.user_id::text = %s
                ORDER BY lp.last_completed_lesson_id DESC
                LIMIT 1
            ) progress ON TRUE
            GROUP BY l.course_id
        )
        SELECT c.course_id, c.name, c.category,
               c.target_language, c.source_language,
               COALESCE(ip.mastered_count, 0) AS mastered_count,
               COALESCE(ip.total_item_count, 0) AS total_item_count,
               COALESCE(lr.lesson_total, 0) AS lesson_total,
               COALESCE(lr.completed_lesson_count, 0) AS completed_lesson_count,
               COALESCE(lp.last_completed_lesson_id, 0) AS last_completed_lesson_id,
               COALESCE(lp.viewed_lesson_id, 0) AS viewed_lesson_id,
               COALESCE(lp.practice_question_index, 0) AS practice_question_index,
               next_lesson.lesson_id AS next_lesson_id,
               next_lesson.title AS next_lesson_title,
               next_lesson.title_localized AS next_lesson_title_localized
        FROM active_courses ac
        JOIN courses c ON c.course_id = ac.course_id
        LEFT JOIN LATERAL (
            SELECT
                lp.last_completed_lesson_id,
                lp.viewed_lesson_id,
                lp.practice_question_index
            FROM user_progress_of_lessons lp
            WHERE lp.course_id = c.course_id
              AND lp.user_id::text = %s
            ORDER BY lp.last_completed_lesson_id DESC
            LIMIT 1
        ) lp ON TRUE
        LEFT JOIN item_progress ip ON ip.course_id = c.course_id
        LEFT JOIN lesson_rollup lr ON lr.course_id = c.course_id
        LEFT JOIN LATERAL (
            SELECT
                l.lesson_id,
                l.title,
                l.lesson_metadata->>'title_localized' AS title_localized
            FROM lessons l
            WHERE l.course_id = c.course_id
              AND l.lesson_id > COALESCE(lp.last_completed_lesson_id, 0)
            ORDER BY l.lesson_id ASC
            LIMIT 1
        ) next_lesson ON TRUE;
    """
    cur.execute(query, (
        user_id,
        ACTIVE_COURSE_STATUS,
        user_id,
        user_id,
        user_id,
    ))
    courses = []
    for r in cur.fetchall():
        definition = public_course_definition(
            course_id=r[0],
            category=r[2],
            target_language=r[3],
            source_language=r[4],
        )
        courses.append({
            "id": r[0],
            "name": r[1],
            "category": r[2],
            "target_language": r[3],
            "source_language": r[4],
            "mastered": r[5],
            "total_items": r[6],
            "lesson_total": r[7],
            "completed_lesson_count": r[8],
            "last_completed_lesson_id": r[9],
            "viewed_lesson_id": r[10],
            "practice_question_index": r[11],
            "next_lesson_id": r[12],
            "next_lesson_title": r[13],
            "next_lesson_title_localized": r[14],
            **definition,
        })
    return courses

@app.post("/courses/enroll")
async def enroll_course(
    req: EnrollReq,
    current_user_id: str = Depends(require_current_user_id),
    db=Depends(get_db),
):
    if req.user_id is not None:
        require_matching_user_id(req.user_id, current_user_id)
    user_id = current_user_id
    cur = db.cursor()
    try:
        cur.execute(
            "SELECT status FROM user_courses WHERE user_id::text = %s AND course_id = %s",
            (user_id, req.course_id)
        )
        existing = cur.fetchone()
        if existing and existing[0] == ACTIVE_COURSE_STATUS:
            db.commit()
            return {"status": "success", "already_enrolled": True}

        cur.execute(
            "SELECT COUNT(*) FROM user_courses WHERE user_id::text = %s AND status = %s",
            (user_id, ACTIVE_COURSE_STATUS)
        )
        active_course_count = cur.fetchone()[0]
        if active_course_count >= MAX_ACTIVE_COURSES:
            raise HTTPException(
                status_code=409,
                detail=f"你当前最多可学习 {MAX_ACTIVE_COURSES} 门课程，请先完成或暂停一门。"
            )

        # 记录用户选课；已暂停/已完成的课程重新加入时恢复为 active，保留历史进度
        if existing:
            cur.execute(
                """
                UPDATE user_courses
                SET status = %s
                WHERE user_id::text = %s AND course_id = %s
                """,
                (ACTIVE_COURSE_STATUS, user_id, req.course_id)
            )
        else:
            cur.execute(
                "INSERT INTO user_courses (user_id, course_id, status) VALUES (%s, %s, %s)",
                (user_id, req.course_id, ACTIVE_COURSE_STATUS)
            )
        
        lesson_bounds = get_lesson_id_bounds(cur, req.course_id)
        initial_completed_lesson_id = 0
        last_lesson_id = None
        if lesson_bounds:
            first_lesson_id, last_lesson_id = lesson_bounds
            initial_completed_lesson_id = max(first_lesson_id - 1, 0)

        # 初始化该课程的“课时进度”记录：按课程真实 lesson_id 起点计算。
        # 中文 Integrated Chinese 从 101 起步会得到 100；日语 MNN 从 1 起步会得到 0。
        cur.execute("""
            INSERT INTO user_progress_of_lessons (user_id, course_id, last_completed_lesson_id)
            VALUES (%s, %s, %s) ON CONFLICT DO NOTHING
        """, (user_id, req.course_id, initial_completed_lesson_id))

        if last_lesson_id is not None:
            cur.execute(
                """
                UPDATE user_progress_of_lessons
                SET last_completed_lesson_id = %s,
                    practice_question_index = 0,
                    practice_question_updated_at = NULL
                WHERE user_id::text = %s
                  AND course_id = %s
                  AND COALESCE(last_completed_lesson_id, 0) > %s
                """,
                (initial_completed_lesson_id, user_id, req.course_id, last_lesson_id),
            )
        
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/courses/enroll")
async def unenroll_course(
    req: EnrollReq,
    current_user_id: str = Depends(require_current_user_id),
    db=Depends(get_db),
):
    if req.user_id is not None:
        require_matching_user_id(req.user_id, current_user_id)
    user_id = current_user_id
    cur = db.cursor()
    try:
        action = (req.action or "pause").strip().lower()
        if action == "clear":
            cur.execute(
                """
                DELETE FROM user_progress_of_language_items p
                USING language_items li
                WHERE p.item_id = li.item_id
                  AND p.user_id::text = %s
                  AND li.course_id = %s
                """,
                (user_id, req.course_id)
            )
            cur.execute(
                "DELETE FROM review_logs WHERE user_id::text = %s AND course_id = %s",
                (user_id, req.course_id)
            )
            cur.execute(
                "DELETE FROM user_progress_of_lessons WHERE user_id::text = %s AND course_id = %s",
                (user_id, req.course_id)
            )
            cur.execute(
                "DELETE FROM user_courses WHERE user_id::text = %s AND course_id = %s",
                (user_id, req.course_id)
            )
        else:
            cur.execute(
                """
                UPDATE user_courses
                SET status = %s
                WHERE user_id::text = %s
                  AND course_id = %s
                  AND status <> %s
                """,
                (PAUSED_COURSE_STATUS, user_id, req.course_id, COMPLETED_COURSE_STATUS)
            )
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/courses/{course_id}/lessons")
async def get_course_lessons(course_id: int, db=Depends(get_db)):
    cur = db.cursor()
    cur.execute(
        "SELECT lesson_id, title, lesson_metadata->>'title_localized' AS title_localized FROM lessons WHERE course_id = %s ORDER BY lesson_id ASC",
        (course_id,)
    )
    return [{"lesson_id": r[0], "title": r[1], "title_localized": r[2]} for r in cur.fetchall()]

# ==========================================
# 3. 教室仪表盘与统计 (数据中心：保留)
# ==========================================

@app.get("/classroom/stats/{user_id}")
async def get_classroom_stats(
    user_id: str,
    current_user_id: str = Depends(require_current_user_id),
    db=Depends(get_db),
):
    require_matching_user_id(user_id, current_user_id)
    cur = db.cursor()
    try:
        cur.execute("""
            SELECT
                due.total_remaining AS total_remaining,
                reviewed.total_reviewed AS total_reviewed,
                newly_learned.total_new_learned AS total_new_learned
            FROM (VALUES (1)) AS one(dummy)
            CROSS JOIN LATERAL (
                SELECT COUNT(*) AS total_remaining
                FROM user_progress_of_language_items p
                JOIN language_items q ON q.item_id = p.item_id
                JOIN user_courses uc
                  ON uc.course_id = q.course_id
                 AND uc.user_id::text = p.user_id::text
                 AND uc.status = %s
                WHERE p.user_id::text = %s
                  AND p.next_review <= CURRENT_TIMESTAMP
            ) due
            CROSS JOIN LATERAL (
                SELECT COUNT(DISTINCT rl.item_id) AS total_reviewed
                FROM review_logs rl
                JOIN user_courses uc
                  ON uc.course_id = rl.course_id
                 AND uc.user_id::text = rl.user_id::text
                 AND uc.status = %s
                WHERE rl.user_id::text = %s
                  AND rl.review_time >= CURRENT_DATE
            ) reviewed
            CROSS JOIN LATERAL (
                SELECT COUNT(*) AS total_new_learned
                FROM review_logs rl
                JOIN user_courses uc
                  ON uc.course_id = rl.course_id
                 AND uc.user_id::text = rl.user_id::text
                 AND uc.status = %s
                WHERE rl.user_id::text = %s
                  AND rl.state = 0
                  AND rl.review_time >= CURRENT_DATE
            ) newly_learned;
        """, (
            ACTIVE_COURSE_STATUS,
            user_id,
            ACTIVE_COURSE_STATUS,
            user_id,
            ACTIVE_COURSE_STATUS,
            user_id,
        ))
        row = cur.fetchone() or (0, 0, 0)
        return {
            "totalRemaining": row[0],
            "totalReviewed": row[1],
            "totalNewLearned": row[2],
        }
    finally:
        cur.close()

@app.get("/daily_tasks/{user_id}")
async def get_daily_tasks(user_id: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        query = """
            SELECT q.item_id, q.question_type, q.original_text FROM language_items q
            JOIN user_progress_of_language_items p ON q.item_id = p.item_id
            JOIN user_courses uc
              ON uc.course_id = q.course_id
             AND uc.user_id::text = p.user_id::text
             AND uc.status = %s
            WHERE p.user_id::text = %s AND p.next_review <= CURRENT_TIMESTAMP
            ORDER BY p.next_review ASC LIMIT 20;
        """
        cur.execute(query, (ACTIVE_COURSE_STATUS, user_id))
        return [{"id": r[0], "type": r[1], "text": r[2]} for r in cur.fetchall()]
    finally:
        cur.close()

@app.get("/overview/stats/{user_id}")
async def get_overview_stats(user_id: str, db=Depends(get_db)):
    """
    学习概览统计：
    - due_count:        当前待复习题目数
    - avg_stability:    所有已学题目的平均稳定性（FSRS stability，越高越不易遗忘）
    - mastered_count:   已掌握词汇总数
    - level:            学习阶段（按掌握数分档：L1-L5）
    """
    cur = db.cursor()
    try:
        # 1. 待复习数（仅活跃课程）
        cur.execute("""
            SELECT COUNT(*)
            FROM user_progress_of_language_items p
            JOIN language_items li ON li.item_id = p.item_id
            JOIN user_courses uc
              ON uc.course_id = li.course_id
             AND uc.user_id::text = p.user_id::text
             AND uc.status = %s
            WHERE p.user_id::text = %s
              AND p.next_review <= CURRENT_TIMESTAMP
        """, (ACTIVE_COURSE_STATUS, user_id))
        due_count = cur.fetchone()[0]

        # 2. 平均稳定性 + 掌握数（所有有进度记录的活跃课程题目）
        cur.execute("""
            SELECT
                COALESCE(AVG(p.stability), 0)                                          AS avg_stability,
                COUNT(*) FILTER (WHERE p.is_mastered = TRUE)                           AS mastered_count
            FROM user_progress_of_language_items p
            JOIN language_items li ON li.item_id = p.item_id
            JOIN user_courses uc
              ON uc.course_id = li.course_id
             AND uc.user_id::text = p.user_id::text
             AND uc.status = %s
            WHERE p.user_id::text = %s
        """, (ACTIVE_COURSE_STATUS, user_id))
        row = cur.fetchone()
        avg_stability = round(float(row[0]), 2) if row else 0.0
        mastered_count = int(row[1]) if row else 0

        # 3. 学习阶段（按掌握词汇总数分档）
        if mastered_count >= 2000:
            level = 'L5'
        elif mastered_count >= 800:
            level = 'L4'
        elif mastered_count >= 300:
            level = 'L3'
        elif mastered_count >= 80:
            level = 'L2'
        else:
            level = 'L1'

        return {
            "due_count":      due_count,
            "avg_stability":  avg_stability,
            "mastered_count": mastered_count,
            "level":          level,
        }
    finally:
        cur.close()
        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
