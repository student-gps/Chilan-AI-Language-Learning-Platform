import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path


CONTENT_BUILDER_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = CONTENT_BUILDER_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database.connection import get_connection


def _jsonable(value):
    if value is None:
        return {} 
    return value


def _database_items(cur, course_id: int, lesson_id: int) -> list[dict]:
    cur.execute(
        """
        SELECT question_id, question_type, original_text, original_pinyin,
               standard_answers, metadata
        FROM language_items
        WHERE course_id = %s AND lesson_id = %s
        ORDER BY question_id
        """,
        (course_id, lesson_id),
    )
    items = []
    for qid, qtype, original_text, original_pinyin, answers, metadata in cur.fetchall():
        metadata = metadata or {}
        item = {
            "lesson_id": lesson_id,
            "question_id": qid,
            "course_id": course_id,
            "question_type": qtype,
            "original_text": original_text or "",
            "original_pinyin": original_pinyin or "",
            "standard_answers": list(answers or []),
            "context_examples": metadata.get("context_examples", []),
        }
        extra_metadata = {
            key: value
            for key, value in metadata.items()
            if key not in {"context_examples", "knowledge"}
        }
        if extra_metadata:
            item["metadata"] = extra_metadata
        items.append(item)
    return items


def _backup_output_dir(output_dir: Path) -> Path | None:
    if not output_dir.exists():
        return None
    backup_dir = output_dir.with_name(f"{output_dir.name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    shutil.copytree(output_dir, backup_dir)
    return backup_dir


def export_lessons(course_id: int, output_dir: Path, backup: bool = True) -> int:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    backup_dir = _backup_output_dir(output_dir) if backup else None
    if backup_dir:
        print(f"Backed up existing JSON directory to: {backup_dir}")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT lesson_id, title, lesson_metadata, course_content,
                   teaching_materials, video_plan, video_render_plan,
                   lesson_audio_assets, explanation_video_urls, llm_usage
            FROM lessons
            WHERE course_id = %s
            ORDER BY lesson_id
            """,
            (course_id,),
        )
        rows = cur.fetchall()
        for (
            lesson_id,
            _title,
            lesson_metadata,
            course_content,
            teaching_materials,
            video_plan,
            video_render_plan,
            lesson_audio_assets,
            explanation_video_urls,
            llm_usage,
        ) in rows:
            data = {
                "lesson_metadata": _jsonable(lesson_metadata),
                "course_content": _jsonable(course_content),
                "teaching_materials": _jsonable(teaching_materials),
                "database_items": _database_items(cur, course_id, int(lesson_id)),
                "video_plan": _jsonable(video_plan),
                "video_render_plan": _jsonable(video_render_plan),
                "lesson_audio_assets": _jsonable(lesson_audio_assets),
                "llm_usage": _jsonable(llm_usage),
                "explanation_video_urls": _jsonable(explanation_video_urls),
            }
            deck = data["video_render_plan"].get("teaching_slide_deck") if isinstance(data["video_render_plan"], dict) else None
            if isinstance(deck, dict):
                data["teaching_slide_deck"] = deck

            output_path = output_dir / f"lesson{int(lesson_id)}_data.json"
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write("\n")
            print(f"Exported {output_path.name}")
    finally:
        cur.close()
        conn.close()

    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export lesson JSON payloads from the lessons table.")
    parser.add_argument("--course-id", type=int, default=1)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=CONTENT_BUILDER_DIR / "artifacts" / "integrated_chinese" / "output_json" / "en",
    )
    parser.add_argument("--no-backup", action="store_true")
    args = parser.parse_args()

    count = export_lessons(args.course_id, args.output_dir, backup=not args.no_backup)
    print(f"Done: exported {count} lesson JSON file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
