"""Compress slide-deck MP3 audio in place.

Default mode is a dry run. With --apply, each referenced slide audio file is
transcoded to a temporary file, then atomically replaces the original path so
JSON and DB object_key/local_path values do not need to change.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from content_builder.core.paths import default_paths
from content_builder.core.pipeline import get_pipeline


def human_size(value: int) -> str:
    size = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.2f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.2f} TB"


def lesson_id(path: Path) -> int:
    digits = "".join(ch for ch in path.stem if ch.isdigit())
    return int(digits) if digits else 0


def resolve_path(value: str, artifact_root: Path) -> Path:
    raw = Path(value or "")
    if raw.exists():
        return raw
    parts = raw.parts
    try:
        index = next(i for i, part in enumerate(parts) if part.lower() == "artifacts")
    except StopIteration:
        return raw
    tail = Path(*parts[index + 1 :])
    candidates = [artifact_root / tail]
    if tail.parts and tail.parts[0] in {"integrated_chinese", "new_concept_english"}:
        candidates.append(artifact_root / Path(*tail.parts[1:]))
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return raw


def deck_from(data: dict) -> dict:
    if isinstance(data.get("teaching_slide_deck"), dict):
        return data["teaching_slide_deck"]
    plan = data.get("video_render_plan")
    if isinstance(plan, dict) and isinstance(plan.get("teaching_slide_deck"), dict):
        return plan["teaching_slide_deck"]
    explanation = plan.get("explanation") if isinstance(plan, dict) else None
    if isinstance(explanation, dict) and isinstance(explanation.get("teaching_slide_deck"), dict):
        return explanation["teaching_slide_deck"]
    return {}


def iter_json_files(pipeline_id: str, lang: str) -> tuple[Path, list[Path]]:
    paths = default_paths()
    pipeline = get_pipeline(pipeline_id)
    artifact_root = pipeline.artifact_root(paths)
    out_dir = pipeline.output_json_dir(paths, lang)
    synced_dir = pipeline.synced_json_dir(paths, lang)
    by_name = {path.name: path for path in synced_dir.glob(f"lesson*_data_{lang}.json")}
    if lang == "en":
        by_name.update({path.name: path for path in synced_dir.glob("lesson*_data.json")})
        by_name.update({path.name: path for path in out_dir.glob("lesson*_data.json")})
    by_name.update({path.name: path for path in out_dir.glob(f"lesson*_data_{lang}.json")})
    return artifact_root, sorted(by_name.values(), key=lesson_id)


def collect_audio_files(pipeline_id: str, langs: list[str]) -> list[Path]:
    files: dict[Path, None] = {}
    for lang in langs:
        artifact_root, json_files = iter_json_files(pipeline_id, lang)
        for json_path in json_files:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            deck = deck_from(data)
            for slide in deck.get("slides") or []:
                if not isinstance(slide, dict):
                    continue
                audio = slide.get("audio") if isinstance(slide.get("audio"), dict) else {}
                local_path = audio.get("local_path")
                if local_path:
                    path = resolve_path(local_path, artifact_root)
                    if path.suffix.lower() == ".mp3" and path.exists():
                        files[path.resolve()] = None
    return sorted(files.keys())


def parse_bitrate(value: str) -> int:
    raw = value.strip().lower()
    if raw.endswith("k"):
        return int(float(raw[:-1]) * 1000)
    return int(raw)


def probe_audio(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=bit_rate,channels,sample_rate",
            "-of",
            "json",
            str(path),
        ],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        return {}
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}
    streams = data.get("streams") or []
    return streams[0] if streams else {}


def is_target_format(path: Path, bitrate: str, sample_rate: int) -> bool:
    stream = probe_audio(path)
    if not stream:
        return False
    channels = int(stream.get("channels") or 0)
    actual_sample_rate = int(stream.get("sample_rate") or 0)
    actual_bitrate = int(stream.get("bit_rate") or 0)
    target_bitrate = parse_bitrate(bitrate)
    # MP3 headers can vary a little; allow 2 kbps tolerance.
    return (
        channels == 1
        and actual_sample_rate == sample_rate
        and abs(actual_bitrate - target_bitrate) <= 2000
    )


def compress_file(path: Path, bitrate: str, sample_rate: int) -> tuple[int, int]:
    before = path.stat().st_size
    tmp = path.with_name(f"{path.stem}.tmp{path.suffix}")
    if tmp.exists():
        tmp.unlink()
    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(path),
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-b:a",
        bitrate,
        "-f",
        "mp3",
        str(tmp),
    ]
    result = subprocess.run(command)
    if result.returncode != 0:
        if tmp.exists():
            tmp.unlink()
        raise RuntimeError(f"ffmpeg failed for {path}")
    if tmp.stat().st_size <= 0:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"empty output for {path}")
    tmp.replace(path)
    after = path.stat().st_size
    return before, after


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pipeline", default="integrated_chinese")
    parser.add_argument("--langs", nargs="+", required=True)
    parser.add_argument("--bitrate", default="40k")
    parser.add_argument("--sample-rate", type=int, default=24000)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--skip-existing-target",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Skip files that already match target bitrate/channels/sample-rate.",
    )
    args = parser.parse_args()

    files = collect_audio_files(args.pipeline, args.langs)
    if args.limit:
        files = files[: args.limit]
    current_size = sum(path.stat().st_size for path in files)
    print(f"files={len(files)} current_size={human_size(current_size)}")
    print(f"target=mp3 {args.bitrate} mono {args.sample_rate}Hz")
    if not args.apply:
        print("Dry run only. Add --apply to replace files in place.")
        return

    started = time.monotonic()
    before_total = 0
    after_total = 0
    failed = 0
    for index, path in enumerate(files, start=1):
        try:
            if args.skip_existing_target and is_target_format(path, args.bitrate, args.sample_rate):
                continue
            before, after = compress_file(path, args.bitrate, args.sample_rate)
            before_total += before
            after_total += after
        except Exception as exc:
            print(f"failed: {path} | {exc}")
            failed += 1
        if index % 100 == 0 or index == len(files):
            elapsed = time.monotonic() - started
            rate = index / elapsed if elapsed else 0
            remaining = (len(files) - index) / rate if rate else 0
            print(
                f"{index}/{len(files)} done, saved={human_size(before_total - after_total)}, "
                f"elapsed={elapsed/60:.1f}m, eta={remaining/60:.1f}m"
            )

    print(
        f"complete: files={len(files)} failed={failed} "
        f"before={human_size(before_total)} after={human_size(after_total)} "
        f"saved={human_size(before_total - after_total)}"
    )


if __name__ == "__main__":
    main()

