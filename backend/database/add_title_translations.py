"""
add_title_translations.py — 为课程 JSON 补填 title_localized 字段

用法（在 backend/ 目录下运行）：
    # 英文已入库课（synced_json/en/），同时更新 DB
    python database/add_title_translations.py

    # 法语未入库课（output_json/fr/），只更新 JSON，不动 DB
    python database/add_title_translations.py --lang fr

    # 指定课号
    python database/add_title_translations.py --lang fr 101 102
"""

import argparse
import json
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
sys.path.append(str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

ARTIFACTS_DIR = BACKEND_DIR / "content_builder" / "artifacts"

LANG_META = {
    "en": {"name": "English",  "dir": ARTIFACTS_DIR / "synced_json" / "en", "update_db": True},
    "fr": {"name": "French",   "dir": ARTIFACTS_DIR / "output_json"  / "fr", "update_db": False},
    "de": {"name": "German",   "dir": ARTIFACTS_DIR / "output_json"  / "de", "update_db": False},
    "es": {"name": "Spanish",  "dir": ARTIFACTS_DIR / "output_json"  / "es", "update_db": False},
    "ja": {"name": "Japanese", "dir": ARTIFACTS_DIR / "output_json"  / "ja", "update_db": False},
    "ko": {"name": "Korean",   "dir": ARTIFACTS_DIR / "output_json"  / "ko", "update_db": False},
}


def _build_translate_prompt(lang_name: str, titles: list[dict]) -> str:
    payload = json.dumps(titles, ensure_ascii=False)
    return f"""你是一名中文教材标题翻译专家。请将以下中文课程标题翻译成{lang_name}，输出 JSON 数组。

待翻译标题列表：
{payload}

【翻译要求】
- 每项必须包含 lesson_id 原样返回（用于对应）
- 每项必须包含 title_localized 字段，值为{lang_name}翻译字符串
- 翻译应简短自然，适合教学标题（3-6个词）
- 保持含义准确，不要过度意译

【输出结构】
[
  {{
    "lesson_id": 101,
    "title_localized": "..."
  }}
]
"""


def _get_llm():
    from content_builder.llm_providers import LLMFactory
    return LLMFactory.create_provider()


def _update_db(course_id: int, lesson_id: int, lesson_metadata: dict):
    from psycopg2.extras import Json
    try:
        from database.connection import get_connection
    except ImportError:
        from connection import get_connection
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE lessons SET lesson_metadata = %s WHERE course_id = %s AND lesson_id = %s",
            (Json(lesson_metadata), course_id, lesson_id),
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default="en", choices=list(LANG_META.keys()),
                        help="目标语言码（默认 en）")
    parser.add_argument("lesson_ids", nargs="*", help="可选：指定课号，如 101 102")
    args = parser.parse_args()

    lang = args.lang
    meta = LANG_META[lang]
    json_dir: Path = meta["dir"]
    update_db: bool = meta["update_db"]
    lang_name: str = meta["name"]

    if not json_dir.exists():
        print(f"📭 目录不存在：{json_dir}")
        sys.exit(0)

    json_files = sorted(json_dir.glob("*_data*.json"))
    if not json_files:
        print(f"📭 {json_dir} 下没有 JSON 文件。")
        sys.exit(0)

    if args.lesson_ids:
        filter_ids = set(args.lesson_ids)
        json_files = [f for f in json_files if any(lid in f.name for lid in filter_ids)]

    needs_update = []
    for json_path in json_files:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        lesson_meta = data.get("lesson_metadata", {})
        if lesson_meta.get("title_localized"):
            print(f"⏭️  {json_path.stem} — 已有 title_localized，跳过")
            continue
        needs_update.append({
            "json_path": json_path,
            "lesson_id": lesson_meta.get("lesson_id"),
            "course_id": lesson_meta.get("course_id"),
            "title": lesson_meta.get("title", ""),
            "data": data,
        })

    if not needs_update:
        print("\n🎉 所有课程均已有 title_localized，无需处理。")
        return

    print(f"\n📋 共 {len(needs_update)} 课需要补填 title_localized（→ {lang_name}）：")
    for item in needs_update:
        print(f"   • lesson {item['lesson_id']}: {item['title']}")

    print(f"\n🤖 正在调用 LLM 批量翻译 {len(needs_update)} 个标题...")
    llm = _get_llm()
    prompt_payload = [{"lesson_id": item["lesson_id"], "title": item["title"]} for item in needs_update]
    result = llm.generate_structured_json(_build_translate_prompt(lang_name, prompt_payload))

    if not isinstance(result, list):
        print(f"❌ LLM 返回格式异常: {type(result)}")
        sys.exit(1)

    translations_map: dict[int, str] = {}
    for r in result:
        if isinstance(r, dict) and r.get("lesson_id") and r.get("title_localized"):
            translations_map[int(r["lesson_id"])] = r["title_localized"]

    updated = 0
    for item in needs_update:
        lid = item["lesson_id"]
        localized = translations_map.get(lid)
        if not localized:
            print(f"  ⚠️  lesson {lid} ({item['title']}) — LLM 未返回翻译，跳过")
            continue

        data = item["data"]
        lm = data.setdefault("lesson_metadata", {})
        lm["title_localized"] = localized

        with open(item["json_path"], "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        if update_db:
            _update_db(item["course_id"], lid, lm)
            print(f"  ✅ lesson {lid} ({item['title']}) → {localized}  [JSON + DB]")
        else:
            print(f"  ✅ lesson {lid} ({item['title']}) → {localized}  [JSON only]")
        updated += 1

    print(f"\n{'='*50}")
    suffix = "（JSON + DB）" if update_db else "（仅 JSON，入库时会同步到 DB）"
    print(f"✅ 共更新 {updated} / {len(needs_update)} 课的 title_localized {suffix}")


if __name__ == "__main__":
    main()
