"""
render_narration.py — Stage 2：母语旁白音轨渲染 + 静态教学幻灯片生成

从 JSON 文件中读取 video_render_plan，调用 TTS 生成旁白音轨，
将实际时长写回 JSON，然后生成 teaching_slide_deck 静态幻灯片清单。
mp4 讲解视频渲染已从 Stage 2 移除，由静态 slide deck 替代。

用法：
    # 指定单个或多个 JSON 文件
    python render_narration.py artifacts/integrated_chinese/output_json/en/lesson101_data.json
    python render_narration.py artifacts/integrated_chinese/output_json/fr/lesson1901_data_fr.json --lang fr --force-narration --force-slides

    # 不指定文件：扫描当前 pipeline 的 output_json/ 下所有 JSON 并处理
    python render_narration.py
    python render_narration.py --lang en
"""

import sys
import json
import re
import argparse
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[4]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from content_builder.core.artifacts import apply_narration_timings, atomic_write_json, narration_fingerprint, resolve_artifact_path
from content_builder.core.paths import default_paths
from content_builder.core.pipeline import get_pipeline
from content_builder.zh.integrated_chinese.scripts.build_teaching_slide_deck import build_deck

PATHS = default_paths()
BASE_DIR = PATHS.backend_dir                    # backend/
ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"

load_dotenv(dotenv_path=BASE_DIR / ".env")


def _extract_lesson_id(json_path: Path) -> int | None:
    numbers = re.findall(r'\d+', json_path.stem)
    return int(numbers[0]) if numbers else None


def _resolve_artifact_path(local_path: str, artifact_root: Path) -> Path:
    """Resolve stale artifact paths after a pipeline artifact-root migration."""
    p = Path(local_path)
    if p.exists():
        return p

    parts = p.parts
    try:
        idx = next(i for i, part in enumerate(parts) if part.lower() == "artifacts")
    except StopIteration:
        return p

    tail = Path(*parts[idx + 1:])
    artifact_root = Path(artifact_root)

    candidates = [artifact_root / tail]
    if tail.parts and tail.parts[0] in {"output_audio", "output_video", "output_json", "synced_json", "raw_materials", "archive_pdfs", "vocab_memory"}:
        candidates.append(artifact_root / Path(*tail.parts))
    if len(tail.parts) > 1 and tail.parts[0] in {"integrated_chinese", "new_concept_english"}:
        candidates.append(artifact_root / Path(*tail.parts[1:]))

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return p


def _merge_legacy_duplicate_segments(lesson_data: dict) -> int:
    """Merge adjacent legacy segments that were split visually but kept identical narration."""
    plan = (
        lesson_data.get("video_render_plan", {})
        .get("explanation", {})
    )
    segments = plan.get("segments", []) if isinstance(plan, dict) else []
    if not isinstance(segments, list) or len(segments) < 2:
        return 0

    merged = []
    merge_count = 0

    def narration_of(seg: dict) -> str:
        return ((seg.get("narration_track") or {}).get("subtitle_en") or "").strip()

    def hero_block(seg: dict) -> dict | None:
        for block in seg.get("visual_blocks", []) if isinstance(seg.get("visual_blocks"), list) else []:
            if isinstance(block, dict) and block.get("block_type") == "hero_line":
                return block
        return None

    def append_field(target: dict, source: dict, key: str) -> None:
        left = ((target.get("content") or {}).get(key) or "").strip()
        right = ((source.get("content") or {}).get(key) or "").strip()
        if not right or right in left:
            return
        content = target.setdefault("content", {})
        joiner = "" if key == "focus_text" else " "
        content[key] = f"{left}{joiner}{right}".strip() if left else right

    for seg in segments:
        if not isinstance(seg, dict):
            merged.append(seg)
            continue

        prev = merged[-1] if merged and isinstance(merged[-1], dict) else None
        is_duplicate = (
            prev is not None
            and (prev.get("segment_id") or prev.get("segment_order")) == (seg.get("segment_id") or seg.get("segment_order"))
            and narration_of(prev)
            and narration_of(prev) == narration_of(seg)
        )

        if not is_duplicate:
            merged.append(seg)
            continue

        prev_hero = hero_block(prev)
        seg_hero = hero_block(seg)
        if prev_hero and seg_hero:
            append_field(prev_hero, seg_hero, "focus_text")
            append_field(prev_hero, seg_hero, "focus_pinyin")
            append_field(prev_hero, seg_hero, "focus_gloss_en")
        prev["duration_seconds"] = max(float(prev.get("duration_seconds") or 0), float(seg.get("duration_seconds") or 0))
        prev["end_time_seconds"] = round(float(prev.get("start_time_seconds") or 0) + float(prev.get("duration_seconds") or 0), 3)
        merge_count += 1

    if merge_count:
        plan["segments"] = merged
        cursor = 0.0
        for order, seg in enumerate(merged, start=1):
            if not isinstance(seg, dict):
                continue
            seg["segment_order"] = order
            seg["start_time_seconds"] = round(cursor, 3)
            cursor += float(seg.get("duration_seconds") or 0)
            seg["end_time_seconds"] = round(cursor, 3)
        timeline = plan.setdefault("timeline", {})
        timeline["total_duration_seconds"] = round(cursor, 3)
        timeline["segment_count"] = len(merged)

    return merge_count


def _normalize_explanation_timeline(lesson_data: dict) -> None:
    plan = (
        lesson_data.get("video_render_plan", {})
        .get("explanation", {})
    )
    segments = plan.get("segments", []) if isinstance(plan, dict) else []
    if not isinstance(segments, list):
        return

    cursor = 0.0
    for order, seg in enumerate(segments, start=1):
        if not isinstance(seg, dict):
            continue
        duration = float(seg.get("duration_seconds") or seg.get("estimated_duration_seconds") or 0)
        seg["segment_order"] = seg.get("segment_order") or order
        seg["start_time_seconds"] = round(cursor, 3)
        cursor += max(0.0, duration)
        seg["end_time_seconds"] = round(cursor, 3)

    timeline = plan.setdefault("timeline", {})
    timeline["total_duration_seconds"] = round(cursor, 3)
    timeline["segment_count"] = len([seg for seg in segments if isinstance(seg, dict)])


def _expected_narration_path(artifact_root: Path, lesson_id: int, lang: str) -> Path:
    suffix = f"_{lang}" if lang != "en" else ""
    return artifact_root / "output_audio" / lang / f"lesson{lesson_id}_narration" / f"lesson{lesson_id}_narration{suffix}.mp3"


def _legacy_narration_path(artifact_root: Path, lesson_id: int, lang: str) -> Path:
    suffix = f"_{lang}" if lang != "en" else ""
    return artifact_root / "output_audio" / f"lesson{lesson_id}_narration{suffix}" / f"lesson{lesson_id}_narration{suffix}.mp3"


def process_file(
    agent,
    json_path: Path,
    lang: str = "en",
    pipeline_id: str = "integrated_chinese",
    force_narration: bool = False,
    force_slides: bool = False,
) -> bool:
    lesson_id = _extract_lesson_id(json_path)
    if lesson_id is None:
        print(f"⚠️ 无法从文件名提取 lesson_id，跳过: {json_path.name}")
        return False

    print(f"\n{'='*45}")
    print(f"🎙️ 处理: {json_path.name} (Lesson ID: {lesson_id})")

    with open(json_path, encoding="utf-8") as f:
        lesson_data = json.load(f)

    merged_legacy_segments = _merge_legacy_duplicate_segments(lesson_data)
    if merged_legacy_segments:
        print(f"  🧩 已合并旧版重复讲解 segment: {merged_legacy_segments} 个")
        if not force_narration:
            print("  ⚠️ 建议加 --force-narration 重生成旁白，否则旧音频仍可能包含重复段落。")

    signature = narration_fingerprint(lesson_data, lang)
    narration_info = lesson_data.get("explanation_narration_audio") or {}
    reusable = False
    if not force_narration and narration_info.get("input_fingerprint") == signature:
        try:
            recorded = resolve_artifact_path(narration_info.get("audio_file", ""), ARTIFACTS_DIR)
            narration_info["audio_file"] = str(recorded)
            apply_narration_timings(lesson_data, narration_info)
            reusable = True
        except (OSError, ValueError, KeyError):
            pass
    if reusable:
        print("  Reusing narration with matching text, voice, configuration and timings.")
    else:
        agent.render_narration(lesson_data, lesson_id, lang=lang)
        narration_info = lesson_data.get("explanation_narration_audio") or {}
        try:
            apply_narration_timings(lesson_data, narration_info)
        except (OSError, ValueError, KeyError) as exc:
            print(f"Narration failed: {exc}")
            atomic_write_json(json_path, lesson_data)
            return False
        narration_info["input_fingerprint"] = signature
    atomic_write_json(json_path, lesson_data)

    # Stage 2b: 静态教学幻灯片（替代旧 mp4 渲染）
    print(f"🖼️ 生成静态教学幻灯片 [lang={lang}]...")
    deck = build_deck(json_path, pipeline_id=pipeline_id, lang=lang, force=force_slides)
    print(f"✨ 静态教学幻灯片已生成，共 {deck.get('slide_count', 0)} 页。")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Stage 2：为 lesson JSON 生成母语旁白音轨和静态教学幻灯片。"
    )
    parser.add_argument(
        "json_files",
        nargs="*",
        help="要处理的 JSON 文件路径。不指定则扫描当前 pipeline 的 output_json/ 下所有文件。",
    )
    parser.add_argument(
        "--pipeline",
        default="integrated_chinese",
        help="教材流水线 ID（默认: integrated_chinese）。",
    )
    parser.add_argument(
        "--force-narration",
        action="store_true",
        help="即使旁白音轨已存在，也重新生成 TTS，并写回新的分句和时间轴。",
    )
    parser.add_argument(
        "--force-slides",
        action="store_true",
        help="即使静态幻灯片已存在，也重新生成 slide assets 和 teaching_slide_deck。",
    )
    parser.add_argument(
        "--lang",
        default="en",
        help="学习者语言代码，用于旁白和静态幻灯片输出目录（默认: en）。",
    )
    args = parser.parse_args()

    try:
        pipeline = get_pipeline(args.pipeline)
        global ARTIFACTS_DIR
        ARTIFACTS_DIR = pipeline.artifact_root(PATHS)
        agent = pipeline.create_agent(provider=None, memory_dir=ARTIFACTS_DIR)
        print(f"🧭 当前内容流水线: {pipeline.display_name} ({pipeline.pipeline_id})")
        print(f"🖼️ 静态教学幻灯片: 开启 [lang={args.lang}]")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return 1

    if args.json_files:
        targets = []
        for raw_path in args.json_files:
            path = Path(raw_path)
            if path.is_dir():
                found = sorted(path.glob("*_data*.json"), key=lambda p: _extract_lesson_id(p) or 0)
                print(f"📦 扫描目录 {path}: 找到 {len(found)} 个 JSON 文件。")
                targets.extend(found)
            else:
                targets.append(path)
    else:
        output_json_dir = pipeline.output_json_dir(PATHS, args.lang)
        targets = sorted(output_json_dir.glob("*_data*.json"), key=lambda p: _extract_lesson_id(p) or 0)
        if not targets:
            print(f"📭 {output_json_dir} 下没有找到 JSON 文件。")
            return 1
        print(f"📦 扫描到 {len(targets)} 个文件待处理。")

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
        ):
            success += 1
        else:
            failed += 1

    print(f"\n{'='*45}")
    print(f"✅ 完成：成功 {success} 个，失败 {failed} 个。")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
