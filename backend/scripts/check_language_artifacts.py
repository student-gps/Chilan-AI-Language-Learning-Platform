"""
Check localized lesson JSONs for reusable narration and slide artifacts.

This is a read-only diagnostic for interrupted Stage 2 runs.
"""

import argparse
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR / "content_builder"))

from core.paths import default_paths
from core.pipeline import get_pipeline


def _lesson_id(path: Path) -> int:
    digits = "".join(ch for ch in path.stem if ch.isdigit())
    return int(digits) if digits else 0


def _resolve_path(value: str, artifact_root: Path) -> Path:
    path = Path(value or "")
    if path.exists():
        return path

    parts = path.parts
    try:
        index = next(i for i, part in enumerate(parts) if part.lower() == "artifacts")
    except StopIteration:
        return path

    tail = Path(*parts[index + 1 :])
    candidates = [artifact_root / tail]
    if tail.parts and tail.parts[0] in {"integrated_chinese", "new_concept_english"}:
        candidates.append(artifact_root / Path(*tail.parts[1:]))

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return path


def _deck_from(data: dict) -> dict:
    if isinstance(data.get("teaching_slide_deck"), dict):
        return data["teaching_slide_deck"]
    plan = data.get("video_render_plan")
    if isinstance(plan, dict) and isinstance(plan.get("teaching_slide_deck"), dict):
        return plan["teaching_slide_deck"]
    explanation = plan.get("explanation") if isinstance(plan, dict) else None
    if isinstance(explanation, dict) and isinstance(explanation.get("teaching_slide_deck"), dict):
        return explanation["teaching_slide_deck"]
    return {}


def _iter_json_files(pipeline_id: str, lang: str) -> tuple[Path, list[Path]]:
    paths = default_paths()
    pipeline = get_pipeline(pipeline_id)
    artifact_root = pipeline.artifact_root(paths)
    out_dir = pipeline.output_json_dir(paths, lang)
    synced_dir = pipeline.synced_json_dir(paths, lang)
    by_name = {path.name: path for path in synced_dir.glob(f"lesson*_data_{lang}.json")}
    by_name.update({path.name: path for path in out_dir.glob(f"lesson*_data_{lang}.json")})
    return artifact_root, sorted(by_name.values(), key=_lesson_id)


def check_file(path: Path, artifact_root: Path, lang: str) -> list[str]:
    issues: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"cannot read JSON: {exc}"]

    deck = _deck_from(data)
    if not deck:
        issues.append("slide deck missing")
        return issues
    if deck.get("lang") != lang:
        issues.append(f"slide deck lang is {deck.get('lang')!r}")

    slides = deck.get("slides")
    if not isinstance(slides, list) or not slides:
        issues.append("slide deck has no slides")
        return issues
    if deck.get("slide_count") != len(slides):
        issues.append(f"slide_count {deck.get('slide_count')} != slides length {len(slides)}")

    missing_images = 0
    missing_audio = 0
    for slide in slides:
        if not isinstance(slide, dict):
            continue
        image = slide.get("image") if isinstance(slide.get("image"), dict) else {}
        audio = slide.get("audio") if isinstance(slide.get("audio"), dict) else {}
        if image and not _resolve_path(image.get("local_path", ""), artifact_root).exists():
            missing_images += 1
        if audio and not _resolve_path(audio.get("local_path", ""), artifact_root).exists():
            missing_audio += 1
    if missing_images:
        issues.append(f"{missing_images} slide image files missing")
    if missing_audio:
        issues.append(f"{missing_audio} slide audio files missing")

    return issues


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pipeline", default="integrated_chinese")
    parser.add_argument("--langs", nargs="+", required=True)
    args = parser.parse_args()

    total_files = 0
    total_bad = 0
    for lang in args.langs:
        artifact_root, files = _iter_json_files(args.pipeline, lang)
        bad: list[tuple[str, list[str]]] = []
        for path in files:
            issues = check_file(path, artifact_root, lang)
            if issues:
                bad.append((path.name, issues))
        total_files += len(files)
        total_bad += len(bad)
        print(f"\n[{lang}] files={len(files)} ok={len(files) - len(bad)} bad={len(bad)}")
        for name, issues in bad[:30]:
            print(f"  - {name}: {'; '.join(issues)}")
        if len(bad) > 30:
            print(f"  ... {len(bad) - 30} more")

    print(f"\nTOTAL files={total_files} bad={total_bad}")
    raise SystemExit(1 if total_bad else 0)


if __name__ == "__main__":
    main()
