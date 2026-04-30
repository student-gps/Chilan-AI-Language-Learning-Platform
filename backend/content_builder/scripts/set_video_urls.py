"""
set_video_urls.py — Update video URLs for a lesson's explanation video.

Usage:
    python set_video_urls.py 101 --show
    python set_video_urls.py 101 --cos-key "zh/video/en/lesson101_explanation_final.mp4"
    python set_video_urls.py 101 --youtube "https://youtu.be/xxxxx"
    python set_video_urls.py 101 --bilibili "https://b23.tv/xxxxx"
"""

import argparse
import json
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent   # backend/content_builder/scripts/
CONTENT_BUILDER_DIR = CURRENT_DIR.parent        # backend/content_builder/
ARTIFACTS_DIR = CONTENT_BUILDER_DIR / "artifacts" / "integrated_chinese"
BACKEND_DIR = CONTENT_BUILDER_DIR.parent        # backend/
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

from database.connection import get_connection
from psycopg2.extras import Json


def _get_lesson_json_path(lesson_id: int) -> Path:
    return ARTIFACTS_DIR / "output_json" / "en" / f"lesson{lesson_id}_data.json"


def show_current(lesson_id: int):
    conn = get_connection()
    from psycopg2.extras import RealDictCursor
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute(
        "SELECT explanation_video_urls FROM lessons WHERE lesson_id = %s LIMIT 1",
        (lesson_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        print(f"❌ Lesson {lesson_id} not found in database.")
        return
    urls = row["explanation_video_urls"] or {}
    print(f"\nLesson {lesson_id} — explanation_video_urls:")
    print(f"  media_url:      {urls.get('media_url', '(empty)')}")
    print(f"  youtube_url:    {urls.get('youtube_url', '(empty)')}")
    print(f"  bilibili_url:   {urls.get('bilibili_url', '(empty)')}")
    print(f"  local_path:     {urls.get('local_path', '(empty)')}\n")


def update_urls(lesson_id: int, youtube_url: str | None, bilibili_url: str | None, cos_key: str | None):
    conn = get_connection()
    from psycopg2.extras import RealDictCursor
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT explanation_video_urls FROM lessons WHERE lesson_id = %s LIMIT 1",
        (lesson_id,),
    )
    row = cur.fetchone()
    if not row:
        print(f"❌ Lesson {lesson_id} not found in database.")
        cur.close()
        conn.close()
        return

    video_urls: dict = dict(row["explanation_video_urls"] or {})

    if cos_key is not None:
        # Store only the object key; the study router generates signed URLs on every request
        video_urls["object_key"] = cos_key.strip()
        video_urls["media_url"] = ""   # cleared — backend hydrates this dynamically
        print(f"  ✅ object_key → {cos_key.strip()}")

    if youtube_url is not None:
        video_urls["youtube_url"] = youtube_url.strip()
        print(f"  ✅ youtube_url  → {video_urls['youtube_url']}")
    if bilibili_url is not None:
        video_urls["bilibili_url"] = bilibili_url.strip()
        print(f"  ✅ bilibili_url → {video_urls['bilibili_url']}")

    cur.execute(
        "UPDATE lessons SET explanation_video_urls = %s WHERE lesson_id = %s",
        (Json(video_urls), lesson_id),
    )
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Database updated for lesson {lesson_id}.")

    # Also update the local JSON file if it exists
    json_path = _get_lesson_json_path(lesson_id)
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        existing = data.get("explanation_video_urls") or {}
        existing.update({k: v for k, v in video_urls.items() if k in ("media_url", "object_key", "youtube_url", "bilibili_url")})
        data["explanation_video_urls"] = existing
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON file updated: {json_path.name}")


def main():
    parser = argparse.ArgumentParser(
        description="Update YouTube / Bilibili URLs for a lesson's explanation video."
    )
    parser.add_argument("lesson_id", type=int, help="Lesson ID (e.g. 101)")
    parser.add_argument("--cos-key",  type=str, default=None, help="R2 object key (e.g. zh/video/en/lesson101_explanation_final.mp4)")
    parser.add_argument("--youtube",  type=str, default=None, help="YouTube video URL")
    parser.add_argument("--bilibili", type=str, default=None, help="Bilibili video URL")
    parser.add_argument("--show",     action="store_true", help="Show current URLs and exit")
    args = parser.parse_args()

    if args.show:
        show_current(args.lesson_id)
        return

    if args.cos_key is None and args.youtube is None and args.bilibili is None:
        print("Nothing to update. Use --cos-key / --youtube / --bilibili, or --show to inspect.")
        parser.print_help()
        return

    update_urls(args.lesson_id, args.youtube, args.bilibili, args.cos_key)


if __name__ == "__main__":
    main()
