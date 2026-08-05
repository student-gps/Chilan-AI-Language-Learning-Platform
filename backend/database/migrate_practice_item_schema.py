#!/usr/bin/env python3
"""Migrate practice artifacts and language_items to schema-v2 activity types.

The command is dry-run by default. It never changes JSON or PostgreSQL until the
corresponding apply flag is supplied.

Examples (run from backend/):
  python database/migrate_practice_item_schema.py lesson101_data.json
  python database/migrate_practice_item_schema.py --artifact-dir content_builder/ja/minna_no_nihongo/artifacts/synced_json/zh
  python database/migrate_practice_item_schema.py --apply-json lesson101_data.json
  python database/migrate_practice_item_schema.py --apply-json --apply-db lesson101_data.json
"""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from psycopg2.extras import Json, RealDictCursor


CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from database.connection import get_connection
from services.study.practice_item_schema import (
    CANONICAL_QUESTION_TYPES,
    PracticeItemSchemaError,
    canonicalize_database_item,
    normalize_language_code,
)


@dataclass
class MigrationReport:
    path: Path
    converted: int = 0
    already_canonical: int = 0
    changed: bool = False
    errors: list[str] = field(default_factory=list)


class MigrationError(ValueError):
    """Raised when a file or database row cannot be migrated safely."""


def _language_from(values: Iterable[Any], *, field_name: str) -> str:
    for value in values:
        if value:
            return normalize_language_code(value, field_name=field_name)
    raise MigrationError(f"Cannot resolve {field_name}")


def _payload_defaults(payload: dict, fallback_support_language: str | None = None) -> dict[str, str]:
    lesson_metadata = payload.get("lesson_metadata")
    lesson_metadata = lesson_metadata if isinstance(lesson_metadata, dict) else {}
    localization = payload.get("localization")
    localization = localization if isinstance(localization, dict) else {}

    target = _language_from(
        (
            payload.get("target_language"),
            lesson_metadata.get("target_language"),
            localization.get("target_lang"),
        ),
        field_name="course_target_language",
    )
    support = _language_from(
        (
            fallback_support_language,
            payload.get("support_language"),
            lesson_metadata.get("support_language"),
            lesson_metadata.get("source_language"),
            payload.get("source_language"),
        ),
        field_name="course_support_language",
    )
    return {
        "course_target_language": target,
        "course_support_language": support,
        "feedback_language": support,
    }


def canonicalize_payload(payload: dict, *, fallback_support_language: str | None = None) -> tuple[dict, MigrationReport]:
    if not isinstance(payload, dict):
        raise MigrationError("Payload must be a JSON object")

    migrated = copy.deepcopy(payload)
    report = MigrationReport(path=Path("<payload>"))
    defaults = _payload_defaults(migrated, fallback_support_language)
    items = migrated.get("database_items")
    if not isinstance(items, list):
        raise MigrationError("database_items must be a list")

    canonical_items = []
    for index, raw_item in enumerate(items):
        if not isinstance(raw_item, dict):
            raise MigrationError(f"database_items[{index}] must be an object")
        before_type = str(raw_item.get("question_type") or "").strip().upper()
        try:
            item = canonicalize_database_item(
                raw_item,
                defaults=defaults,
                retire_legacy_fields=True,
            )
        except PracticeItemSchemaError as exc:
            raise MigrationError(f"database_items[{index}] {before_type or '<empty>'}: {exc}") from exc
        if item["question_type"] not in CANONICAL_QUESTION_TYPES:
            raise MigrationError(f"database_items[{index}] did not produce a canonical question_type")
        if before_type == item["question_type"]:
            report.already_canonical += 1
        else:
            report.converted += 1
        canonical_items.append(item)

    migrated["database_items"] = canonical_items
    report.changed = migrated != payload
    return migrated, report


def _backup_path(path: Path) -> Path:
    return path.with_name(f"{path.stem}.practice-schema-v2-backup{path.suffix}")


def migrate_file(
    path: Path,
    *,
    fallback_support_language: str | None = None,
    apply_json: bool = False,
    overwrite_backup: bool = False,
) -> MigrationReport:
    with path.open(encoding="utf-8") as handle:
        source = json.load(handle)
    migrated, report = canonicalize_payload(source, fallback_support_language=fallback_support_language)
    report.path = path

    if apply_json and report.changed:
        backup = _backup_path(path)
        if backup.exists() and not overwrite_backup:
            raise MigrationError(f"Backup already exists: {backup}; use --overwrite-backup to replace it")
        shutil.copy2(path, backup)
        path.write_text(json.dumps(migrated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def _payload_identity(payload: dict, path: Path) -> tuple[int, int]:
    metadata = payload.get("lesson_metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    course_id = metadata.get("course_id")
    lesson_id = metadata.get("lesson_id")
    try:
        return int(course_id), int(lesson_id)
    except (TypeError, ValueError) as exc:
        raise MigrationError(f"{path}: lesson_metadata.course_id and lesson_id must be numeric for --apply-db") from exc


def patch_database_from_payload(payload: dict, path: Path, *, fallback_support_language: str | None = None, apply: bool = False) -> int:
    migrated, _ = canonicalize_payload(payload, fallback_support_language=fallback_support_language)
    course_id, lesson_id = _payload_identity(migrated, path)
    conn = get_connection()
    updated = 0
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        for item in migrated["database_items"]:
            question_id = item.get("question_id")
            cur.execute(
                """
                SELECT item_id, standard_answers, question_type, metadata
                FROM language_items
                WHERE course_id = %s AND lesson_id = %s AND question_id = %s
                """,
                (course_id, lesson_id, question_id),
            )
            row = cur.fetchone()
            if not row:
                raise MigrationError(f"{path}: missing DB item course={course_id}, lesson={lesson_id}, question={question_id}")
            if list(row.get("standard_answers") or []) != list(item.get("standard_answers") or []):
                raise MigrationError(f"{path}: standard_answers mismatch for question_id={question_id}")
            if row.get("question_type") == item["question_type"] and row.get("metadata") == item["metadata"]:
                continue
            updated += 1
            if apply:
                cur.execute(
                    """
                    UPDATE language_items
                    SET question_type = %s, metadata = %s
                    WHERE item_id = %s
                    """,
                    (item["question_type"], Json(item["metadata"]), row["item_id"]),
                )
                if cur.rowcount != 1:
                    raise MigrationError(f"{path}: expected exactly one updated row for question_id={question_id}")
        if apply:
            conn.commit()
        else:
            conn.rollback()
        return updated
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _json_paths(files: list[str], directories: list[str]) -> list[Path]:
    paths = {Path(value) for value in files}
    for directory in directories:
        paths.update(Path(directory).glob("*_data*.json"))
    return sorted(paths)


def main() -> None:
    parser = argparse.ArgumentParser(description="Canonicalize practice-item question types and metadata.")
    parser.add_argument("files", nargs="*", help="Specific lesson JSON file(s) to inspect.")
    parser.add_argument("--artifact-dir", action="append", default=[], help="Directory containing lesson JSON artifacts; repeatable.")
    parser.add_argument("--support-language", help="Fallback support language when an old artifact lacks it.")
    parser.add_argument("--apply-json", action="store_true", help="Write migrated JSON after creating backups.")
    parser.add_argument("--apply-db", action="store_true", help="Patch matching language_items rows; requires --apply-json.")
    parser.add_argument("--overwrite-backup", action="store_true", help="Allow replacement of an existing migration backup.")
    args = parser.parse_args()

    if args.apply_db and not args.apply_json:
        parser.error("--apply-db requires --apply-json so artifact and database state remain aligned.")
    paths = _json_paths(args.files, args.artifact_dir)
    if not paths:
        parser.error("Provide at least one file or --artifact-dir.")

    failures = []
    total_converted = 0
    total_db_updates = 0
    for path in paths:
        try:
            report = migrate_file(
                path,
                fallback_support_language=args.support_language,
                apply_json=args.apply_json,
                overwrite_backup=args.overwrite_backup,
            )
            total_converted += report.converted
            print(
                f"{path}: converted={report.converted}, already_canonical={report.already_canonical}, changed={report.changed}"
            )
            if args.apply_db:
                payload = json.loads(path.read_text(encoding="utf-8"))
                updates = patch_database_from_payload(
                    payload,
                    path,
                    fallback_support_language=args.support_language,
                    apply=True,
                )
                total_db_updates += updates
                print(f"  database_updates={updates}")
        except (OSError, json.JSONDecodeError, MigrationError) as exc:
            failures.append(f"{path}: {exc}")

    print(f"Summary: files={len(paths)}, converted={total_converted}, database_updates={total_db_updates}, failures={len(failures)}")
    for failure in failures:
        print(f"ERROR: {failure}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
