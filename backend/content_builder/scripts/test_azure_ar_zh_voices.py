"""
test_azure_ar_zh_voices.py — Azure 中阿混合旁白声色试听

生成多组「阿拉伯语 voice + 中文 voice」混合 TTS 小样，方便人工试听后选择
TTS_EXPLANATION_VOICE_AR。中文 voice 默认固定为 zh-CN-YunjianNeural。

运行方式：
    cd backend/content_builder
    python scripts/test_azure_ar_zh_voices.py

可选：
    python scripts/test_azure_ar_zh_voices.py --limit 4
    python scripts/test_azure_ar_zh_voices.py --ar-voices ar-SA-HamedNeural,ar-SA-ZariyahNeural
    python scripts/test_azure_ar_zh_voices.py --zh-voice zh-CN-YunjianNeural

输出目录：
    artifacts/test_tts_output/azure_ar_zh/
"""

import argparse
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

CONTENT_BUILDER_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = CONTENT_BUILDER_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from config.env import get_env

load_dotenv(BACKEND_DIR / ".env")

DEFAULT_AR_VOICES = [
    "ar-SA-HamedNeural",
    "ar-SA-ZariyahNeural",
    "ar-EG-ShakirNeural",
    "ar-EG-SalmaNeural",
    "ar-AE-HamdanNeural",
    "ar-AE-FatimaNeural",
]

DEFAULT_ZH_VOICE = "zh-CN-YunjianNeural"

SAMPLES = [
    "اليوم نتعلم هذه الجملة: [zh:今天天气很好]. معناها أن الطقس جميل جدا اليوم.",
    "[zh:马上] تعني فورا أو بعد قليل جدا. لنستمع إليها ببطء مرة أخرى: [zh:马上].",
    "نستخدم التركيب [zh:不但...而且...] لربط فكرتين. معناه: ليس فقط، بل أيضا.",
]

OUTPUT_DIR = CONTENT_BUILDER_DIR / "artifacts" / "test_tts_output" / "azure_ar_zh"


def _ensure_tts_terminal_punctuation(text: str) -> str:
    text = text.strip()
    if text and text[-1] not in ".!?,:;。！？，：；»”」』)]؟،؛":
        return text + "."
    return text


def _azure_call(endpoint: str, api_key: str, voice: str, content: str, output_path: Path) -> None:
    lang_code = "-".join(voice.split("-")[:2]) if "-" in voice else "ar-SA"
    import xml.sax.saxutils as sx

    content = _ensure_tts_terminal_punctuation(content)
    ssml = (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xml:lang="{lang_code}">'
        f'<voice name="{voice}">{sx.escape(content)}</voice>'
        f"</speak>"
    )

    last_error = None
    for attempt in range(1, 5):
        resp = requests.post(
            endpoint,
            headers={
                "Ocp-Apim-Subscription-Key": api_key,
                "Content-Type": "application/ssml+xml",
                "X-Microsoft-OutputFormat": "audio-24khz-96kbitrate-mono-mp3",
            },
            data=ssml.encode("utf-8"),
            timeout=60,
        )
        if resp.ok and len(resp.content) >= 100:
            output_path.write_bytes(resp.content)
            return
        if resp.ok:
            content_type = resp.headers.get("Content-Type", "")
            last_error = f"Azure returned empty/corrupt audio (voice={voice}, bytes={len(resp.content)}, content-type={content_type})"
            if attempt < 4:
                wait = attempt * 8
                print(f"    ⚠️ {last_error}，{wait}s 后重试...")
                time.sleep(wait)
                continue
            raise RuntimeError(f"{last_error}, body={resp.text[:200]!r}")
        last_error = f"Azure TTS error {resp.status_code}: {resp.text[:500]}"
        if resp.status_code in {429, 500, 502, 503, 504} and attempt < 4:
            wait = attempt * 8
            print(f"    ⚠️ {last_error[:120]}，{wait}s 后重试...")
            time.sleep(wait)
            continue
        raise RuntimeError(last_error)

    raise RuntimeError(last_error or "Azure TTS failed after retries")


def _concat_audio(files: list[Path], output_path: Path) -> None:
    concat_list = output_path.with_suffix(".concat.txt")
    try:
        with open(concat_list, "w", encoding="utf-8") as f:
            for item in files:
                f.write(f"file '{str(item).replace(chr(92), '/')}'\n")
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-c:a",
                "libmp3lame",
                "-q:a",
                "4",
                str(output_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    finally:
        try:
            concat_list.unlink()
        except Exception:
            pass


def synthesize_combo(endpoint: str, api_key: str, ar_voice: str, zh_voice: str, index: int) -> Path:
    safe_ar = ar_voice.replace("-", "_")
    safe_zh = zh_voice.replace("-", "_")
    output_file = OUTPUT_DIR / f"{index:02d}_{safe_ar}__{safe_zh}.mp3"
    tmp_dir = OUTPUT_DIR / f"_tmp_{index:02d}"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    segment_files: list[Path] = []
    try:
        chunk_index = 0
        for sample_index, sample in enumerate(SAMPLES, start=1):
            chunks = re.split(r"(\[zh:[^\]]+\])", sample)
            for chunk in chunks:
                if not chunk.strip():
                    continue
                match = re.match(r"\[zh:([^\]]+)\]", chunk)
                if match:
                    voice = zh_voice
                    content = match.group(1).strip()
                else:
                    voice = ar_voice
                    content = chunk.strip()
                    if not content or not any(c.isalpha() or "一" <= c <= "鿿" for c in content):
                        continue
                chunk_index += 1
                chunk_file = tmp_dir / f"chunk_{chunk_index:03d}.mp3"
                try:
                    _azure_call(endpoint, api_key, voice, content, chunk_file)
                except Exception as exc:
                    raise RuntimeError(f"chunk failed voice={voice}, text={content!r}: {exc}") from exc
                segment_files.append(chunk_file)
                time.sleep(0.75)

            pause_file = tmp_dir / f"pause_{sample_index:03d}.mp3"
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "anullsrc=r=24000:cl=mono",
                    "-t",
                    "0.45",
                    "-q:a",
                    "9",
                    "-acodec",
                    "libmp3lame",
                    str(pause_file),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            segment_files.append(pause_file)

        _concat_audio(segment_files, output_file)
        return output_file
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Azure Arabic+Chinese mixed TTS voice samples.")
    parser.add_argument("--ar-voices", help="Comma-separated Azure Arabic voices.")
    parser.add_argument("--zh-voice", default=DEFAULT_ZH_VOICE, help="Azure Chinese voice.")
    parser.add_argument("--limit", type=int, help="Only render the first N voices.")
    parser.add_argument("--delay", type=float, default=4.0, help="Seconds to wait between voice combinations.")
    args = parser.parse_args()

    api_key = get_env("TTS_AZURE_KEY")
    region = get_env("TTS_AZURE_REGION", default="eastus")
    if not api_key:
        raise SystemExit("TTS_AZURE_KEY 未配置，请检查 backend/.env")

    ar_voices = [item.strip() for item in (args.ar_voices.split(",") if args.ar_voices else DEFAULT_AR_VOICES) if item.strip()]
    if args.limit:
        ar_voices = ar_voices[: args.limit]
    endpoint = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"输出目录: {OUTPUT_DIR}")
    print(f"阿拉伯语 voices: {', '.join(ar_voices)}")
    print(f"中文 voice: {args.zh_voice}")

    successes: list[tuple[int, str, Path]] = []
    failures: list[tuple[int, str, str]] = []

    for index, ar_voice in enumerate(ar_voices, start=1):
        print(f"\n[{index:02d}] AR={ar_voice} | ZH={args.zh_voice}")
        try:
            output = synthesize_combo(endpoint, api_key, ar_voice, args.zh_voice, index)
            print(f"  ✅ {output.name} ({output.stat().st_size / 1024:.1f} KB)")
            successes.append((index, ar_voice, output))
        except Exception as exc:
            print(f"  ❌ {exc}")
            failures.append((index, ar_voice, str(exc)))
        if index < len(ar_voices) and args.delay > 0:
            print(f"  ⏸️ 等待 {args.delay:g}s，避免 Azure 限流...")
            time.sleep(args.delay)

    print("\n试听清单:")
    for index, ar_voice, output in successes:
        print(f"  {index:02d}. {output.name}  |  AR={ar_voice}  ZH={args.zh_voice}")

    if failures:
        print("\n失败组合:")
        for index, ar_voice, reason in failures:
            print(f"  {index:02d}. AR={ar_voice}: {reason[:160]}")


if __name__ == "__main__":
    main()
