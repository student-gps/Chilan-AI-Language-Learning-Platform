#!/usr/bin/env python3
"""
migrate_integrated_chinese_practice_types.py

Canonicalize historical Integrated Chinese speaking/listen-write items before
re-syncing them with database/sync_to_db.py.

The migration preserves question IDs, answer text, audio lookup fields, and all
unrelated metadata. It is safe to re-run: an already canonical item is only
changed when required metadata is missing or incorrect.

Examples (run from backend/):
  python database/migrate_integrated_chinese_practice_types.py --all-langs
  python database/migrate_integrated_chinese_practice_types.py --lang en --lesson 101
  python database/migrate_integrated_chinese_practice_types.py --all-langs --apply-json
  python database/migrate_integrated_chinese_practice_types.py --all-langs --apply-json --sync-db

By default the script is dry-run only. `--sync-db` requires `--apply-json`.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shutil
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from dotenv import load_dotenv


CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

load_dotenv(BACKEND_DIR / ".env")

PRIMARY_ARTIFACT_ROOT = (
    BACKEND_DIR / "content_builder" / "zh" / "integrated_chinese" / "artifacts"
)
LEGACY_ARTIFACT_ROOT = BACKEND_DIR / "content_builder" / "artifacts" / "integrated_chinese"
DEFAULT_LANG = "en"
LEGACY_SPEAK_PATTERN = re.compile(r"^(?P<support>[A-Z]+)_TO_CN_SPEAK$")
LEGACY_LISTEN_WRITE_TYPE = "CN_LISTEN_WRITE"


@dataclass
class FileReport:
    path: Path
    lang: str
    legacy_speak: int = 0
    legacy_listen_write: int = 0
    metadata_repaired: int = 0
    unresolved: list[str] = field(default_factory=list)
    changed: bool = False

    @property
    def change_count(self) -> int:
        return self.legacy_speak + self.legacy_listen_write + self.metadata_repaired


@dataclass
class MigrationReport:
    files_scanned: int = 0
    files_changed: int = 0
    legacy_speak: int = 0
    legacy_listen_write: int = 0
    metadata_repaired: int = 0
    unresolved: list[str] = field(default_factory=list)
    per_language: Counter = field(default_factory=Counter)
    changed_files: list[FileReport] = field(default_factory=list)

    def add(self, report: FileReport) -> None:
        self.files_scanned += 1
        self.legacy_speak += report.legacy_speak
        self.legacy_listen_write += report.legacy_listen_write
        self.metadata_repaired += report.metadata_repaired
        self.unresolved.extend(report.unresolved)
        if report.changed:
            self.files_changed += 1
            self.per_language[report.lang] += report.change_count
            self.changed_files.append(report)


class MigrationError(ValueError):
    """Raised when a source item cannot be migrated safely."""


def _normalize_lang(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    aliases = {"cn": "zh", "jp": "ja"}
    return aliases.get(normalized, normalized)


def _lesson_id(path: Path) -> int | None:
    match = re.search(r"lesson(?P<id>\d+)_data", path.name, flags=re.IGNORECASE)
    return int(match.group("id")) if match else None


def _backup_path(path: Path) -> Path:
    return path.with_name(f"{path.stem}.speaking-migration-backup{path.suffix}")


def _is_migration_backup(path: Path) -> bool:
    return path.name.endswith(".speaking-migration-backup.json")


def _artifact_dirs(
    *,
    lang: str,
    include_output_json: bool,
    roots: Iterable[Path] = (PRIMARY_ARTIFACT_ROOT, LEGACY_ARTIFACT_ROOT),
) -> list[Path]:
    directories: list[Path] = []
    for root in roots:
        synced = root / "synced_json" / lang
        if synced.exists():
            directories.append(synced)
        if include_output_json:
            output = root / "output_json" / lang
            if output.exists():
                directories.append(output)
    return directories


def iter_artifacts(
    *,
    langs: Iterable[str],
    lessons: set[int],
    include_output_json: bool,
) -> Iterable[tuple[Path, str]]:
    seen: set[Path] = set()
    for lang in langs:
        for directory in _artifact_dirs(lang=lang, include_output_json=include_output_json):
            for path in sorted(directory.glob("*_data*.json"), key=lambda item: (_lesson_id(item) or 0, item.name)):
                if _is_migration_backup(path):
                    continue
                resolved = path.resolve()
                if resolved in seen:
                    continue
                lesson_id = _lesson_id(path)
                if lessons and lesson_id not in lessons:
                    continue
                seen.add(resolved)
                yield path, lang


def _support_language(data: dict, item_metadata: dict, directory_lang: str) -> str:
    candidates = (
        item_metadata.get("support_language"),
        item_metadata.get("source_language"),
        (data.get("localization") or {}).get("target_lang"),
        directory_lang,
        data.get("support_language"),
        (data.get("lesson_metadata") or {}).get("support_language"),
    )
    for candidate in candidates:
        normalized = _normalize_lang(candidate)
        if normalized:
            return normalized
    return ""


def _merge_required_metadata(metadata: dict, required: dict[str, Any]) -> bool:
    changed = False
    for key, value in required.items():
        if metadata.get(key) != value:
            metadata[key] = value
            changed = True
    return changed


def _canonicalize_item(data: dict, item: dict, directory_lang: str, item_index: int) -> tuple[bool, str | None, str | None]:
    question_type = str(item.get("question_type") or "").strip().upper()
    metadata = item.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
        item["metadata"] = metadata

    support_language = _support_language(data, metadata, directory_lang)
    legacy_speak = LEGACY_SPEAK_PATTERN.match(question_type)
    is_canonical_speak = question_type == "SPEAK"
    is_legacy_listen_write = question_type == LEGACY_LISTEN_WRITE_TYPE
    is_canonical_listen_write = question_type == "LISTEN_WRITE"

    if legacy_speak or is_canonical_speak:
        support_language = support_language or _normalize_lang(legacy_speak.group("support") if legacy_speak else "")
        if not support_language:
            return False, None, f"item[{item_index}] SPEAK has no resolvable support language"

        changed = False
        if question_type != "SPEAK":
            item["question_type"] = "SPEAK"
            changed = True
            legacy_kind = "speak"
        else:
            legacy_kind = None

        required = {
            "answer_mode": "speech",
            "target_language": "zh",
            "support_language": support_language,
            "speech_language": "zh",
            "audio_language": support_language,
        }
        metadata_changed = _merge_required_metadata(metadata, required)
        return changed or metadata_changed, legacy_kind, "metadata" if metadata_changed and not changed else None

    if is_legacy_listen_write or is_canonical_listen_write:
        if not support_language:
            return False, None, f"item[{item_index}] LISTEN_WRITE has no resolvable support language"

        changed = False
        if question_type != "LISTEN_WRITE":
            item["question_type"] = "LISTEN_WRITE"
            changed = True
            legacy_kind = "listen_write"
        else:
            legacy_kind = None

        required = {
            "answer_mode": "text",
            "target_language": "zh",
            "support_language": support_language,
            "audio_language": "zh",
        }
        metadata_changed = _merge_required_metadata(metadata, required)
        return changed or metadata_changed, legacy_kind, "metadata" if metadata_changed and not changed else None

    return False, None, None


def canonicalize_payload(data: dict, directory_lang: str) -> tuple[dict, FileReport]:
    migrated = copy.deepcopy(data)
    report = FileReport(path=Path("<payload>"), lang=directory_lang)
    items = migrated.get("database_items")
    if not isinstance(items, list):
        return migrated, report

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        changed, legacy_kind, issue = _canonicalize_item(migrated, item, directory_lang, index)
        if issue and issue != "metadata":
            report.unresolved.append(issue)
            continue
        if not changed:
            continue
        report.changed = True
        if legacy_kind == "speak":
            report.legacy_speak += 1
        elif legacy_kind == "listen_write":
            report.legacy_listen_write += 1
        else:
            report.metadata_repaired += 1

    return migrated, report


def _validate_payload(original: dict, migrated: dict) -> None:
    original_items = original.get("database_items") if isinstance(original.get("database_items"), list) else []
    migrated_items = migrated.get("database_items") if isinstance(migrated.get("database_items"), list) else []
    if len(original_items) != len(migrated_items):
        raise MigrationError("database_items count changed")

    for index, (before, after) in enumerate(zip(original_items, migrated_items)):
        if not isinstance(before, dict) or not isinstance(after, dict):
            continue
        for key in ("question_id", "original_text", "original_pinyin", "standard_answers"):
            if before.get(key) != after.get(key):
                raise MigrationError(f"item[{index}] unexpectedly changed {key}")

        question_type = after.get("question_type")
        metadata = after.get("metadata") if isinstance(after.get("metadata"), dict) else {}
        if question_type == "SPEAK":
            required = {
                "answer_mode": "speech",
                "target_language": "zh",
                "speech_language": "zh",
            }
        elif question_type == "LISTEN_WRITE":
            required = {
                "answer_mode": "text",
                "target_language": "zh",
                "audio_language": "zh",
            }
        else:
            continue

        missing = [key for key, value in required.items() if metadata.get(key) != value]
        if not metadata.get("support_language"):
            missing.append("support_language")
        if missing:
            raise MigrationError(f"item[{index}] {question_type} metadata invalid: {', '.join(missing)}")


def migrate_file(path: Path, lang: str, apply_json: bool, overwrite_backup: bool) -> FileReport:
    with open(path, encoding="utf-8") as handle:
        original = json.load(handle)

    migrated, report = canonicalize_payload(original, lang)
    report.path = path
    if report.unresolved:
        return report
    if not report.changed:
        return report

    _validate_payload(original, migrated)
    if not apply_json:
        return report

    backup = _backup_path(path)
    if backup.exists() and not overwrite_backup:
        raise MigrationError(
            f"Backup already exists for {path.name}: {backup.name}. "
            "Pass --overwrite-backup only after reviewing it."
        )

    if not backup.exists() or overwrite_backup:
        shutil.copy2(path, backup)

    temp_path = path.with_name(f"{path.name}.tmp")
    try:
        with open(temp_path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(migrated, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        with open(temp_path, encoding="utf-8") as handle:
            written = json.load(handle)
        _validate_payload(original, written)
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    return report


def _ensure_utf8_console() -> None:
    if os.name != "nt":
        return
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


def sync_changed_files(changed_files: Iterable[FileReport]) -> list[str]:
    _ensure_utf8_console()
    from database.sync_to_db import EmbeddingFactory, sync_lesson_data

    provider = EmbeddingFactory.create_provider()
    failures: list[str] = []
    for report in changed_files:
        try:
            synced = sync_lesson_data(
                str(report.path),
                provider,
                sync_context={"pipeline": "integrated_chinese", "lang": report.lang},
            )
        except Exception as exc:  # sync_lesson_data normally handles exceptions, keep the batch report robust.
            failures.append(f"{report.path}: {exc}")
            continue
        if not synced:
            failures.append(f"{report.path}: sync_to_db returned false")
    return failures


def _available_languages(include_output_json: bool) -> list[str]:
    languages: set[str] = set()
    for root in (PRIMARY_ARTIFACT_ROOT, LEGACY_ARTIFACT_ROOT):
        for parent_name in ("synced_json", "output_json"):
            if parent_name == "output_json" and not include_output_json:
                continue
            parent = root / parent_name
            if not parent.exists():
                continue
            languages.update(path.name.lower() for path in parent.iterdir() if path.is_dir())
    return sorted(languages)


def _print_report(report: MigrationReport, dry_run: bool) -> None:
    mode = "DRY-RUN" if dry_run else "APPLIED"
    print(f"\n=== {mode}: Integrated Chinese practice-type migration ===")
    print(
        "files_scanned={files} files_changed={changed} legacy_speak={speak} "
        "legacy_listen_write={listen} metadata_repaired={metadata}".format(
            files=report.files_scanned,
            changed=report.files_changed,
            speak=report.legacy_speak,
            listen=report.legacy_listen_write,
            metadata=report.metadata_repaired,
        )
    )
    for lang, changes in sorted(report.per_language.items()):
        print(f"  {lang}: {changes} item changes")
    for item in report.changed_files:
        print(
            f"  {'[DRY] ' if dry_run else ''}{item.path}: "
            f"speak={item.legacy_speak}, listen_write={item.legacy_listen_write}, "
            f"metadata={item.metadata_repaired}"
        )
    if report.unresolved:
        print("\nUnresolved items (no files were written for these cases):")
        for issue in report.unresolved:
            print(f"  - {issue}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Canonicalize historical Integrated Chinese SPEAK/LISTEN_WRITE lesson items."
    )
    parser.add_argument(
        "--lang",
        action="append",
        default=[],
        metavar="LANG",
        help="Artifact language folder to process. Repeat for multiple languages.",
    )
    parser.add_argument(
        "--all-langs",
        action="store_true",
        help="Process every available language folder under Integrated Chinese artifacts.",
    )
    parser.add_argument(
        "--lesson",
        action="append",
        type=int,
        default=[],
        metavar="ID",
        help="Restrict work to lesson ID. Repeat for multiple lessons.",
    )
    parser.add_argument(
        "--include-output-json",
        action="store_true",
        help="Also migrate output_json in addition to synced_json.",
    )
    parser.add_argument(
        "--apply-json",
        action="store_true",
        help="Write migrated JSON. Omit for a dry-run preview.",
    )
    parser.add_argument(
        "--overwrite-backup",
        action="store_true",
        help="Allow replacing an existing per-file migration backup.",
    )
    parser.add_argument(
        "--sync-db",
        action="store_true",
        help="Re-sync each changed JSON to PostgreSQL after JSON migration. Requires --apply-json.",
    )
    parser.add_argument(
        "--sync-existing-db",
        action="store_true",
        help="Re-sync already-migrated JSON artifacts to PostgreSQL without rewriting JSON.",
    )
    args = parser.parse_args()

    if args.sync_db and not args.apply_json:
        parser.error("--sync-db requires --apply-json so DB data cannot get ahead of the JSON source.")
    if args.sync_existing_db and (args.sync_db or args.apply_json):
        parser.error("--sync-existing-db cannot be combined with --sync-db or --apply-json.")
    if args.overwrite_backup and not args.apply_json:
        parser.error("--overwrite-backup only applies together with --apply-json.")
    if args.all_langs and args.lang:
        parser.error("Use either --all-langs or one or more --lang values, not both.")

    langs = [_normalize_lang(lang) for lang in args.lang if _normalize_lang(lang)]
    if args.all_langs:
        langs = _available_languages(args.include_output_json)
    if not langs:
        langs = [DEFAULT_LANG]

    report = MigrationReport()
    lessons = set(args.lesson)
    if args.sync_existing_db:
        report.changed_files = [
            FileReport(path=path, lang=lang, changed=True)
            for path, lang in iter_artifacts(
                langs=langs,
                lessons=lessons,
                include_output_json=args.include_output_json,
            )
        ]
        report.files_scanned = len(report.changed_files)
        report.files_changed = len(report.changed_files)
    else:
        for path, lang in iter_artifacts(
            langs=langs,
            lessons=lessons,
            include_output_json=args.include_output_json,
        ):
            try:
                file_report = migrate_file(
                    path,
                    lang,
                    apply_json=args.apply_json,
                    overwrite_backup=args.overwrite_backup,
                )
            except (MigrationError, OSError, json.JSONDecodeError) as exc:
                file_report = FileReport(path=path, lang=lang, unresolved=[str(exc)])
            report.add(file_report)

    _print_report(report, dry_run=not args.apply_json and not args.sync_existing_db)
    if report.unresolved:
        raise SystemExit("Migration stopped: resolve the listed items before applying or syncing.")

    if (args.sync_db or args.sync_existing_db) and report.changed_files:
        failures = sync_changed_files(report.changed_files)
        if failures:
            print("\nDatabase sync failures:")
            for failure in failures:
                print(f"  - {failure}")
            raise SystemExit("JSON migration completed, but one or more DB syncs failed.")
        print(f"\nDatabase sync complete for {len(report.changed_files)} JSON files.")


if __name__ == "__main__":
    main()
