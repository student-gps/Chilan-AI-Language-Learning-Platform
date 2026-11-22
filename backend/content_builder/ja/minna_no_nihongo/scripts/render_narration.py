from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.stdout.reconfigure(line_buffering=True)

BACKEND_DIR = Path(__file__).resolve().parents[4]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from content_builder.core.paths import default_paths
from content_builder.core.pipeline import get_pipeline
from content_builder.ja.minna_no_nihongo.scripts.build_teaching_slide_deck import build_deck
from content_builder.ja.minna_no_nihongo.tasks.render_plan_builder import MinnaNoNihongoRenderPlanBuilder


PATHS = default_paths()
BASE_DIR = PATHS.backend_dir
ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"

load_dotenv(dotenv_path=BASE_DIR / ".env")


def _extract_lesson_id(json_path: Path) -> int | None:
    numbers = re.findall(r"\d+", json_path.stem)
    return int(numbers[0]) if numbers else None


def _lesson_digits(lesson_id: int | str) -> str:
    return f"{int(lesson_id):03d}" if str(lesson_id).isdigit() else str(lesson_id)


def _normalize_explanation_timeline(lesson_data: dict) -> None:
    plan = (lesson_data.get("video_render_plan", {}) or {}).get("explanation", {})
    segments = plan.get("segments", []) if isinstance(plan, dict) else []
    if not isinstance(segments, list):
        return

    cursor = 0.0
    count = 0
    for order, segment in enumerate(segments, start=1):
        if not isinstance(segment, dict):
            continue
        duration = float(segment.get("duration_seconds") or segment.get("estimated_duration_seconds") or 0)
        segment["segment_order"] = segment.get("segment_order") or order
        segment["start_time_seconds"] = round(cursor, 3)
        cursor += max(0.0, duration)
        segment["end_time_seconds"] = round(cursor, 3)
        count += 1

    timeline = plan.setdefault("timeline", {})
    timeline["total_duration_seconds"] = round(cursor, 3)
    timeline["segment_count"] = count


def _expected_narration_path(artifact_root: Path, lesson_id: int, lang: str) -> Path:
    suffix = f"_{lang}" if lang != "en" else ""
    lesson_slug = f"lesson{lesson_id:03d}"
    return artifact_root / "output_audio" / lang / f"{lesson_slug}_narration" / f"{lesson_slug}_narration{suffix}.mp3"


def _recorded_audio_matches(narration_info: dict, expected_path: Path) -> bool:
    if not isinstance(narration_info, dict) or narration_info.get("status") != "ok":
        return False
    audio_file = narration_info.get("audio_file")
    if not audio_file:
        return False
    return Path(audio_file) == expected_path and expected_path.exists()


def _refresh_render_plan(lesson_data: dict) -> None:
    metadata = lesson_data.get("lesson_metadata") if isinstance(lesson_data.get("lesson_metadata"), dict) else {}
    course_content = lesson_data.get("course_content") if isinstance(lesson_data.get("course_content"), dict) else {}
    lesson_data["video_render_plan"] = MinnaNoNihongoRenderPlanBuilder().run(
        metadata,
        course_content,
        existing_plan=None,
    )


def process_file(
    agent,
    json_path: Path,
    *,
    lang: str,
    pipeline_id: str,
    force_narration: bool = False,
    force_slides: bool = False,
    refresh_render_plan: bool = False,
) -> bool:
    lesson_id = _extract_lesson_id(json_path)
    if lesson_id is None:
        print(f"⚠️ 无法从文件名提取 lesson_id，跳过: {json_path.name}")
        return False

    print(f"\n{'=' * 45}")
    print(f"🎙️ 处理: {json_path.name} (Lesson: {lesson_id:03d}, lang={lang})")

    with json_path.open(encoding="utf-8") as handle:
        lesson_data = json.load(handle)
    if refresh_render_plan:
        _refresh_render_plan(lesson_data)

    expected_narration = _expected_narration_path(ARTIFACTS_DIR, lesson_id, lang)
    if force_narration and expected_narration.exists():
        expected_narration.unlink()
        print(f"  ♻️ 已删除旧旁白音轨: {expected_narration.name}")

    narration_info = lesson_data.get("explanation_narration_audio", {})
    if not force_narration and _recorded_audio_matches(narration_info, expected_narration):
        print(f"  ⏭️ 复用已有旁白音轨: {expected_narration.name}")
    else:
        agent.render_narration(lesson_data, lesson_id, lang=lang)

    _normalize_explanation_timeline(lesson_data)
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(lesson_data, handle, ensure_ascii=False, indent=2)
    print(f"📄 已更新: {json_path.name}")

    narration_info = lesson_data.get("explanation_narration_audio", {})
    if not isinstance(narration_info, dict) or narration_info.get("status") != "ok":
        print(f"❌ 旁白音轨未生成成功，跳过静态幻灯片: {narration_info.get('reason', '') if isinstance(narration_info, dict) else ''}")
        return False

    print(f"🖼️ 生成日语静态教学幻灯片 [lang={lang}]...")
    deck = build_deck(json_path, pipeline_id=pipeline_id, lang=lang, force=force_slides)
    print(f"✨ 日语静态教学幻灯片已生成，共 {deck.get('slide_count', 0)} 页。")
    return True


def _resolve_targets(args, pipeline) -> list[Path]:
    if args.json_files:
        targets: list[Path] = []
        for raw_path in args.json_files:
            path = Path(raw_path)
            if path.is_dir():
                found = sorted(path.glob("*_data*.json"), key=lambda item: _extract_lesson_id(item) or 0)
                print(f"📦 扫描目录 {path}: 找到 {len(found)} 个 JSON 文件。")
                targets.extend(found)
            else:
                targets.append(path)
        return targets

    output_json_dir = pipeline.output_json_dir(PATHS, args.lang)
    targets = sorted(output_json_dir.glob("*_data*.json"), key=lambda item: _extract_lesson_id(item) or 0)
    if targets:
        print(f"📦 扫描到 {len(targets)} 个文件待处理。")
    return targets


def main() -> None:
    parser = argparse.ArgumentParser(description="MNN Stage 2：生成中文旁白音轨和静态教学幻灯片。")
    parser.add_argument("json_files", nargs="*", help="要处理的 JSON 文件路径。不指定则扫描 output_json/<lang>。")
    parser.add_argument("--pipeline", default="minna_no_nihongo", help="教材流水线 ID。")
    parser.add_argument("--lang", default="zh", help="学习者语言代码，默认 zh。")
    parser.add_argument("--force-narration", action="store_true", help="即使旁白已存在也重新生成。")
    parser.add_argument("--force-slides", action="store_true", help="即使幻灯片已存在也重新生成。")
    parser.add_argument(
        "--refresh-render-plan",
        action="store_true",
        help="重新用 deterministic builder 刷新 render plan。默认不刷新，以保留 Stage 1 的 LLM narration。",
    )
    args = parser.parse_args()

    try:
        pipeline = get_pipeline(args.pipeline)
        global ARTIFACTS_DIR
        ARTIFACTS_DIR = pipeline.artifact_root(PATHS)
        provider = pipeline.create_provider()
        agent = pipeline.create_agent(provider=provider, memory_dir=ARTIFACTS_DIR)
        print(f"🔧 当前激活模型引擎: {type(provider).__name__}")
        print(f"🧭 当前内容流水线: {pipeline.display_name} ({pipeline.pipeline_id})")
        print(f"🖼️ 静态教学幻灯片: 开启 [lang={args.lang}]")
    except Exception as exc:
        print(f"❌ 初始化失败: {exc}")
        return

    targets = _resolve_targets(args, pipeline)
    if not targets:
        print(f"📭 未找到待处理 JSON。")
        return

    success, failed = 0, 0
    for json_path in targets:
        if not json_path.exists():
            print(f"⚠️ 文件不存在，跳过: {json_path}")
            failed += 1
            continue
        if process_file(
            agent,
            json_path,
            lang=args.lang,
            pipeline_id=pipeline.pipeline_id,
            force_narration=args.force_narration,
            force_slides=args.force_slides,
            refresh_render_plan=args.refresh_render_plan,
        ):
            success += 1
        else:
            failed += 1

    print(f"\n{'=' * 45}")
    print(f"✅ Stage 2 完成：成功 {success} 个，失败 {failed} 个。")


if __name__ == "__main__":
    main()
