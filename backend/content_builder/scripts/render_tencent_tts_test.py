import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

import sys

CURRENT_DIR = Path(__file__).resolve().parent
CONTENT_BUILDER_DIR = CURRENT_DIR.parent
ARTIFACTS_DIR = CONTENT_BUILDER_DIR / "artifacts" / "integrated_chinese"
if str(CONTENT_BUILDER_DIR) not in sys.path:
    sys.path.insert(0, str(CONTENT_BUILDER_DIR))

from tasks.dialogue_audio import Task4BLessonAudioRenderer


def parse_args():
    parser = argparse.ArgumentParser(description="测试腾讯云逐句课文音频生成。")
    parser.add_argument("--lesson-id", type=int, required=True, help="要测试的 lesson 编号，例如 101")
    parser.add_argument("--include-speakers", action="store_true", help="是否在音频文本中加入说话人名字")
    parser.add_argument("--enable-subtitle", action="store_true", help="是否请求字级时间戳信息")
    parser.add_argument("--voice-type", type=int, default=None, help="可选，覆盖默认音色 ID")
    return parser.parse_args()


def main():
    current_dir = CURRENT_DIR
    content_builder_dir = CONTENT_BUILDER_DIR
    backend_dir = content_builder_dir.parent
    load_dotenv(dotenv_path=backend_dir / ".env")

    args = parse_args()
    lesson_id = args.lesson_id

    source_file = ARTIFACTS_DIR / "output_json" / "en" / f"lesson{lesson_id}_data.json"
    if not source_file.exists():
        raise FileNotFoundError(f"未找到 lesson 数据文件: {source_file}")

    with open(source_file, "r", encoding="utf-8") as f:
        lesson_data = json.load(f)

    renderer = Task4BLessonAudioRenderer(voice_type=args.voice_type)
    output_audio_dir = ARTIFACTS_DIR / "output_audio" / f"lesson{lesson_id}"

    result = renderer.render_sentence_audio_assets(
        lesson_data=lesson_data,
        output_dir=output_audio_dir,
        include_speakers=args.include_speakers,
        enable_subtitle=args.enable_subtitle,
    )

    output_file = ARTIFACTS_DIR / "output_json" / "en" / f"lesson{lesson_id}_tencent_tts.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    items = result.get("lesson_audio_assets", {}).get("items", [])
    print(
        f"✅ 腾讯云逐句 TTS 完成 | lesson={lesson_id} | "
        f"items={len(items)} | output_dir={output_audio_dir}"
    )
    print(f"📄 输出文件: {output_file}")


if __name__ == "__main__":
    main()
