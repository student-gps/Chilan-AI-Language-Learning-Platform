import argparse
import json
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="检查已生成的腾讯云逐句课文音频结果。")
    parser.add_argument("--lesson-id", type=int, required=True, help="要检查的 lesson 编号，例如 101")
    return parser.parse_args()


def main():
    current_dir = Path(__file__).resolve().parent
    args = parse_args()
    lesson_id = args.lesson_id

    render_file = current_dir / "output_json" / f"lesson{lesson_id}_tencent_tts.json"
    if not render_file.exists():
        raise FileNotFoundError(f"未找到腾讯云 TTS 结果文件: {render_file}")

    with open(render_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assets = data.get("lesson_audio_assets", {})
    items = assets.get("items", []) if isinstance(assets.get("items"), list) else []
    ready_count = 0

    print(
        f"🔎 lesson={lesson_id} | title={assets.get('lesson_title', '')} | "
        f"provider={assets.get('provider', '')} | items={len(items)}"
    )

    for item in items:
        local_audio_file = item.get("local_audio_file", "")
        exists = Path(local_audio_file).exists() if local_audio_file else False
        if exists:
            ready_count += 1
        print(
            f"line_ref={item.get('line_ref')} | "
            f"status={item.get('status', '')} | "
            f"exists={exists} | "
            f"text={item.get('hanzi', '')}"
        )

    print(f"✅ 检查完成 | ready_files={ready_count}/{len(items)}")


if __name__ == "__main__":
    main()
