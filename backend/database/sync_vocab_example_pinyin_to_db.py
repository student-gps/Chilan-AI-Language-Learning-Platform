import argparse
import json
import sys
from pathlib import Path

from psycopg2.extras import Json, RealDictCursor

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from database.connection import get_connection


def iter_lesson_files(target: Path):
    if target.is_file():
        yield target
        return

    for path in sorted(target.glob("*.json")):
        if path.is_file():
            yield path


def load_lesson_payload(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def sync_lesson_file(path: Path, apply: bool = False) -> dict:
    data = load_lesson_payload(path)
    lesson_metadata = data.get("lesson_metadata") or {}
    course_content = data.get("course_content") or {}
    vocabulary = course_content.get("vocabulary") or []

    course_id = lesson_metadata.get("course_id")
    lesson_id = lesson_metadata.get("lesson_id")
    if course_id is None or lesson_id is None:
        return {"file": str(path), "lessons": 0, "vocabulary": 0, "language_items": 0}

    conn = get_connection()
    try:
        updated_lessons = 0
        updated_vocab = 0
        updated_items = 0

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT course_content
                FROM lessons
                WHERE course_id = %s AND lesson_id = %s
                """,
                (course_id, lesson_id),
            )
            lesson_row = cur.fetchone()

            if lesson_row is not None:
                db_course_content = lesson_row.get("course_content") or {}
                db_vocabulary = (db_course_content.get("vocabulary") or [])

                incoming_map = {}
                for item in vocabulary:
                    if not isinstance(item, dict):
                        continue
                    key = (
                        (item.get("word") or "").strip(),
                        (item.get("definition") or "").strip(),
                    )
                    if key[0] and key[1]:
                        incoming_map[key] = item.get("example_sentence") or {}

                changed = False
                for item in db_vocabulary:
                    if not isinstance(item, dict):
                        continue
                    key = (
                        (item.get("word") or "").strip(),
                        (item.get("definition") or "").strip(),
                    )
                    replacement = incoming_map.get(key)
                    if not replacement:
                        continue
                    current_example = item.get("example_sentence") or {}
                    if current_example != replacement:
                        item["example_sentence"] = replacement
                        changed = True

                if changed:
                    updated_lessons = 1
                    if apply:
                        cur.execute(
                            """
                            UPDATE lessons
                            SET course_content = %s
                            WHERE course_id = %s AND lesson_id = %s
                            """,
                            (Json(db_course_content), course_id, lesson_id),
                        )

            for vocab_item in vocabulary:
                if not isinstance(vocab_item, dict):
                    continue

                word = (vocab_item.get("word") or "").strip()
                definition = (vocab_item.get("definition") or "").strip()
                example_sentence = vocab_item.get("example_sentence") or {}
                if not word or not definition:
                    continue

                cur.execute(
                    """
                    SELECT example
                    FROM vocabulary_knowledge
                    WHERE course_id = %s AND lesson_id = %s AND word = %s AND definition = %s
                    """,
                    (course_id, lesson_id, word, definition),
                )
                vocab_row = cur.fetchone()
                if vocab_row and (vocab_row.get("example") or {}) != example_sentence:
                    updated_vocab += 1
                    if apply:
                        cur.execute(
                            """
                            UPDATE vocabulary_knowledge
                            SET example = %s
                            WHERE course_id = %s AND lesson_id = %s AND word = %s AND definition = %s
                            """,
                            (Json(example_sentence), course_id, lesson_id, word, definition),
                        )

                cur.execute(
                    """
                    SELECT item_id, metadata
                    FROM language_items
                    WHERE course_id = %s AND lesson_id = %s
                      AND metadata->'knowledge'->>'word' = %s
                      AND metadata->'knowledge'->>'definition' = %s
                    """,
                    (course_id, lesson_id, word, definition),
                )
                language_rows = cur.fetchall()
                for row in language_rows:
                    metadata = row.get("metadata") or {}
                    knowledge = metadata.get("knowledge") or {}
                    current_example = knowledge.get("example_sentence") or {}
                    if current_example == example_sentence:
                        continue

                    knowledge["example_sentence"] = example_sentence
                    metadata["knowledge"] = knowledge
                    updated_items += 1

                    if apply:
                        cur.execute(
                            """
                            UPDATE language_items
                            SET metadata = %s
                            WHERE item_id = %s
                            """,
                            (Json(metadata), row["item_id"]),
                        )

        if apply:
            conn.commit()
        else:
            conn.rollback()

        return {
            "file": str(path),
            "lessons": updated_lessons,
            "vocabulary": updated_vocab,
            "language_items": updated_items,
        }
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Sync vocabulary example pinyin fixes from lesson JSON into the database.")
    parser.add_argument(
        "target",
        nargs="?",
        default=str(
            Path(__file__).resolve().parents[1]
            / "content_builder"
            / "zh"
            / "integrated_chinese"
            / "artifacts"
            / "synced_json"
        ),
        help="Lesson JSON file or directory. Defaults to content_builder/zh/integrated_chinese/artifacts/synced_json.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write updates into the database. Without this flag, runs as a dry run.",
    )
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.exists():
        raise SystemExit(f"Target not found: {target}")

    summaries = [sync_lesson_file(path, apply=args.apply) for path in iter_lesson_files(target)]

    total_lessons = sum(item["lessons"] for item in summaries)
    total_vocab = sum(item["vocabulary"] for item in summaries)
    total_items = sum(item["language_items"] for item in summaries)

    for item in summaries:
        if item["lessons"] or item["vocabulary"] or item["language_items"]:
            print(
                f"{Path(item['file']).name}: lessons={item['lessons']}, "
                f"vocabulary={item['vocabulary']}, language_items={item['language_items']}"
            )

    mode = "Applied" if args.apply else "Dry run"
    print(
        f"{mode} complete. files={len(summaries)}, "
        f"lessons={total_lessons}, vocabulary={total_vocab}, language_items={total_items}"
    )


if __name__ == "__main__":
    main()

