"""Backfill canonical numbering and verify topic titles for the Japanese course.

The app uses one continuous lesson sequence (1-74), while the intermediate
source book restarts its printed chapter numbers. This command repairs both
local lesson artifacts and the matching PostgreSQL rows without touching lesson
content, media, practice items, or learner progress.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from psycopg2.extras import Json


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database.connection import get_connection


DEFAULT_COURSE_ID = 303
DEFAULT_LANG = "zh"
ARTIFACT_ROOT = (
    BACKEND_DIR
    / "content_builder"
    / "ja"
    / "minna_no_nihongo"
    / "artifacts"
)


def canonical_titles(lesson_id: int) -> tuple[str, str]:
    return f"第{lesson_id}課", f"第{lesson_id}课"


def load_artifacts(lang: str) -> dict[int, tuple[Path, dict]]:
    artifacts: dict[int, tuple[Path, dict]] = {}
    for folder in ("synced_json", "output_json"):
        directory = ARTIFACT_ROOT / folder / lang
        for path in sorted(directory.glob("lesson*_data.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            metadata = data.get("lesson_metadata")
            if not isinstance(metadata, dict):
                raise ValueError(f"{path} has no lesson_metadata object")
            lesson_id = int(metadata.get("lesson_id"))
            artifacts[lesson_id] = (path, data)
    return artifacts


def validate_topic_titles(records: dict[int, tuple[Path, dict]]) -> None:
    missing = []
    for lesson_id, (_, data) in sorted(records.items()):
        metadata = data["lesson_metadata"]
        if not str(metadata.get("topic_title") or "").strip():
            missing.append(f"lesson{lesson_id:03d}: topic_title")
        if not str(metadata.get("topic_title_localized") or "").strip():
            missing.append(f"lesson{lesson_id:03d}: topic_title_localized")
    if missing:
        raise ValueError("Missing Japanese lesson titles: " + ", ".join(missing))


def update_artifacts(records: dict[int, tuple[Path, dict]], *, dry_run: bool) -> int:
    changed = 0
    for lesson_id, (path, data) in sorted(records.items()):
        metadata = data["lesson_metadata"]
        title, title_localized = canonical_titles(lesson_id)
        if metadata.get("title") == title and metadata.get("title_localized") == title_localized:
            continue
        changed += 1
        metadata["title"] = title
        metadata["title_localized"] = title_localized
        if not dry_run:
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    return changed


def update_database(course_id: int, *, dry_run: bool) -> tuple[int, int]:
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            SELECT lesson_id, title, lesson_metadata
            FROM lessons
            WHERE course_id = %s
            ORDER BY lesson_id
            """,
            (course_id,),
        )
        rows = cursor.fetchall()
        missing = [
            lesson_id
            for lesson_id, _, metadata in rows
            if not str((metadata or {}).get("topic_title") or "").strip()
            or not str((metadata or {}).get("topic_title_localized") or "").strip()
        ]
        if missing:
            raise ValueError(f"Database lessons missing topic titles: {missing}")

        changed = 0
        for lesson_id, stored_title, metadata in rows:
            title, title_localized = canonical_titles(int(lesson_id))
            metadata = dict(metadata or {})
            if (
                stored_title == title
                and metadata.get("title") == title
                and metadata.get("title_localized") == title_localized
            ):
                continue
            changed += 1
            metadata["title"] = title
            metadata["title_localized"] = title_localized
            cursor.execute(
                """
                UPDATE lessons
                SET title = %s, lesson_metadata = %s
                WHERE course_id = %s AND lesson_id = %s
                """,
                (title, Json(metadata), course_id, lesson_id),
            )

        if dry_run:
            connection.rollback()
        else:
            connection.commit()
        return len(rows), changed
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course-id", type=int, default=DEFAULT_COURSE_ID)
    parser.add_argument("--lang", default=DEFAULT_LANG)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    records = load_artifacts(args.lang)
    if not records:
        raise SystemExit(f"No Japanese lesson artifacts found for lang={args.lang}")
    validate_topic_titles(records)
    artifact_changes = update_artifacts(records, dry_run=args.dry_run)
    db_count, db_changes = update_database(args.course_id, dry_run=args.dry_run)

    mode = "DRY RUN" if args.dry_run else "UPDATED"
    print(
        f"{mode}: {len(records)} artifacts verified ({artifact_changes} numbering fixes); "
        f"{db_count} database lessons verified ({db_changes} numbering fixes)."
    )


if __name__ == "__main__":
    main()
