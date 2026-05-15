"""Report Cloudflare R2 objects that are not referenced by local JSON or DB.

Read-only by default. Use this before deleting any media from R2.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from database.connection import get_connection
from services.storage.r2_storage import R2Storage


ARTIFACTS_DIR = BACKEND_DIR / "content_builder" / "artifacts"


def human_size(value: int) -> str:
    size = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.2f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.2f} TB"


def extract_object_keys(value) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        object_key = value.get("object_key")
        if isinstance(object_key, str) and object_key.strip():
            keys.add(object_key.strip().lstrip("/"))
        for child in value.values():
            keys.update(extract_object_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(extract_object_keys(child))
    return keys


def collect_local_keys() -> set[str]:
    keys: set[str] = set()
    for path in ARTIFACTS_DIR.rglob("*.json"):
        if "node_modules" in path.parts:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        keys.update(extract_object_keys(data))
    return keys


def collect_db_keys() -> set[str]:
    keys: set[str] = set()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT lesson_metadata, course_content, teaching_materials, video_plan,
               video_render_plan, lesson_audio_assets, explanation_video_urls
        FROM lessons;
        """
    )
    for row in cur.fetchall():
        for value in row:
            keys.update(extract_object_keys(value))
    cur.close()
    conn.close()
    return keys


def list_r2_objects(prefix: str = "") -> list[dict]:
    storage = R2Storage.from_env(optional=False)
    client = storage._get_client()
    paginator = client.get_paginator("list_objects_v2")
    objects: list[dict] = []
    kwargs = {"Bucket": storage.bucket}
    if prefix:
        kwargs["Prefix"] = prefix.strip().lstrip("/")
    for page in paginator.paginate(**kwargs):
        objects.extend(page.get("Contents", []))
    return objects


def summarize(label: str, objects: list[dict]) -> None:
    total = sum(int(item.get("Size") or 0) for item in objects)
    print(f"{label}: count={len(objects)} size={human_size(total)}")


def group_by_prefix(objects: list[dict], depth: int = 3) -> list[tuple[str, int, int]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in objects:
        key = str(item.get("Key") or "")
        parts = key.split("/")
        group = "/".join(parts[:depth]) if len(parts) >= depth else key
        grouped[group].append(item)
    rows = []
    for group, items in grouped.items():
        rows.append((group, len(items), sum(int(item.get("Size") or 0) for item in items)))
    return sorted(rows, key=lambda row: row[2], reverse=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", default="", help="Optional R2 prefix to scan, e.g. zh/")
    parser.add_argument("--top", type=int, default=30)
    args = parser.parse_args()

    print("Collecting referenced object keys...")
    local_keys = collect_local_keys()
    db_keys = collect_db_keys()
    referenced = local_keys | db_keys
    print(f"local_keys={len(local_keys)} db_keys={len(db_keys)} union={len(referenced)}")

    print("Listing R2 objects...")
    objects = list_r2_objects(args.prefix)
    summarize("r2_total", objects)

    orphan = [item for item in objects if str(item.get("Key") or "").strip().lstrip("/") not in referenced]
    referenced_objects = [item for item in objects if str(item.get("Key") or "").strip().lstrip("/") in referenced]
    summarize("r2_referenced", referenced_objects)
    summarize("r2_orphan_candidates", orphan)

    print("\nTop orphan groups:")
    for group, count, size in group_by_prefix(orphan)[: args.top]:
        print(f"  {group:48} count={count:6} size={human_size(size):>10}")

    print("\nTop orphan objects:")
    for item in sorted(orphan, key=lambda row: int(row.get("Size") or 0), reverse=True)[: args.top]:
        print(f"  {human_size(int(item.get('Size') or 0)):>10}  {item.get('Key')}")


if __name__ == "__main__":
    main()
