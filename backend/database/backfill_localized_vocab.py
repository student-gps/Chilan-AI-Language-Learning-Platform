#!/usr/bin/env python3
"""
backfill_localized_vocab.py

Patches vocabulary_knowledge and language_items.metadata->knowledge
for localized courses (e.g. ja, fr) WITHOUT re-uploading R2 assets
or regenerating embeddings.

Safe to run multiple times (all writes are idempotent upserts / jsonb_set).

Usage:
    python database/backfill_localized_vocab.py --lang ja
    python database/backfill_localized_vocab.py --lang fr
    python database/backfill_localized_vocab.py --lang ja --lang fr
    python database/backfill_localized_vocab.py --lang ja --dry-run
"""

import argparse
import json
import re
import sys
from pathlib import Path

from psycopg2.extras import Json, RealDictCursor

sys.path.append(str(Path(__file__).resolve().parent.parent))
from database.connection import get_connection
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

CONTENT_BUILDER_DIR = Path(__file__).resolve().parents[1] / "content_builder"
ARTIFACT_ROOT = CONTENT_BUILDER_DIR / "artifacts" / "integrated_chinese"


# ── helpers ──────────────────────────────────────────────────────────────────

def _resolve_course_id(cur, lang: str) -> int:
    category = f"{lang.upper()}_TO_CN"
    cur.execute(
        """
        SELECT course_id FROM courses
        WHERE category = %s AND lower(target_language) = 'chinese'
        ORDER BY course_id
        """,
        (category,),
    )
    rows = cur.fetchall()
    if len(rows) == 1:
        return int(rows[0][0])
    if not rows:
        raise ValueError(
            f"No course found for lang={lang!r} (category={category!r}). "
            "Create the course first."
        )
    raise ValueError(
        f"Multiple courses matched for lang={lang!r}, category={category!r}: {rows}"
    )


def _extract_lesson_id(path: Path) -> int | None:
    nums = re.findall(r"\d+", path.stem)
    return int(nums[0]) if nums else None


def _build_vocab_lookup(course_content: dict) -> dict[str, dict]:
    lookup: dict[str, dict] = {}
    for vocab in course_content.get("vocabulary", []):
        if not isinstance(vocab, dict):
            continue
        word = (vocab.get("word") or "").strip()
        if word:
            lookup[word] = vocab
    return lookup


def _get_vocab_word(q_type: str, item: dict) -> str:
    """
    Derive the Chinese word key used to look up vocab_lookup.
    - CN_TO_*  : original_text is the Chinese word
    - *_TO_CN* : standard_answers[0] is the Chinese word
    """
    if re.match(r"^CN_TO_\w+$", q_type or ""):
        return (item.get("original_text") or "").strip()
    if re.match(r"^\w+_TO_CN", q_type or ""):
        answers = item.get("standard_answers") or []
        return (answers[0] if answers else "").strip()
    return ""


def _build_knowledge(vocab_word: str, vocab_entry: dict, q_pinyin: str) -> dict:
    current_example = vocab_entry.get("example_sentence", {})
    historical_usages = vocab_entry.get("historical_usages", [])
    current_definition = (vocab_entry.get("definition") or "").strip().lower()

    history_cards = []
    for usage in (historical_usages if isinstance(historical_usages, list) else []):
        if not isinstance(usage, dict):
            continue
        usage_def = (usage.get("definition") or "").strip()
        if usage_def.lower() == current_definition:
            continue
        history_cards.append({
            "definition": usage_def,
            "pinyin": usage.get("pinyin"),
            "part_of_speech": usage.get("part_of_speech"),
            "example": usage.get("example", {}),
            "lesson_id": usage.get("lesson_id"),
        })

    return {
        "word": vocab_word or vocab_entry.get("word", ""),
        "pinyin": vocab_entry.get("pinyin", q_pinyin),
        "part_of_speech": vocab_entry.get("part_of_speech", ""),
        "definition": vocab_entry.get("definition", ""),
        "example_sentence": current_example,
        "history": history_cards,
    }


# ── per-file patch ────────────────────────────────────────────────────────────

def patch_file(cur, json_path: Path, course_id: int, dry_run: bool) -> tuple[int, int]:
    """Returns (vocab_knowledge_rows, language_items_rows) affected."""
    lesson_id = _extract_lesson_id(json_path)
    if lesson_id is None:
        print(f"  ⚠️  Cannot parse lesson_id from {json_path.name}, skipping.")
        return 0, 0

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    course_content = data.get("course_content") or {}
    vocab_lookup = _build_vocab_lookup(course_content)
    database_items = data.get("database_items") or []

    vk_count = 0
    li_count = 0

    for item in database_items:
        q_id = item.get("question_id")
        q_type = item.get("question_type") or ""
        q_pinyin = item.get("original_pinyin") or ""

        vocab_word = _get_vocab_word(q_type, item)
        vocab_entry = vocab_lookup.get(vocab_word)
        if not vocab_entry or not (vocab_entry.get("word") or "").strip():
            continue

        knowledge = _build_knowledge(vocab_word, vocab_entry, q_pinyin)

        if dry_run:
            print(
                f"    [DRY] lesson={lesson_id} q={q_id} type={q_type} "
                f"word={vocab_word!r} def={knowledge['definition'][:40]!r}"
            )
            vk_count += 1
            li_count += 1
            continue

        # 1. Upsert vocabulary_knowledge
        cur.execute(
            """
            INSERT INTO vocabulary_knowledge
                (course_id, lesson_id, word, pinyin, part_of_speech, definition, example)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (course_id, lesson_id, word, definition)
            DO UPDATE SET
                pinyin          = EXCLUDED.pinyin,
                part_of_speech  = EXCLUDED.part_of_speech,
                example         = EXCLUDED.example
            """,
            (
                course_id,
                lesson_id,
                (vocab_entry.get("word") or "").strip(),
                vocab_entry.get("pinyin"),
                vocab_entry.get("part_of_speech"),
                vocab_entry.get("definition"),
                Json(vocab_entry.get("example_sentence", {})),
            ),
        )
        vk_count += 1

        # 2. Patch language_items.metadata->knowledge (jsonb_set, surgical update)
        cur.execute(
            """
            UPDATE language_items
            SET metadata = jsonb_set(
                COALESCE(metadata, '{}'::jsonb),
                '{knowledge}',
                %s::jsonb
            )
            WHERE course_id = %s AND lesson_id = %s AND question_id = %s
            """,
            (
                Json(knowledge),
                course_id,
                lesson_id,
                q_id,
            ),
        )
        li_count += cur.rowcount

    return vk_count, li_count


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Backfill vocabulary_knowledge and metadata->knowledge for localized courses."
    )
    parser.add_argument(
        "--lang",
        action="append",
        required=True,
        metavar="LANG",
        help="Language code to patch (e.g. ja, fr). Repeat for multiple.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be patched without writing to DB.",
    )
    args = parser.parse_args()

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    for lang in args.lang:
        print(f"\n{'='*50}")
        print(f"🌐 Language: {lang.upper()}")

        try:
            course_id = _resolve_course_id(cur, lang)
            print(f"   course_id = {course_id}")
        except ValueError as e:
            print(f"   ❌ {e}")
            continue

        # Prefer synced_json (already processed), fall back to output_json
        synced_dir = ARTIFACT_ROOT / "synced_json" / lang
        output_dir = ARTIFACT_ROOT / "output_json" / lang
        scan_dir = synced_dir if synced_dir.exists() else output_dir

        json_files = sorted(scan_dir.glob("*_data*.json"), key=lambda p: _extract_lesson_id(p) or 0)
        if not json_files:
            print(f"   ⚠️  No JSON files found in {scan_dir}")
            continue

        print(f"   📂 Scanning {scan_dir} ({len(json_files)} files)")

        total_vk = 0
        total_li = 0
        for json_path in json_files:
            vk, li = patch_file(cur, json_path, course_id, dry_run=args.dry_run)
            total_vk += vk
            total_li += li
            print(f"   ✅ {json_path.name}: vocab_knowledge={vk}, language_items={li}")

        if not args.dry_run:
            conn.commit()
            print(f"\n   💾 Committed. Total: vocab_knowledge={total_vk}, language_items={total_li}")
        else:
            print(f"\n   [DRY] Would patch: vocab_knowledge≈{total_vk}, language_items≈{total_li}")

    cur.close()
    conn.close()
    print("\n✨ Done.")


if __name__ == "__main__":
    main()
