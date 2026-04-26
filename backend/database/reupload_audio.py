"""
reupload_audio.py — 补传遗漏的课文音频到 R2

用法（在 backend/ 目录下运行）：
    python database/reupload_audio.py              # 处理所有已归档课
    python database/reupload_audio.py 1101 1102    # 只处理指定课

针对场景：
    sync_to_db.py 入库成功，但本地音频路径在旧机器上（如 G:\\）无法找到，
    导致 R2 音频上传被跳过。本脚本重新定位文件并补传，同时更新 DB 中的
    lesson_audio_assets 字段。
"""

import json
import sys
import psycopg2
from pathlib import Path
from psycopg2.extras import Json
from dotenv import load_dotenv

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
sys.path.append(str(BACKEND_DIR))

load_dotenv(BACKEND_DIR / ".env")

from config.env import get_env

try:
    from database.connection import get_connection
except ImportError:
    from connection import get_connection

try:
    from services.storage.media_storage import get_media_storage
except ImportError:
    get_media_storage = None

ARTIFACTS_DIR = BACKEND_DIR / "content_builder" / "artifacts"
SYNCED_DIR    = ARTIFACTS_DIR / "synced_json" / "en"


def resolve_path(local_path: str) -> Path | None:
    """Try to locate an audio file regardless of which machine generated it."""
    if not local_path:
        return None
    p = Path(local_path)
    if p.exists():
        return p
    # Re-root by stripping everything before 'artifacts'
    parts = p.parts
    try:
        idx = next(i for i, part in enumerate(parts) if part.lower() == "artifacts")
        candidate = ARTIFACTS_DIR / Path(*parts[idx + 1:])
        if candidate.exists():
            return candidate
    except StopIteration:
        pass
    return None


def reupload_lesson(json_path: Path, r2) -> dict:
    """Upload missing audio for one lesson. Returns stats dict."""
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    lesson_audio = data.get("lesson_audio_assets", {})
    if not isinstance(lesson_audio, dict):
        return {"uploaded": 0, "missing": [], "skipped": 0}

    uploaded = 0
    missing  = []
    skipped  = 0

    def _upload_item(local_path: str, object_key: str, label: str) -> str | None:
        nonlocal uploaded, skipped
        p = resolve_path(local_path)
        if p is None:
            missing.append(local_path)
            return None
        if not object_key:
            skipped += 1
            return None
        try:
            result = r2.upload_file(str(p), object_key, content_type="audio/mpeg")
            print(f"    ☁️  [{label}] {object_key}")
            uploaded += 1
            return result.get("object_key", object_key)
        except Exception as e:
            print(f"    ⚠️  [{label}] 上传失败: {e}")
            return None

    # Sentence audio items
    for item in lesson_audio.get("items", []):
        if not isinstance(item, dict):
            continue
        local = (item.get("local_audio_file") or "").strip()
        key   = (item.get("object_key") or "").strip()
        new_key = _upload_item(local, key, f"line {item.get('line_ref', '?')}")
        if new_key:
            item["object_key"] = new_key

    # Full dialogue audio
    full = lesson_audio.get("full_audio", {})
    if isinstance(full, dict):
        local = (full.get("local_audio_file") or "").strip()
        key   = (full.get("object_key") or "").strip()
        new_key = _upload_item(local, key, "full_audio")
        if new_key:
            full["object_key"] = new_key

    return {"uploaded": uploaded, "missing": missing, "skipped": skipped, "data": data}


def update_db(data: dict):
    """Patch lesson_audio_assets in the lessons table."""
    meta = data.get("lesson_metadata", {})
    course_id = meta.get("course_id")
    lesson_id = meta.get("lesson_id")
    if not course_id or not lesson_id:
        return
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE lessons SET lesson_audio_assets = %s WHERE course_id = %s AND lesson_id = %s",
            (Json(data.get("lesson_audio_assets", {})), course_id, lesson_id),
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()


def main():
    if get_media_storage is None:
        print("❌ media_storage 不可用，请确认在 backend/ 目录下运行。")
        sys.exit(1)

    r2 = get_media_storage(optional=True)
    if not r2:
        print("❌ R2 未配置，无法上传。请检查 .env 中的 STORAGE_R2_* 配置。")
        sys.exit(1)

    filter_ids = set(sys.argv[1:])  # optional: restrict to given lesson IDs

    json_files = sorted(SYNCED_DIR.glob("*_data.json"))
    if not json_files:
        print(f"📭 {SYNCED_DIR} 下没有已归档的 JSON 文件。")
        sys.exit(0)

    if filter_ids:
        json_files = [f for f in json_files if any(lid in f.name for lid in filter_ids)]

    total_uploaded = 0
    all_missing: list[tuple[str, str]] = []  # (lesson, path)

    for json_path in json_files:
        lesson_name = json_path.stem
        print(f"\n📂 {lesson_name}")
        stats = reupload_lesson(json_path, r2)

        if "data" in stats and stats["uploaded"] > 0:
            # Write updated object_keys back to JSON
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(stats["data"], f, ensure_ascii=False, indent=2)
            update_db(stats["data"])
            print(f"   ✅ 上传 {stats['uploaded']} 个，数据库已更新")
        elif stats["uploaded"] == 0 and not stats["missing"]:
            print(f"   ⏭️  无需处理（已上传或无音频）")
        else:
            print(f"   ⏭️  上传 {stats['uploaded']} 个")

        for p in stats["missing"]:
            all_missing.append((lesson_name, p))
        total_uploaded += stats["uploaded"]

    print(f"\n{'='*50}")
    print(f"✅ 共上传 {total_uploaded} 个音频文件")

    if all_missing:
        print(f"\n⚠️  以下 {len(all_missing)} 个文件在本机上找不到，需要重新生成音频：")
        seen_lessons = set()
        for lesson, path in all_missing:
            if lesson not in seen_lessons:
                print(f"   • {lesson}")
                seen_lessons.add(lesson)
        print("\n对这些课重新生成音频，在 backend/content_builder/ 目录下运行：")
        print("   python generate.py <PDF路径>  # 重新跑 Stage 1（含音频）")
    else:
        print("🎉 所有音频均已找到并上传！")


if __name__ == "__main__":
    main()
