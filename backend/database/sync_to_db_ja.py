"""
sync_to_db_ja.py — 将「大家的日本语」日语课程产物上传到 R2 并同步至 PostgreSQL。

课程编码：
  303 = 目标语言日语(3) + 学习语言中文(3)

用法（在项目根目录或 backend/ 目录下运行）：

    python backend/database/sync_to_db_ja.py --lang zh

    python backend/database/sync_to_db_ja.py --lang zh \
        backend/content_builder/ja/minna_no_nihongo/artifacts/output_json/zh/lesson001_data.json

同步后 JSON 会从 output_json/<lang>/ 移至 synced_json/<lang>/。
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv


CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

load_dotenv(BACKEND_DIR / ".env")

from content_builder.core.paths import default_paths
from content_builder.core.pipeline import get_pipeline
from database.connection import get_connection
from database.sync_to_db import EmbeddingFactory, sync_lesson_data, upload_assets_to_r2


MNN_PIPELINE_ID = "minna_no_nihongo"
DEFAULT_COURSE_ID = 303
DEFAULT_LANG = "zh"
DEFAULT_COURSE_SLUG = "minna_no_nihongo_1_zh"
DEFAULT_COURSE_NAME = "用中文学习大家的日本语"
DEFAULT_CATEGORY = "CN_TO_JA"
DEFAULT_TARGET_LANGUAGE = "japanese"
DEFAULT_SOURCE_LANGUAGE = "chinese"


def ensure_japanese_course(course_id: int) -> None:
    """Create/update the course row used by the formal Japanese-learning flow."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO courses (course_id, name, category, target_language, source_language)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (course_id)
            DO UPDATE SET
                name = EXCLUDED.name,
                category = EXCLUDED.category,
                target_language = EXCLUDED.target_language,
                source_language = EXCLUDED.source_language
            """,
            (
                course_id,
                DEFAULT_COURSE_NAME,
                DEFAULT_CATEGORY,
                DEFAULT_TARGET_LANGUAGE,
                DEFAULT_SOURCE_LANGUAGE,
            ),
        )
        cur.execute("SELECT setval('courses_course_id_seq', (SELECT MAX(course_id) FROM courses))")
        conn.commit()
        print(f"✅ course 已就绪: {course_id} {DEFAULT_CATEGORY} ({DEFAULT_COURSE_NAME})")
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def prepare_mnn_lesson_data(data: dict, *, course_id: int, lang: str) -> dict:
    """Normalize formal DB identity without changing generated lesson content."""
    data["pipeline_id"] = MNN_PIPELINE_ID
    data["target_language"] = "ja"
    data["support_language"] = lang

    metadata = data.get("lesson_metadata")
    if not isinstance(metadata, dict):
        metadata = {}
        data["lesson_metadata"] = metadata

    old_course_id = metadata.get("course_id")
    old_course_digits = int(str(old_course_id)) if str(old_course_id).isdigit() else None
    if old_course_id not in {None, ""} and old_course_digits != course_id:
        metadata.setdefault("source_course_id", old_course_id)
    metadata["course_id"] = course_id
    metadata["course_slug"] = DEFAULT_COURSE_SLUG
    metadata["target_language"] = "ja"
    metadata["source_language"] = lang
    metadata["support_language"] = lang

    for item in data.get("database_items", []) if isinstance(data.get("database_items"), list) else []:
        if isinstance(item, dict):
            item["course_id"] = course_id
    return data


def find_json_files(files: list[str], *, lang: str) -> tuple[list[Path], Path]:
    pipeline = get_pipeline(MNN_PIPELINE_ID)
    paths = default_paths()
    artifact_root = pipeline.artifact_root(paths)
    output_dir = artifact_root / "output_json" / lang
    synced_dir = artifact_root / "synced_json" / lang
    synced_dir.mkdir(parents=True, exist_ok=True)

    if files:
        return [Path(item) for item in files], synced_dir

    by_name = {path.name: path for path in synced_dir.glob("*_data*.json")}
    by_name.update({path.name: path for path in output_dir.glob("*_data*.json")})
    json_files = list(by_name.values())
    if json_files and not list(output_dir.glob("*_data*.json")) and synced_dir.exists():
        print(f"ℹ️ 未在 {output_dir} 找到 JSON，改用已同步目录重刷: {synced_dir}")
    return json_files, synced_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync Minna no Nihongo lesson JSON files to DB/R2.")
    parser.add_argument("files", nargs="*", help="Specific MNN lesson JSON file(s) to sync.")
    parser.add_argument("--lang", default=DEFAULT_LANG, help="Support language folder, default: zh.")
    parser.add_argument("--course-id", type=int, default=DEFAULT_COURSE_ID, help="Formal course_id, default: 303.")
    parser.add_argument("--skip-upload", action="store_true", help="Skip R2 upload and only sync DB rows.")
    args = parser.parse_args()

    lang = (args.lang or DEFAULT_LANG).strip().lower()
    json_files, synced_dir = find_json_files(args.files, lang=lang)
    if not json_files:
        print("📭 没有待处理的 MNN JSON 文件。")
        return

    ensure_japanese_course(args.course_id)
    embed_provider = EmbeddingFactory.create_provider()

    sync_context = {
        "pipeline": MNN_PIPELINE_ID,
        "lang": lang,
        "course_id": args.course_id,
        "course_slug": DEFAULT_COURSE_SLUG,
        "target_language": "ja",
        "source_language": lang,
        "support_language": lang,
    }

    failed: list[str] = []
    for target_json in json_files:
        print(f"\n🚀 [MNN JA Sync] 开始处理: {target_json.name}")
        with target_json.open(encoding="utf-8") as f:
            lesson_data = json.load(f)

        lesson_data = prepare_mnn_lesson_data(lesson_data, course_id=args.course_id, lang=lang)
        if not args.skip_upload:
            print("☁️ 上传本地资产到 R2...")
            lesson_data = upload_assets_to_r2(lesson_data)

        with target_json.open("w", encoding="utf-8") as f:
            json.dump(lesson_data, f, ensure_ascii=False, indent=2)

        if sync_lesson_data(str(target_json), embed_provider, sync_context=sync_context):
            destination = synced_dir / target_json.name
            if target_json.resolve() != destination.resolve():
                shutil.move(str(target_json), str(destination))
                print(f"📦 已归档到: {destination}")
        else:
            failed.append(target_json.name)
            break

    if failed:
        raise SystemExit(f"❌ MNN JA sync failed for: {', '.join(failed)}")


if __name__ == "__main__":
    main()
