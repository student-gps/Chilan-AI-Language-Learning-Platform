"""
一次性脚本：为课程介绍幻灯片生成 TTS 旁白音频。

输出目录：frontend/public/audio/intro/slide_{id}.mp3
前端通过 /audio/intro/slide_{id}.mp3 直接引用（Vite 静态资源）。

用法：
    cd backend
    python generate_intro_narration.py

    # 指定 TTS 提供商（默认读 .env 里的 TTS_EXPLANATION_PROVIDER）：
    TTS_EXPLANATION_PROVIDER=ali python generate_intro_narration.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from content_builder.tasks.narration_audio import Task4DExplanationNarrator

# ── 与前端 SLIDES 对应的旁白文本（顺序和 id 必须与 CourseIntroVideo.jsx 一致）────

SLIDES = [
    {
        "id": "welcome",
        "narration": (
            "Welcome to Chilan — an AI-powered Chinese language learning platform. "
            "This course builds real communication skills: listening, speaking, and typing. "
            "We start from first principles, beginning with the sound system."
        ),
    },
    {
        "id": "sounds",
        "narration": (
            "Every Chinese syllable has a tone, and changing the tone completely changes the meaning. "
            "The four tones are high and level, rising, falling-rising, and falling. "
            "Mastering tones is the single most important foundation in Chinese."
        ),
    },
    {
        "id": "skills",
        "narration": (
            "This course trains three core skills: listening, speaking, and typing with a pinyin input method. "
            "We focus on how Chinese is actually used in daily digital life — not handwriting. "
            "You'll be able to read, listen, speak, and type before long."
        ),
    },
    {
        "id": "ai",
        "narration": (
            "Every answer you submit is evaluated by a three-tier system. "
            "Instant pattern matching handles obvious cases. "
            "Semantic comparison catches answers that mean the same thing in different words. "
            "And a large language model handles genuine edge cases with a detailed explanation."
        ),
    },
    {
        "id": "fsrs",
        "narration": (
            "Your review schedule is powered by FSRS — the Free Spaced Repetition Scheduler. "
            "Items you know well come back less often. Tricky items reappear sooner. "
            "This ensures you spend your study time exactly where it's needed."
        ),
    },
    {
        "id": "start",
        "narration": (
            "You're ready to begin. "
            "Start with the foundation modules: pinyin for the sound system, "
            "then Chinese characters for structure. "
            "Every lesson in the course builds on these foundations."
        ),
    },
]

# 输出到 frontend/public/audio/intro/，Vite 构建时会直接复制到 dist/
BACKEND_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BACKEND_DIR.parent / "frontend" / "public" / "audio" / "intro"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tts = Task4DExplanationNarrator()
    print(f"TTS provider: {tts.provider}")
    print(f"Output dir:   {OUTPUT_DIR}\n")

    ok, fail = 0, 0
    for slide in SLIDES:
        slide_id = slide["id"]
        text = slide["narration"]
        out_path = OUTPUT_DIR / f"slide_{slide_id}.mp3"

        print(f"🔊  [{slide_id}]  {text[:60]}…")
        try:
            tts._synthesize(text, out_path)
            size_kb = out_path.stat().st_size // 1024
            print(f"  ✅  saved → {out_path.name}  ({size_kb} KB)\n")
            ok += 1
        except Exception as e:
            print(f"  ❌  failed: {e}\n")
            fail += 1

    print(f"完成：{ok} 成功，{fail} 失败。")
    print(f"\n前端引用路径：/audio/intro/slide_{{id}}.mp3")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
