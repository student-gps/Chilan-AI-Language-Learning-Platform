"""
test_azure_it_zh_voices.py — Azure 中意混合旁白声色试听

运行方式：
    cd backend/content_builder
    python scripts/test_azure_it_zh_voices.py

输出目录：
    artifacts/test_tts_output/azure_it_zh/
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

DEFAULT_IT_VOICES = [
    "it-IT-DiegoNeural",     # 男声
    "it-IT-ElsaNeural",      # 女声
    "it-IT-IsabellaNeural",  # 女声（更柔和）
]

DEFAULT_ZH_VOICE = "zh-CN-YunjianNeural"

SAMPLES = [
    "Oggi impariamo [zh:你好], che in cinese significa ciao.",
    "[zh:马上] significa subito o tra poco. Ascoltiamo ancora una volta: [zh:马上].",
    "La struttura [zh:不但...而且...] collega due frasi. In italiano significa non solo, ma anche.",
]

OUTPUT_DIR = CONTENT_BUILDER_DIR / "artifacts" / "test_tts_output" / "azure_it_zh"


def _ensure_tts_terminal_punctuation(text: str) -> str:
    text = text.strip()
    if text and text[-1] not in '.!?,:;。！？，：；»""」』)]':
        return text + "."
    return text


def _azure_call(endpoint: str, api_key: str, voice: str, content: str, output_path: Path) -> None:
    lang_code = "-".join(voice.split("-")[:2]) if "-" in voice else "it-IT"
    import xml.sax.saxutils as sx

    content = _ensure_tts_terminal_punctuation(content)
    ssml = (
        f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xml:lang="{lang_code}">'
        f'<voice name="{voice}">{sx.escape(content)}</voice>'
        f"</speak>"
    )

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
        reason = f"Azure TTS error {resp.status_code}: {resp.text[:500]}" if not resp.ok else f"empty audio (bytes={len(resp.content)})"
        if resp.status_code in {429, 500, 502, 503, 504} or resp.ok:
            if attempt < 4:
                wait = attempt * 8
                print(f"    ⚠️ {reason[:140]}，{wait}s 后重试...")
                time.sleep(wait)
                continue
        raise RuntimeError(reason)

    raise RuntimeError("Azure TTS failed after retries")


def _concat_audio(files: list[Path], output_path: Path) -> None:
    concat_list = output_path.with_suffix(".concat.txt")
    try:
        with open(concat_list, "w", encoding="utf-8") as f:
            for item in files:
                f.write(f"file '{str(item).replace(chr(92), '/')}'\n")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c:a", "libmp3lame", "-q:a", "4", str(output_path)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    finally:
        try:
            concat_list.unlink()
        except Exception:
            pass


def synthesize_combo(endpoint: str, api_key: str, it_voice: str, zh_voice: str, index: int) -> Path:
    output_file = OUTPUT_DIR / f"{index:02d}_{it_voice.replace('-', '_')}__{zh_voice.replace('-', '_')}.mp3"
    tmp_dir = OUTPUT_DIR / f"_tmp_{index:02d}"
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    segment_files: list[Path] = []
    try:
        chunk_index = 0
        for sample_index, sample in enumerate(SAMPLES, start=1):
            for chunk in re.split(r"(\[zh:[^\]]+\])", sample):
                if not chunk.strip():
                    continue
                match = re.match(r"\[zh:([^\]]+)\]", chunk)
                if match:
                    voice, content = zh_voice, match.group(1).strip()
                else:
                    voice, content = it_voice, chunk.strip()
                    if not content or not any(c.isalpha() or "一" <= c <= "鿿" for c in content):
                        continue
                chunk_index += 1
                chunk_file = tmp_dir / f"chunk_{chunk_index:03d}.mp3"
                _azure_call(endpoint, api_key, voice, content, chunk_file)
                segment_files.append(chunk_file)
                time.sleep(0.75)

            pause_file = tmp_dir / f"pause_{sample_index:03d}.mp3"
            subprocess.run(
                ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "0.45", "-q:a", "9", "-acodec", "libmp3lame", str(pause_file)],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            segment_files.append(pause_file)

        _concat_audio(segment_files, output_file)
        return output_file
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Azure Italian+Chinese mixed TTS voice samples.")
    parser.add_argument("--it-voices", help="Comma-separated Azure Italian voices.")
    parser.add_argument("--zh-voice", default=DEFAULT_ZH_VOICE)
    parser.add_argument("--delay", type=float, default=4.0)
    args = parser.parse_args()

    api_key = get_env("TTS_AZURE_KEY")
    region = get_env("TTS_AZURE_REGION", default="eastus")
    if not api_key:
        raise SystemExit("TTS_AZURE_KEY 未配置，请检查 backend/.env")

    it_voices = [v.strip() for v in (args.it_voices.split(",") if args.it_voices else DEFAULT_IT_VOICES) if v.strip()]
    endpoint = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"输出目录: {OUTPUT_DIR}")
    print(f"意大利语 voices: {', '.join(it_voices)}")
    print(f"中文 voice: {args.zh_voice}")

    successes, failures = [], []
    for index, it_voice in enumerate(it_voices, start=1):
        print(f"\n[{index:02d}] IT={it_voice} | ZH={args.zh_voice}")
        try:
            output = synthesize_combo(endpoint, api_key, it_voice, args.zh_voice, index)
            print(f"  ✅ {output.name} ({output.stat().st_size / 1024:.1f} KB)")
            successes.append((index, it_voice, output))
        except Exception as exc:
            print(f"  ❌ {exc}")
            failures.append((index, it_voice, str(exc)))
        if index < len(it_voices) and args.delay > 0:
            time.sleep(args.delay)

    print("\n试听清单:")
    for index, it_voice, output in successes:
        print(f"  {index:02d}. {output.name}  |  IT={it_voice}")
    if failures:
        print("\n失败:")
        for index, it_voice, reason in failures:
            print(f"  {index:02d}. IT={it_voice}: {reason[:160]}")


if __name__ == "__main__":
    main()
