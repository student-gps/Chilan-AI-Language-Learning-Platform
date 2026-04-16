"""
一次性脚本：把 frontend/public/audio/intro/ 下所有音频文件上传到 R2。
R2 路径约定：zh/audio/intro/{filename}

用法：
    cd backend
    python upload_intro_audio_to_r2.py

生成音频请先运行：
    python generate_intro_narration.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from services.storage.r2_storage import R2Storage

BACKEND_DIR = Path(__file__).resolve().parent
INTRO_AUDIO_DIR = BACKEND_DIR.parent / "frontend" / "public" / "audio" / "intro"
R2_PREFIX = "zh/audio/intro"


def main():
    if not INTRO_AUDIO_DIR.exists():
        print(f"❌ 目录不存在: {INTRO_AUDIO_DIR}")
        print("   请先运行: python generate_intro_narration.py")
        sys.exit(1)

    audio_files = sorted(
        f for f in INTRO_AUDIO_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in {".mp3", ".wav"}
    )

    if not audio_files:
        print("⚠️  intro 音频目录下没有找到音频文件。")
        print("   请先运行: python generate_intro_narration.py")
        sys.exit(0)

    storage = R2Storage.from_env()
    print(f"📂 共找到 {len(audio_files)} 个音频文件，开始上传到 R2 ({R2_PREFIX}/)...\n")

    ok, fail = 0, 0
    for f in audio_files:
        object_key = f"{R2_PREFIX}/{f.name}"
        try:
            result = storage.upload_file(f, object_key)
            print(f"  ✅  {f.name}  →  {result['public_url']}")
            ok += 1
        except Exception as e:
            print(f"  ❌  {f.name}  →  {e}")
            fail += 1

    print(f"\n完成：{ok} 成功，{fail} 失败。")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
