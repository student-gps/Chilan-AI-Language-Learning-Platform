import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from tasks.task4a_dramatization_renderer import Task4ADramatizationRenderer


def parse_args():
    parser = argparse.ArgumentParser(description="检查已有 Luma 渲染任务状态，不重复提交。")
    parser.add_argument("--lesson-id", type=int, required=True, help="要检查的 lesson 编号，例如 101")
    parser.add_argument("--wait", action="store_true", help="是否持续轮询直到全部任务完成或失败")
    parser.add_argument("--poll-interval", type=int, default=3, help="轮询间隔秒数，默认 3")
    parser.add_argument("--timeout", type=int, default=600, help="单个任务最大等待秒数，默认 600")
    return parser.parse_args()


def _extract_asset_url(generation: dict, asset_name: str) -> str:
    assets = generation.get("assets", {}) if isinstance(generation, dict) else {}
    if not isinstance(assets, dict):
        return ""
    value = assets.get(asset_name)
    return value.strip() if isinstance(value, str) else ""


def main():
    current_dir = Path(__file__).resolve().parent
    backend_dir = current_dir.parent
    load_dotenv(dotenv_path=backend_dir / ".env")

    args = parse_args()
    lesson_id = args.lesson_id

    render_file = current_dir / "output_json" / f"lesson{lesson_id}_luma_render.json"
    if not render_file.exists():
        raise FileNotFoundError(f"未找到 Luma 渲染结果文件: {render_file}")

    with open(render_file, "r", encoding="utf-8") as f:
        render_data = json.load(f)

    artifacts = render_data.get("render_artifacts", {})
    clips = artifacts.get("dramatization_clips", []) if isinstance(artifacts.get("dramatization_clips"), list) else []
    if not clips:
        raise ValueError("当前渲染结果中没有 dramatization_clips，无法查询状态。")

    renderer = Task4ADramatizationRenderer(poll_interval_seconds=args.poll_interval)

    print(f"🔎 开始检查 lesson {lesson_id} 的 Luma 渲染状态，共 {len(clips)} 条。")

    updated = False
    for clip in clips:
        generation_id = (clip.get("generation_id") or "").strip()
        if not generation_id:
            print(f"  ⚠️ scene {clip.get('scene_id')} 缺少 generation_id，跳过。")
            continue

        scene_id = clip.get("scene_id")
        print(f"  ▶️ 正在检查 scene {scene_id} | generation_id={generation_id}")

        if args.wait:
            generation = renderer.wait_for_generation(generation_id, timeout_seconds=args.timeout)
        else:
            generation = renderer.get_generation(generation_id)

        state = (generation.get("state") or "").strip()
        clip["status"] = state or clip.get("status", "")
        clip["video_url"] = _extract_asset_url(generation, "video")
        clip["thumbnail_url"] = _extract_asset_url(generation, "image")
        updated = True

        print(
            f"    状态: {clip['status']} | "
            f"video_url={'有' if clip.get('video_url') else '无'} | "
            f"thumbnail_url={'有' if clip.get('thumbnail_url') else '无'}"
        )

    if updated:
        with open(render_file, "w", encoding="utf-8") as f:
            json.dump(render_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 状态已回写: {render_file}")


if __name__ == "__main__":
    main()
