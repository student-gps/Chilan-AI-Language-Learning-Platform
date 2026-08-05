from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent


@dataclass(frozen=True)
class ContentBuilderRequest:
    pipeline: str
    lang: str
    lesson_start: int
    lesson_end: int
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


def build_content_builder_request(
    *,
    pipeline: str,
    lang: str,
    lesson_start: int | None = None,
    lesson_end: int | None = None,
    run_stage1: bool = True,
    run_stage2: bool = True,
    stage2_mode: str = "full",
    force_stage1: bool = True,
    force_narration: bool = True,
    force_slides: bool = True,
    refresh_render_plan: bool = False,
    lesson_audio_metadata_only: bool = False,
    only_slide: int | None = None,
    confirm: bool = False,
    confirm_code: str = "",
) -> ContentBuilderRequest:
    pipeline = str(pipeline or "").strip()
    lang = str(lang or "").strip().lower()
    if pipeline != "minna_no_nihongo":
        raise ValueError("Only minna_no_nihongo is supported by this dev runner for now.")
    if not lang:
        raise ValueError("lang is required")
    start = int(lesson_start or lesson_end or 1)
    end = int(lesson_end or lesson_start or start)
    if start <= 0 or end <= 0 or start > end:
        raise ValueError("lesson range must be positive and start <= end")
    mode = str(stage2_mode or "full").strip().lower()
    if mode not in {"full", "slides_only"}:
        raise ValueError("stage2_mode must be full or slides_only")
    if only_slide is not None and int(only_slide) <= 0:
        raise ValueError("only_slide must be positive")
    return ContentBuilderRequest(
        pipeline=pipeline,
        lang=lang,
        lesson_start=start,
        lesson_end=end,
        run_stage1=bool(run_stage1),
        run_stage2=bool(run_stage2),
        stage2_mode=mode,
        force_stage1=bool(force_stage1),
        force_narration=bool(force_narration),
        force_slides=bool(force_slides),
        refresh_render_plan=bool(refresh_render_plan),
        lesson_audio_metadata_only=bool(lesson_audio_metadata_only),
        only_slide=int(only_slide) if only_slide is not None else None,
        confirm=bool(confirm),
        confirm_code=str(confirm_code or "").strip(),
    )


def validate_content_builder_execution(req: ContentBuilderRequest) -> None:
    if not req.confirm:
        raise ValueError("confirmation required: set confirm=true")
    if not req.run_stage1 and not req.run_stage2:
        raise ValueError("Select at least one stage to run.")


def preview_content_builder(req: ContentBuilderRequest) -> dict[str, Any]:
    commands = []
    for lesson_id in range(req.lesson_start, req.lesson_end + 1):
        commands.extend(_commands_for_lesson(req, lesson_id))
    return {
        "request": _request_dict(req),
        "summary": {
            "lesson_count": req.lesson_end - req.lesson_start + 1,
            "command_count": len(commands),
        },
        "commands": [{"lesson_id": lesson_id, "stage": stage, "argv": argv} for lesson_id, stage, argv in commands],
    }


def iter_content_builder_progress(req: ContentBuilderRequest) -> Iterator[dict[str, Any]]:
    validate_content_builder_execution(req)
    plan = preview_content_builder(req)
    yield {"type": "start", "message": "开始运行 content builder。", "plan": plan}

    for lesson_id, stage, argv in (
        item for lesson_id in range(req.lesson_start, req.lesson_end + 1) for item in _commands_for_lesson(req, lesson_id)
    ):
        lesson_slug = f"lesson{lesson_id:03d}"
        yield {
            "type": "command_start",
            "message": f"{lesson_slug} · {stage}: 开始。",
            "lesson_id": lesson_id,
            "stage": stage,
            "argv": argv,
        }
        result = yield from _run_command(argv, lesson_id=lesson_id, stage=stage)
        if result != 0:
            yield {
                "type": "command_failed",
                "message": f"{lesson_slug} · {stage}: 失败，退出码 {result}。",
                "lesson_id": lesson_id,
                "stage": stage,
                "returncode": result,
            }
            yield {"type": "fatal", "message": "content builder 已停止。"}
            return
        yield {
            "type": "command_success",
            "message": f"{lesson_slug} · {stage}: 完成。",
            "lesson_id": lesson_id,
            "stage": stage,
        }

    yield {
        "type": "complete",
        "message": "content builder 全部完成。",
        "preview_url": _preview_url(req),
        "plan": plan,
    }


def _request_dict(req: ContentBuilderRequest) -> dict[str, Any]:
    return {
        "pipeline": req.pipeline,
        "lang": req.lang,
        "lesson_start": req.lesson_start,
        "lesson_end": req.lesson_end,
        "run_stage1": req.run_stage1,
        "run_stage2": req.run_stage2,
        "stage2_mode": req.stage2_mode,
        "force_stage1": req.force_stage1,
        "force_narration": req.force_narration,
        "force_slides": req.force_slides,
        "refresh_render_plan": req.refresh_render_plan,
        "lesson_audio_metadata_only": req.lesson_audio_metadata_only,
        "only_slide": req.only_slide,
    }


def _commands_for_lesson(req: ContentBuilderRequest, lesson_id: int) -> list[tuple[int, str, list[str]]]:
    lesson_slug = f"lesson{lesson_id:03d}"
    commands: list[tuple[int, str, list[str]]] = []
    if req.run_stage1:
        argv = [
            sys.executable,
            str(BACKEND_DIR / "content_builder" / "ja" / "minna_no_nihongo" / "build_lesson.py"),
            "--lesson",
            lesson_slug,
            "--support-lang",
            req.lang,
        ]
        if req.force_stage1:
            argv.append("--force")
        if req.lesson_audio_metadata_only:
            argv.append("--lesson-audio-metadata-only")
        commands.append((lesson_id, "Stage1 JSON + lesson audio", argv))

    if req.run_stage2:
        json_path = _lesson_json_path(req, lesson_id)
        if req.stage2_mode == "slides_only":
            argv = [
                sys.executable,
                str(BACKEND_DIR / "content_builder" / "ja" / "minna_no_nihongo" / "scripts" / "build_teaching_slide_deck.py"),
                str(json_path),
                "--pipeline",
                req.pipeline,
                "--lang",
                req.lang,
                "--renderer",
                "remotion",
            ]
            if req.force_slides:
                argv.append("--force")
            if req.refresh_render_plan:
                argv.append("--refresh-render-plan")
            argv.append("--without-audio")
            if req.only_slide:
                argv.extend(["--only-slide", str(req.only_slide)])
            commands.append((lesson_id, "Stage2 slides only", argv))
        else:
            argv = [
                sys.executable,
                str(BACKEND_DIR / "content_builder" / "ja" / "minna_no_nihongo" / "scripts" / "render_narration.py"),
                str(json_path),
                "--pipeline",
                req.pipeline,
                "--lang",
                req.lang,
            ]
            if req.force_narration:
                argv.append("--force-narration")
            if req.force_slides:
                argv.append("--force-slides")
            if req.refresh_render_plan:
                argv.append("--refresh-render-plan")
            commands.append((lesson_id, "Stage2 narration + slides", argv))
    return commands


def _lesson_json_path(req: ContentBuilderRequest, lesson_id: int) -> Path:
    lesson_slug = f"lesson{lesson_id:03d}"
    artifact_root = BACKEND_DIR / "content_builder" / "ja" / "minna_no_nihongo" / "artifacts"
    output = artifact_root / "output_json" / req.lang / f"{lesson_slug}_data.json"
    synced = artifact_root / "synced_json" / req.lang / f"{lesson_slug}_data.json"
    return output if output.exists() or not synced.exists() else synced


def _preview_url(req: ContentBuilderRequest) -> str:
    lesson = f"{req.lesson_start:03d}"
    return f"/dev/teaching-preview?pipeline={req.pipeline}&lang={req.lang}&lesson={lesson}"


def _run_command(argv: list[str], *, lesson_id: int, stage: str) -> Iterator[dict[str, Any]]:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    process = subprocess.Popen(
        argv,
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env=env,
    )
    try:
        assert process.stdout is not None
        for line in process.stdout:
            text = line.rstrip()
            if text:
                yield {
                    "type": "log",
                    "message": text,
                    "lesson_id": lesson_id,
                    "stage": stage,
                }
        return process.wait()
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
