"""Generate and upload static audio for the Japanese foundation experience.

The frontend inventory is the source of truth. Course-intro narration uses the
configured Azure voices for the learner language; Japanese examples use the
same Azure Neural renderer as Minna no Nihongo lesson audio.

Examples:
    python generate_japanese_foundation_audio.py
    python generate_japanese_foundation_audio.py --generate-only
    python generate_japanese_foundation_audio.py --upload-only
    python generate_japanese_foundation_audio.py --overwrite
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parent
FRONTEND_DIR = REPO_ROOT / "frontend"
OUTPUT_DIR = FRONTEND_DIR / "public" / "audio" / "japanese-foundations"
INVENTORY_SCRIPT = FRONTEND_DIR / "scripts" / "list-japanese-static-audio.mjs"
R2_PREFIX = "ja/audio/foundations"

sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")

from config.env import get_env  # noqa: E402
from content_builder.ja.minna_no_nihongo.tasks.lesson_audio import (  # noqa: E402
    MinnaNoNihongoLessonAudioRenderer,
)
from content_builder.zh.integrated_chinese.tasks.narration_audio import (  # noqa: E402
    Task4DExplanationNarrator,
)
from services.storage.r2_storage import R2Storage  # noqa: E402


def load_inventory() -> list[dict]:
    result = subprocess.run(
        ["node", str(INVENTORY_SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    inventory = json.loads(result.stdout)
    filenames = [item["filename"] for item in inventory]
    if len(filenames) != len(set(filenames)):
        raise ValueError("Japanese static-audio inventory contains duplicate filenames")
    return inventory


def is_valid_audio(path: Path) -> bool:
    return path.is_file() and path.stat().st_size >= 512


def build_intro_narrator(language: str) -> Task4DExplanationNarrator:
    os.environ.setdefault(f"TTS_EXPLANATION_PROVIDER_{language.upper()}", "azure")
    narrator = Task4DExplanationNarrator()
    narrator._configure_for_lang(language)
    narrator._lang = language
    if narrator.provider != "azure":
        raise ValueError(
            f"Static course-intro narration requires Azure; {language} resolved to {narrator.provider}"
        )
    return narrator


def generate_intro_items(items: list[dict], overwrite: bool, max_retries: int) -> tuple[int, int]:
    generated = skipped = 0
    narrators = {language: build_intro_narrator(language) for language in {item["language"] for item in items}}
    os.environ["TTS_EXPLANATION_SINGLE_VOICE"] = "1"
    for index, item in enumerate(items, start=1):
        output_path = OUTPUT_DIR / item["filename"]
        if is_valid_audio(output_path) and not overwrite:
            skipped += 1
            print(f"  [intro {index}/{len(items)}] SKIP {item['filename']}", flush=True)
            continue
        narrator = narrators[item["language"]]
        print(
            f"  [intro {index}/{len(items)}] {item['language']} | {narrator.voice} | {item['filename']}",
            flush=True,
        )
        narrator._synthesize(item["text"], output_path, max_retries=max_retries)
        if not is_valid_audio(output_path):
            raise RuntimeError(f"Invalid generated audio: {output_path}")
        generated += 1
    return generated, skipped


def generate_foundation_items(items: list[dict], overwrite: bool, workers: int) -> tuple[int, int]:
    voice = get_env("TTS_JAPANESE_FOUNDATION_VOICE", default="ja-JP-NanamiNeural")
    rate = get_env("TTS_JAPANESE_FOUNDATION_RATE", default="-10%")
    renderer = MinnaNoNihongoLessonAudioRenderer(default_voice=voice, rate=rate)
    pending = []
    skipped = 0
    for item in items:
        output_path = OUTPUT_DIR / item["filename"]
        if is_valid_audio(output_path) and not overwrite:
            skipped += 1
        else:
            pending.append(item)

    print(
        f"Japanese foundation voice={voice} rate={rate}; "
        f"generate={len(pending)} skip={skipped} workers={workers}",
        flush=True,
    )

    def render(item: dict) -> tuple[str, int]:
        output_path = OUTPUT_DIR / item["filename"]
        renderer._synthesize_azure(item["text"], output_path, voice)
        if not is_valid_audio(output_path):
            raise RuntimeError(f"Invalid generated audio: {output_path}")
        return item["filename"], output_path.stat().st_size

    completed = 0
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = {executor.submit(render, item): item for item in pending}
        for future in as_completed(futures):
            item = futures[future]
            filename, size = future.result()
            completed += 1
            print(
                f"  [foundation {completed}/{len(pending)}] {filename} "
                f"({size // 1024} KB) | {item['text']}",
                flush=True,
            )
    return completed, skipped


def upload_items(items: list[dict], workers: int) -> tuple[int, int]:
    storage = R2Storage.from_env()

    def upload(item: dict) -> tuple[str, int]:
        local_path = OUTPUT_DIR / item["filename"]
        if not is_valid_audio(local_path):
            raise FileNotFoundError(f"Missing generated audio: {local_path}")
        object_key = f"{R2_PREFIX}/{item['filename']}"
        storage.upload_file(local_path, object_key, content_type="audio/mpeg")
        metadata = storage.get_object_metadata(object_key)
        expected_size = local_path.stat().st_size
        if metadata["content_length"] != expected_size:
            raise RuntimeError(
                f"R2 size mismatch for {object_key}: {metadata['content_length']} != {expected_size}"
            )
        if metadata["content_type"] != "audio/mpeg":
            raise RuntimeError(f"Unexpected R2 content type for {object_key}: {metadata['content_type']}")
        return object_key, expected_size

    completed = 0
    total_bytes = 0
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = {executor.submit(upload, item): item for item in items}
        for future in as_completed(futures):
            object_key, size = future.result()
            completed += 1
            total_bytes += size
            print(f"  [upload {completed}/{len(items)}] {object_key}", flush=True)
    return completed, total_bytes


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate static Japanese foundation audio and upload it to R2")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--generate-only", action="store_true")
    mode.add_argument("--upload-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--upload-workers", type=int, default=8)
    parser.add_argument("--max-retries", type=int, default=3)
    args = parser.parse_args()

    inventory = load_inventory()
    intro_items = [item for item in inventory if item["kind"] == "course_intro"]
    foundation_items = [item for item in inventory if item["kind"] == "foundation"]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Inventory: {len(intro_items)} course-intro + {len(foundation_items)} foundation "
        f"= {len(inventory)} files",
        flush=True,
    )

    started = time.monotonic()
    if not args.upload_only:
        intro_generated, intro_skipped = generate_intro_items(
            intro_items,
            overwrite=args.overwrite,
            max_retries=args.max_retries,
        )
        foundation_generated, foundation_skipped = generate_foundation_items(
            foundation_items,
            overwrite=args.overwrite,
            workers=args.workers,
        )
        print(
            f"Generated: intro={intro_generated} foundation={foundation_generated}; "
            f"skipped={intro_skipped + foundation_skipped}",
            flush=True,
        )

    if not args.generate_only:
        uploaded, total_bytes = upload_items(inventory, workers=args.upload_workers)
        print(f"Uploaded and HEAD-verified: {uploaded} files, {total_bytes / 1024 / 1024:.2f} MB", flush=True)

    print(f"Done in {time.monotonic() - started:.1f}s", flush=True)


if __name__ == "__main__":
    main()
