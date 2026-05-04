import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


CONTENT_BUILDER_DIR = Path(__file__).resolve().parents[1]
if str(CONTENT_BUILDER_DIR) not in sys.path:
    sys.path.insert(0, str(CONTENT_BUILDER_DIR))

from core.paths import default_paths
from core.pipeline import get_pipeline


ZH_MARKER_RE = re.compile(r"\[zh:[^\]]*\]")


def markers(value: Any) -> list[str]:
    return ZH_MARKER_RE.findall(value) if isinstance(value, str) else []


SKIP_PATH_PARTS = {"teaching_slide_deck", "caption_cues", "sentence_texts"}


def iter_strings(value: Any, path: str = ""):
    if any(part in SKIP_PATH_PARTS for part in path.split(".")):
        return
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from iter_strings(item, f"{path}.{index}" if path else str(index))
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from iter_strings(item, f"{path}.{key}" if path else str(key))


def get_path(value: Any, path: str):
    current = value
    for part in path.split("."):
        if isinstance(current, list):
            index = int(part)
            if index >= len(current):
                return None
            current = current[index]
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def localized_filename(lesson_id: str, lang: str) -> str:
    return f"lesson{lesson_id}_data.json" if lang == "en" else f"lesson{lesson_id}_data_{lang}.json"


def lesson_digits(path: Path) -> str:
    match = re.search(r"lesson(\d+)", path.stem)
    if not match:
        raise ValueError(f"Cannot parse lesson id from {path.name}")
    return str(int(match.group(1)))


def check_language(source_dir: Path, target_dir: Path, lang: str) -> int:
    problems = 0
    for source_path in sorted(source_dir.glob("*_data*.json")):
        lesson_id = lesson_digits(source_path)
        target_path = target_dir / localized_filename(lesson_id, lang)
        if not target_path.exists():
            print(f"{lang}: missing {target_path.name}")
            problems += 1
            continue

        source = json.loads(source_path.read_text(encoding="utf-8"))
        target = json.loads(target_path.read_text(encoding="utf-8"))
        for path, source_value in iter_strings(source):
            expected = markers(source_value)
            if not expected:
                continue
            actual = markers(get_path(target, path))
            if expected != actual:
                print(f"{lang}/{target_path.name}: {path}")
                print(f"  expected: {expected}")
                print(f"  actual:   {actual}")
                problems += 1
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Check that localized JSON preserves [zh:...] markers exactly.")
    parser.add_argument("--pipeline", default="integrated_chinese")
    parser.add_argument("--langs", nargs="+", default=["fr", "de", "ja", "vi", "ko", "ar"])
    args = parser.parse_args()

    paths = default_paths()
    pipeline = get_pipeline(args.pipeline)
    artifact_root = pipeline.artifact_root(paths)
    source_dir = artifact_root / "output_json" / "en"

    total = 0
    for lang in args.langs:
        target_dir = artifact_root / "output_json" / lang
        if not target_dir.exists():
            print(f"{lang}: missing directory {target_dir}")
            total += 1
            continue
        count = check_language(source_dir, target_dir, lang)
        print(f"{lang}: {count} marker mismatch(es)")
        total += count
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
