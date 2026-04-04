import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from tasks.task4a_dramatization_renderer import Task4ADramatizationRenderer


def parse_args():
    parser = argparse.ArgumentParser(description="测试 Luma task4a 情景演绎渲染。")
    parser.add_argument("--lesson-id", type=int, required=True, help="要测试的 lesson 编号，例如 101")
    parser.add_argument("--scene-limit", type=int, default=2, help="最多提交多少个 scene，默认 2")
    parser.add_argument("--wait", action="store_true", help="是否轮询直到生成完成")
    parser.add_argument("--duration", type=str, default="5s", help="Luma 单个 scene 时长，例如 5s")
    parser.add_argument("--resolution", type=str, default="720p", help="Luma 分辨率，例如 720p")
    parser.add_argument("--aspect-ratio", type=str, default="16:9", help="Luma 宽高比，例如 16:9")
    return parser.parse_args()


def main():
    current_dir = Path(__file__).resolve().parent
    backend_dir = current_dir.parent
    load_dotenv(dotenv_path=backend_dir / ".env")

    args = parse_args()
    lesson_id = args.lesson_id

    source_file = current_dir / "output_json" / f"lesson{lesson_id}_data.json"
    if not source_file.exists():
        raise FileNotFoundError(f"未找到 lesson 数据文件: {source_file}")

    with open(source_file, "r", encoding="utf-8") as f:
        lesson_data = json.load(f)

    video_plan = lesson_data.get("video_plan", {})
    if not isinstance(video_plan, dict) or not video_plan:
        raise ValueError("当前 lesson 数据中不存在有效的 video_plan。")

    renderer = Task4ADramatizationRenderer(
        duration=args.duration,
        resolution=args.resolution,
        aspect_ratio=args.aspect_ratio,
    )

    print(
        f"🎬 开始测试 Luma task4a | lesson={lesson_id} | "
        f"scene_limit={args.scene_limit} | wait={args.wait}"
    )

    result = renderer.render_video_plan(
        video_plan=video_plan,
        scene_limit=args.scene_limit,
        wait_for_result=args.wait,
    )

    output_file = current_dir / "output_json" / f"lesson{lesson_id}_luma_render.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    clips = result.get("render_artifacts", {}).get("dramatization_clips", [])
    print(f"✅ Luma 测试完成，共写入 {len(clips)} 条渲染记录。")
    print(f"📄 输出文件: {output_file}")


if __name__ == "__main__":
    main()
