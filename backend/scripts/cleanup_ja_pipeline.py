"""
一键清理日语 pipeline 所有产物：
  1. 本地 artifacts 目录（output_json / synced_json / output_audio / output_slides / vocab_memory）
  2. PostgreSQL：course_id=303 关联的所有记录（含 user_courses）
  3. Cloudflare R2：ja/ 前缀的所有对象

用法：
    python backend/scripts/cleanup_ja_pipeline.py
    python backend/scripts/cleanup_ja_pipeline.py --dry-run   # 只预览，不实际删除
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")


COURSE_ID = 303
R2_PREFIX = "ja/"

ARTIFACTS_BASE = (
    BACKEND_DIR
    / "content_builder"
    / "ja"
    / "minna_no_nihongo"
    / "artifacts"
)
LOCAL_DIRS_TO_DELETE = [
    ARTIFACTS_BASE / "output_json",
    ARTIFACTS_BASE / "synced_json",
    ARTIFACTS_BASE / "output_audio",
    ARTIFACTS_BASE / "output_slides",
    ARTIFACTS_BASE / "vocab_memory",
]


def cleanup_local(dry_run: bool) -> None:
    print("\n── 1. 本地 artifacts ──")
    for d in LOCAL_DIRS_TO_DELETE:
        if d.exists():
            file_count = sum(1 for _ in d.rglob("*") if _.is_file())
            print(f"  {'[DRY]' if dry_run else '删除'} {d.relative_to(BACKEND_DIR)}  ({file_count} 个文件)")
            if not dry_run:
                shutil.rmtree(d)
        else:
            print(f"  跳过（不存在）: {d.relative_to(BACKEND_DIR)}")


def cleanup_db(dry_run: bool) -> None:
    from database.connection import get_connection
    print("\n── 2. 数据库 ──")
    conn = get_connection()
    cur = conn.cursor()

    # Each entry: (label, count_sql, delete_sql)
    steps = [
        (
            "user_progress_of_language_items",
            "SELECT COUNT(*) FROM user_progress_of_language_items p JOIN language_items li ON li.item_id = p.item_id WHERE li.course_id = %s",
            "DELETE FROM user_progress_of_language_items p USING language_items li WHERE li.item_id = p.item_id AND li.course_id = %s",
        ),
        (
            "review_logs",
            "SELECT COUNT(*) FROM review_logs WHERE course_id = %s",
            "DELETE FROM review_logs WHERE course_id = %s",
        ),
        (
            "user_courses",
            "SELECT COUNT(*) FROM user_courses WHERE course_id = %s",
            "DELETE FROM user_courses WHERE course_id = %s",
        ),
        (
            "user_progress_of_lessons",
            "SELECT COUNT(*) FROM user_progress_of_lessons WHERE course_id = %s",
            "DELETE FROM user_progress_of_lessons WHERE course_id = %s",
        ),
        (
            "vocabulary_knowledge",
            "SELECT COUNT(*) FROM vocabulary_knowledge WHERE course_id = %s",
            "DELETE FROM vocabulary_knowledge WHERE course_id = %s",
        ),
        (
            "language_items",
            "SELECT COUNT(*) FROM language_items WHERE course_id = %s",
            "DELETE FROM language_items WHERE course_id = %s",
        ),
        (
            "lessons",
            "SELECT COUNT(*) FROM lessons WHERE course_id = %s",
            "DELETE FROM lessons WHERE course_id = %s",
        ),
    ]

    try:
        for label, count_sql, delete_sql in steps:
            cur.execute(count_sql, (COURSE_ID,))
            count = cur.fetchone()[0]
            print(f"  {'[DRY]' if dry_run else '删除'} {label}: {count} 行")
            if not dry_run and count > 0:
                cur.execute(delete_sql, (COURSE_ID,))

        if not dry_run:
            conn.commit()
            print("  ✅ 数据库清理完成")
        else:
            conn.rollback()
    except Exception as e:
        conn.rollback()
        print(f"  ❌ 数据库错误: {e}")
        raise
    finally:
        conn.close()


def cleanup_r2(dry_run: bool) -> None:
    from services.storage.r2_storage import R2Storage
    print(f"\n── 3. R2 (前缀 {R2_PREFIX!r}) ──")
    storage = R2Storage.from_env()
    client = storage._get_client()

    paginator = client.get_paginator("list_objects_v2")
    keys = []
    for page in paginator.paginate(Bucket=storage.bucket, Prefix=R2_PREFIX):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])

    print(f"  找到 {len(keys)} 个对象")
    if not keys:
        return

    if dry_run:
        for k in keys[:10]:
            print(f"    [DRY] {k}")
        if len(keys) > 10:
            print(f"    ... 还有 {len(keys) - 10} 个")
        return

    BATCH = 1000
    deleted_total = 0
    for i in range(0, len(keys), BATCH):
        batch = keys[i : i + BATCH]
        resp = client.delete_objects(
            Bucket=storage.bucket,
            Delete={"Objects": [{"Key": k} for k in batch]},
        )
        deleted = len(resp.get("Deleted", []))
        errors = resp.get("Errors", [])
        deleted_total += deleted
        if errors:
            for err in errors:
                print(f"  ⚠️  删除失败: {err['Key']} — {err['Message']}")

    print(f"  ✅ R2 删除完成：共 {deleted_total} 个对象")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="预览，不实际删除")
    args = parser.parse_args()

    if args.dry_run:
        print("[DRY RUN] 预览模式，不会实际删除任何内容\n")
    else:
        print(f"!! 将永久删除 course_id={COURSE_ID} 的所有产物（本地 + DB + R2）\n")

    cleanup_local(args.dry_run)
    cleanup_db(args.dry_run)
    cleanup_r2(args.dry_run)

    print("\n[OK] 全部完成" if not args.dry_run else "\n[OK] DRY RUN 完成（未实际删除）")


if __name__ == "__main__":
    main()
