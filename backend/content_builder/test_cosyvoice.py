"""
test_cosyvoice.py — DashScope CosyVoice TTS 测试

测试四种输入方式，对比混合中英文旁白效果：
  A. 纯文本 + language_hints
  B. 拼音替代汉字（带调符）
  C. SSML <phoneme> 标签
  D. hot_fix.pronunciation（数字声调，仅 v3-flash 复刻音色支持）

运行方式：
    cd backend/content_builder
    python test_cosyvoice.py

输出文件保存到 test_tts_output/ 目录
"""

import os
import sys
import json
import requests
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

# ── 配置 ──────────────────────────────────────────────────────────────────────
API_KEY  = os.environ.get("LLM_ALI_API_KEY", "")
ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer"

# ⚠️ v3.5 系列没有系统音色，只支持声音复刻/设计音色
# 如果你有声音复刻 ID，填在这里；否则改用 cosyvoice-v3-plus + 系统音色
MODEL = "cosyvoice-v3-plus"
VOICE = "longanyang"   # 系统音色，可替换为其他 v3-plus 支持的音色

OUTPUT_DIR = Path(__file__).parent / "test_tts_output"

# 测试文本（模拟旁白常见的中英混合场景）
SENTENCE = '"你" means You, while "好" means Good. Together, 你好 is the most common Chinese greeting.'

TEST_CASES = {
    "A_plain_hint": {
        "desc": "纯文本 + language_hints=['en']（v3-plus）",
        "input": {
            "text": SENTENCE,
            "voice": VOICE,
            "format": "mp3",
            "sample_rate": 24000,
            "language_hints": ["en"],
        },
    },
    "B_pinyin": {
        "desc": "拼音替代汉字（带调符）+ language_hints（v3-plus）",
        "input": {
            "text": '"nǐ" means You, while "hǎo" means Good. Together, nǐ hǎo, is the most common Chinese greeting.',
            "voice": VOICE,
            "format": "mp3",
            "sample_rate": 24000,
            "language_hints": ["en"],
        },
    },
    "C_ssml_phoneme": {
        "desc": "SSML <phoneme> 指定声调，无隔断（v3-plus）",
        "input": {
            "text": (
                "<speak>"
                'The word <phoneme alphabet="py" ph="ni3">你</phoneme> means You, '
                'while <phoneme alphabet="py" ph="hao3">好</phoneme> means Good. '
                'Together, <phoneme alphabet="py" ph="ni3 hao3">你好</phoneme> '
                "is the most common Chinese greeting."
                "</speak>"
            ),
            "voice": VOICE,
            "format": "mp3",
            "sample_rate": 24000,
            "enable_ssml": True,
        },
    },
    # ✅ 已验证有效版本（勿轻易修改）
    # 模型: cosyvoice-v3-plus（v3-flash 同样有效）
    # 音色: longanyang（均支持 SSML）
    # 方案: 单 <speak> 块，phoneme 指定声调 + <break time="300ms"/> 隔断上下文
    # 效果: 声调准确，单字发音自然，无音质失真
    "D_ssml_break": {
        "desc": "SSML phoneme + break 300ms，单 speak 块（v3-plus，原始有效版本）",
        "input": {
            "text": (
                "<speak>"
                'The word <phoneme alphabet="py" ph="ni3">你</phoneme>'
                '<break time="300ms"/>'
                "means You, while "
                '<phoneme alphabet="py" ph="hao3">好</phoneme>'
                '<break time="300ms"/>'
                "means Good."
                "</speak>"
            ),
            "voice": VOICE,
            "format": "mp3",
            "sample_rate": 24000,
            "enable_ssml": True,
        },
    },
}

# ── 合成 ──────────────────────────────────────────────────────────────────────
def synthesize(case_key: str, case: dict) -> bool:
    model = case.get("model_override", MODEL)
    body = {
        "model": model,
        "input": case["input"],
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    print(f"\n[{case_key}] {case['desc']}")
    print(f"  模型: {model}")
    print(f"  输入: {str(case['input'].get('text', ''))[:80]}...")

    try:
        resp = requests.post(ENDPOINT, headers=headers, json=body, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.HTTPError as e:
        print(f"  ❌ HTTP {e.response.status_code}: {e.response.text[:200]}")
        return False
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        return False

    audio_url = data.get("output", {}).get("audio", {}).get("url", "")
    chars_used = data.get("usage", {}).get("characters", "?")

    if not audio_url:
        print(f"  ❌ 未返回音频 URL，响应: {json.dumps(data, ensure_ascii=False)[:300]}")
        return False

    # 下载音频
    try:
        audio_resp = requests.get(audio_url, timeout=30)
        audio_resp.raise_for_status()
        output_path = OUTPUT_DIR / f"test_{case_key}.mp3"
        output_path.write_bytes(audio_resp.content)
        size_kb = output_path.stat().st_size / 1024
        print(f"  ✅ 已保存: {output_path.name}  ({size_kb:.1f} KB)  计费字符: {chars_used}")
        return True
    except Exception as e:
        print(f"  ❌ 音频下载失败: {e}")
        return False


# ── 主流程 ────────────────────────────────────────────────────────────────────
def main():
    if not API_KEY:
        print("❌ LLM_ALI_API_KEY 未配置，请检查 backend/.env")
        return
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"{'=' * 55}")
    print(f"模型: {MODEL}  音色: {VOICE}")
    print(f"{'=' * 55}")

    results = {}
    for key, case in TEST_CASES.items():
        results[key] = synthesize(key, case)

    print(f"\n{'─' * 55}")
    print("测试结果汇总:")
    for key, ok in results.items():
        status = "✅" if ok else "❌"
        print(f"  {status} {key}: {TEST_CASES[key]['desc']}")
    print(f"输出目录: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
