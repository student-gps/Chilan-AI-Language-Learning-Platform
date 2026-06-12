#!/usr/bin/env python3
"""
Fast course_content refresh: update lessons.course_content in DB from JSON files.
Does NOT regenerate embeddings or upload to R2. Much faster than sync_to_db.py.

Usage (from backend/):
    python database/refresh_tokens.py
    python database/refresh_tokens.py --dry-run
"""

import json
import re
import sys
from functools import lru_cache
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

from database.connection import get_connection  # noqa: E402
from psycopg2.extras import Json               # noqa: E402

CB_DIR = BACKEND_DIR / "content_builder"

# Directories to scan: (base_dir, lang_from_subdir)
# Old structure: synced_json/en/*.json — all English canonical
# New structure: synced_json/{lang}/*.json — each lang has its own subdir
SCAN_ROOTS = [
    CB_DIR / "artifacts" / "integrated_chinese" / "synced_json",
    CB_DIR / "zh" / "integrated_chinese" / "artifacts" / "synced_json",
]

LANG_SUFFIXES = ["fr", "de", "es", "ko", "ja", "ar", "ru", "vi", "th", "pt", "ms", "id", "it"]


@lru_cache(maxsize=32)
def _get_course_id(lang: str) -> int | None:
    if not lang or lang == "en":
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT course_id FROM courses WHERE category = 'EN_TO_CN' ORDER BY course_id LIMIT 1"
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        return int(row[0]) if row else None

    category = f"{lang.upper()}_TO_CN"
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT course_id FROM courses WHERE category = %s AND lower(target_language) = 'chinese' ORDER BY course_id LIMIT 1",
        (category,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return int(row[0]) if row else None


def _parse_lesson_id(stem: str, lang: str) -> int | None:
    # Remove _{lang} suffix if present
    if lang != "en" and stem.endswith(f"_{lang}"):
        stem = stem[: -len(f"_{lang}")]
    # lesson{digits}_data  or  lesson{digits}
    m = re.match(r"^lesson(\d+)(?:_data)?$", stem)
    if not m:
        return None
    return int(m.group(1))


def collect_files() -> list[tuple[Path, str]]:
    """Return list of (json_path, lang_code) for all lesson JSON files."""
    result: list[tuple[Path, str]] = []
    seen: set[tuple[str, str]] = set()  # dedup by (stem, lang)

    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for lang_dir in sorted(root.iterdir()):
            if not lang_dir.is_dir():
                continue
            dir_lang = lang_dir.name  # "en", "fr", etc.
            for f in sorted(lang_dir.glob("*_data*.json")):
                # Detect language: prefer filename suffix over directory name
                # (old structure placed _fr variants in the en/ dir)
                lang = dir_lang
                for lc in LANG_SUFFIXES:
                    if f.stem.endswith(f"_{lc}"):
                        lang = lc
                        break
                key = (f.stem, lang)
                if key in seen:
                    continue
                seen.add(key)
                result.append((f, lang))

    return result


def main() -> None:
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv

    files = collect_files()
    print(f"Found {len(files)} JSON files across all language directories\n")

    ok = 0
    skipped = 0
    errors = 0

    conn = get_connection()
    cur = conn.cursor()

    for path, lang in files:
        lesson_id = _parse_lesson_id(path.stem, lang)
        if lesson_id is None:
            print(f"  SKIP  {path.name}  (cannot parse lesson_id)")
            skipped += 1
            continue

        course_id = _get_course_id(lang)
        if course_id is None:
            print(f"  SKIP  {path.name}  (no course found for lang={lang!r})")
            skipped += 1
            continue

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            print(f"  ERR   {path.name}: {exc}")
            errors += 1
            continue

        course_content = data.get("course_content")
        if not course_content:
            skipped += 1
            continue

        if dry_run:
            ok += 1
            continue

        try:
            cur.execute(
                "UPDATE lessons SET course_content = %s WHERE course_id = %s AND lesson_id = %s",
                (Json(course_content), course_id, lesson_id),
            )
            if cur.rowcount == 0:
                skipped += 1
            else:
                ok += 1
                if ok % 100 == 0:
                    conn.commit()
                    print(f"  ... {ok} rows updated")
        except Exception as exc:
            print(f"  ERR   {path.name}: {exc}")
            conn.rollback()
            errors += 1

    conn.commit()
    cur.close()
    conn.close()

    verb = "would update" if dry_run else "updated"
    print(f"\nDone: {ok} rows {verb} | {skipped} skipped (no DB row or empty) | {errors} errors")


if __name__ == "__main__":
    main()
