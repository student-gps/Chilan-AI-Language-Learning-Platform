#!/usr/bin/env python3
"""
Backfill localized historical vocabulary usage fields in lesson JSON files.

This script only updates:
  course_content.vocabulary[].historical_usages[].definition
  course_content.vocabulary[].historical_usages[].part_of_speech
  course_content.vocabulary[].historical_usages[].example.translation

It does not touch narration, video render plans, audio paths, or video paths.

Usage:
  python scripts/backfill_localized_historical_usages.py --lang fr --dry-run
  python scripts/backfill_localized_historical_usages.py --lang fr
  python scripts/backfill_localized_historical_usages.py --lang fr --include-synced
"""

import argparse
import json
import sys
from pathlib import Path


CONTENT_BUILDER_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = CONTENT_BUILDER_DIR.parent
sys.path.insert(0, str(CONTENT_BUILDER_DIR))
sys.path.insert(0, str(BACKEND_DIR))

from core.paths import default_paths
from core.pipeline import get_pipeline


def _load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _sense_lookup(localized_memory: dict) -> dict[tuple[str, str], dict]:
    lookup = {}
    for word, senses in localized_memory.items():
        if not isinstance(senses, list):
            continue
        for sense in senses:
            if not isinstance(sense, dict):
                continue
            source_definition = (sense.get("source_definition") or "").strip()
            if source_definition:
                lookup[(word, source_definition.lower())] = sense
    return lookup


def _backfill_file(json_path: Path, lookup: dict[tuple[str, str], dict], write: bool = True) -> tuple[int, int]:
    data = _load_json(json_path)
    changed = 0
    missing = 0
    vocabulary = (data.get("course_content") or {}).get("vocabulary") or []

    for vocab in vocabulary:
        if not isinstance(vocab, dict):
            continue
        word = (vocab.get("word") or "").strip()
        if not word:
            continue

        for usage in vocab.get("historical_usages") or []:
            if not isinstance(usage, dict):
                continue
            source_definition = (
                usage.get("source_definition")
                or usage.get("definition")
                or ""
            ).strip()
            if not source_definition:
                continue

            localized = lookup.get((word, source_definition.lower()))
            if not localized:
                missing += 1
                continue

            localized_definition = localized.get("definition")
            localized_pos = localized.get("part_of_speech")
            localized_example_translation = (
                (localized.get("example") or {}).get("translation")
                if isinstance(localized.get("example"), dict)
                else None
            )

            before = json.dumps(usage, ensure_ascii=False, sort_keys=True)
            usage["source_definition"] = localized.get("source_definition", source_definition)
            usage["source_part_of_speech"] = localized.get(
                "source_part_of_speech",
                usage.get("source_part_of_speech") or usage.get("part_of_speech") or "",
            )
            if localized_definition:
                usage["definition"] = localized_definition
            if localized_pos:
                usage["part_of_speech"] = localized_pos
            if localized_example_translation:
                usage.setdefault("example", {})["translation"] = localized_example_translation
            after = json.dumps(usage, ensure_ascii=False, sort_keys=True)
            if after != before:
                changed += 1

    if changed and write:
        _write_json(json_path, data)
    return changed, missing


def _target_files(pipeline, paths, lang: str, include_synced: bool) -> list[Path]:
    dirs = [pipeline.output_json_dir(paths, lang)]
    if include_synced:
        dirs.append(pipeline.synced_json_dir(paths, lang))
    files: list[Path] = []
    for directory in dirs:
        if directory.exists():
            files.extend(sorted(directory.glob(f"lesson*_data_{lang}.json")))
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill localized historical vocabulary usages.")
    parser.add_argument("--lang", required=True, help="Target language code, e.g. fr, de, ja, ko, vi, ar.")
    parser.add_argument("--pipeline", default="integrated_chinese", help="Content pipeline ID.")
    parser.add_argument("--include-synced", action="store_true", help="Also update synced_json/<lang>.")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing files.")
    args = parser.parse_args()

    paths = default_paths()
    pipeline = get_pipeline(args.pipeline)
    vocab_memory = (
        pipeline.artifact_root(paths)
        / "vocab_memory"
        / f"global_vocab_memory_{args.lang}.json"
    )
    if not vocab_memory.exists():
        print(f"❌ Missing localized vocab memory: {vocab_memory}")
        print(f"   Run: python localize_vocab_memory.py --lang {args.lang}")
        sys.exit(1)

    lookup = _sense_lookup(_load_json(vocab_memory))
    if not lookup:
        print(f"❌ No source_definition entries found in {vocab_memory.name}.")
        sys.exit(1)

    files = _target_files(pipeline, paths, args.lang, args.include_synced)
    if not files:
        print(f"📭 No localized lesson JSON files found for lang={args.lang}.")
        return

    changed_files = 0
    changed_entries = 0
    missing_entries = 0
    for json_path in files:
        changed, missing = _backfill_file(json_path, lookup, write=not args.dry_run)

        missing_entries += missing
        changed_entries += changed
        if changed:
            changed_files += 1
            print(f"  ✅ {json_path.name}: updated {changed} historical usage(s)")

    mode = "dry-run" if args.dry_run else "written"
    print(
        f"\n✨ Done ({mode}): files={len(files)}, changed_files={changed_files}, "
        f"changed_entries={changed_entries}, missing_matches={missing_entries}"
    )


if __name__ == "__main__":
    main()
