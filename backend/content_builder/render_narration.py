"""
render_narration.py — Stage 2：母语旁白音轨渲染 + 可选讲解视频合成

从 JSON 文件中读取 video_render_plan，调用 TTS 生成旁白音轨，
并将实际时长写回 JSON。
加上 --render-video 后，会在旁白渲染完成后立即用 Remotion + ffmpeg
渲染讲解视频并保存到本地（不上传 R2，由 sync_to_db.py 统一上传）。

用法：
    # 指定单个或多个 JSON 文件
    python render_narration.py artifacts/integrated_chinese/output_json/en/lesson101_data.json
    python render_narration.py artifacts/integrated_chinese/output_json/en/lesson101_data.json --render-video
    python render_narration.py artifacts/integrated_chinese/output_json/en/lesson101_data.json --render-video --lang fr

    # 不指定文件：扫描当前 pipeline 的 output_json/ 下所有 JSON 并处理
    python render_narration.py
    python render_narration.py --render-video --lang en
"""

import sys
import json
import re
import subprocess
import argparse
from pathlib import Path

sys.stdout.reconfigure(line_buffering=True)
from dotenv import load_dotenv

from core.paths import default_paths
from core.pipeline import get_pipeline

PATHS = default_paths()
CURRENT_DIR = PATHS.content_builder_dir         # backend/content_builder/
BASE_DIR = PATHS.backend_dir                    # backend/
ARTIFACTS_DIR = PATHS.artifacts_dir

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


def render_explanation_video(lesson_id: int, lesson_data: dict, lang: str, pipeline_id: str = "integrated_chinese") -> dict:
    """
    Render explanation video locally (no R2 upload).
    1. Remotion renders silent video from JSON
    2. ffmpeg merges narration audio track
    3. Saves to artifacts/output_video/{lang}/

    Returns:
        {
            "local_path": str,   # absolute path to final mp4 (empty on failure)
            "object_key": str,   # intended R2 key (pre-computed, not uploaded yet)
            "lang": str,
        }
    """
    result = {"local_path": "", "object_key": "", "lang": lang}

    frontend_dir = BASE_DIR.parent / "frontend"
    render_script = frontend_dir / "scripts" / "render-explanation-video.mjs"

    if not frontend_dir.exists() or not render_script.exists():
        print(f"  ⚠️ 未找到前端 Remotion 渲染脚本，跳过 lesson{lesson_id} 讲解视频渲染。")
        return result

    output_dir = ARTIFACTS_DIR / "output_video" / lang
    output_dir.mkdir(parents=True, exist_ok=True)
    silent_video = output_dir / f"lesson{lesson_id}_explanation.mp4"

    if silent_video.exists():
        print(f"  ⏭️ 无声视频已存在，跳过渲染: {silent_video.name}")
    else:
        print(f"  🎞️ Remotion 渲染 lesson{lesson_id} 讲解视频（无声）...")
        try:
            subprocess.run(
                ["node", str(render_script), str(lesson_id), lang, pipeline_id],
                cwd=str(frontend_dir),
                check=True,
            )
            # Remotion 默认输出到 artifacts/output_video/，移动到 lang 子目录
            default_out = ARTIFACTS_DIR / "output_video" / f"lesson{lesson_id}_explanation.mp4"
            if default_out.exists() and default_out != silent_video:
                if silent_video.exists():
                    silent_video.unlink()
                default_out.rename(silent_video)
            print(f"  ✅ 无声视频渲染完成: {silent_video.name}")
        except FileNotFoundError:
            print("  ⚠️ 当前环境缺少 node 命令，跳过讲解视频渲染。")
            return result
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️ Remotion 渲染失败（退出码 {e.returncode}），已跳过。")
            return result

    # Merge narration audio
    narration_info = lesson_data.get("explanation_narration_audio", {})
    narration_file = narration_info.get("audio_file", "") if narration_info.get("status") == "ok" else ""
    narration_path = _resolve_artifact_path(narration_file, ARTIFACTS_DIR) if narration_file else Path("")

    final_video = output_dir / f"lesson{lesson_id}_explanation_final.mp4"

    if final_video.exists():
        print(f"  ⏭️ 最终视频已存在，跳过合并: {final_video.name}")
        result["local_path"] = str(final_video)
        result["object_key"] = f"zh/video/{lang}/lesson{lesson_id}_explanation_final.mp4"
        return result

    if narration_file and narration_path.exists() and silent_video.exists():
        print(f"  🎙️ ffmpeg 合并旁白音轨 → {final_video.name}...")
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", str(silent_video),
                    "-i", str(narration_path),
                    "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac",
                    "-shortest",
                    str(final_video),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            print(f"  ✅ 讲解视频（含旁白）已生成: {final_video.name}")
            result["local_path"] = str(final_video)
        except Exception as e:
            print(f"  ⚠️ ffmpeg 合并失败，使用无声版本: {e}")
            result["local_path"] = str(silent_video) if silent_video.exists() else ""
    else:
        if not narration_file:
            print(f"  ℹ️ 无旁白音轨，输出无声版本: {silent_video.name}")
        result["local_path"] = str(silent_video) if silent_video.exists() else ""

    if result["local_path"]:
        result["object_key"] = f"zh/video/{lang}/lesson{lesson_id}_explanation_final.mp4"

    return result


def process_file(
    agent,
    json_path: Path,
    should_render_video: bool = False,
    lang: str = "en",
    pipeline_id: str = "integrated_chinese",
) -> bool:
    lesson_id = _extract_lesson_id(json_path)
    if lesson_id is None:
        print(f"⚠️ 无法从文件名提取 lesson_id，跳过: {json_path.name}")
        return False

    print(f"\n{'='*45}")
    print(f"🎙️ 处理: {json_path.name} (Lesson ID: {lesson_id})")

    with open(json_path, encoding="utf-8") as f:
        lesson_data = json.load(f)

    # Stage 2a: 旁白 TTS（已存在则跳过）
    # 根据 lang 计算预期的输出文件路径，避免误用其他语言的旧路径
    lang_suffix = f"_{lang}" if lang != "en" else ""
    expected_narration = (
        ARTIFACTS_DIR / "output_audio"
        / f"lesson{lesson_id}_narration{lang_suffix}"
        / f"lesson{lesson_id}_narration{lang_suffix}.mp3"
    )
    if expected_narration.exists():
        print(f"  ⏭️ 旁白音轨已存在，跳过 TTS: {expected_narration.name}")
        narration_info = lesson_data.get("explanation_narration_audio", {})
        recorded_audio = narration_info.get("audio_file", "") if isinstance(narration_info, dict) else ""
        recorded_path = _resolve_artifact_path(recorded_audio, ARTIFACTS_DIR) if recorded_audio else Path("")
        if narration_info.get("status") != "ok" or recorded_path != expected_narration:
            lesson_data["explanation_narration_audio"] = {
                **(narration_info if isinstance(narration_info, dict) else {}),
                "status": "ok",
                "audio_file": str(expected_narration),
            }
    else:
        agent.render_narration(lesson_data, lesson_id, lang=lang)

    # 写回 JSON（含实际 TTS 时长），视频渲染前必须落盘，Remotion 会从文件读取
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(lesson_data, f, ensure_ascii=False, indent=2)
    print(f"📄 已更新: {json_path.name}")

    # Stage 2b: 视频渲染（可选，读取上方已更新的 JSON）
    if should_render_video:
        print(f"🎬 渲染讲解视频 [lang={lang}]...")
        video_info = render_explanation_video(lesson_id, lesson_data, lang, pipeline_id=pipeline_id)
        if video_info["local_path"]:
            lesson_data["explanation_video_urls"] = {
                "media_url":   "",
                "object_key":  video_info["object_key"],
                "local_path":  video_info["local_path"],
                "lang":        lang,
                "youtube_url": "",
                "bilibili_url": "",
            }
            # 将视频路径写回 JSON
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(lesson_data, f, ensure_ascii=False, indent=2)
            print(f"📄 已更新 (含视频路径): {json_path.name}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Stage 2：为 lesson JSON 生成母语旁白音轨，并可选渲染讲解视频（本地）。"
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
        "--render-video",
        action="store_true",
        help="旁白渲染后立即渲染讲解视频（Remotion + ffmpeg 合并旁白音轨）。需要 Node.js。",
    )
    parser.add_argument(
        "--lang",
        default="en",
        help="学习者语言代码，用于视频输出目录及 R2 路径（默认: en）。",
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
        if args.render_video:
            print(f"🎬 视频渲染: 开启 [lang={args.lang}]")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return

    if args.json_files:
        targets = [Path(p) for p in args.json_files]
    else:
        output_json_dir = pipeline.output_json_dir(PATHS, args.lang)
        targets = sorted(output_json_dir.glob("*_data*.json"), key=lambda p: _extract_lesson_id(p) or 0)
        if not targets:
            print(f"📭 {output_json_dir} 下没有找到 JSON 文件。")
            return
        print(f"📦 扫描到 {len(targets)} 个文件待处理。")

    success, failed = 0, 0
    for json_path in targets:
        if not json_path.exists():
            print(f"⚠️ 文件不存在，跳过: {json_path}")
            failed += 1
            continue
        if process_file(agent, json_path, should_render_video=args.render_video, lang=args.lang, pipeline_id=pipeline.pipeline_id):
            success += 1
        else:
            failed += 1

    print(f"\n{'='*45}")
    print(f"✅ 完成：成功 {success} 个，失败 {failed} 个。")


if __name__ == "__main__":
    main()
