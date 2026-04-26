"""
repatch_dialogue_audio.py — 只对已入库课程中"使用了默认音色"的对话行进行补录

用法（在 backend/ 目录下运行）：
    python database/repatch_dialogue_audio.py              # 处理所有已归档课
    python database/repatch_dialogue_audio.py 901 902      # 只处理指定课

流程：
  1. 扫描 synced_json/en/，找出 voice_type == DEFAULT_VOICE 且角色已在新映射表里的句子
  2. 只重新合成这些句子的音频，替换本地文件
  3. 重新拼接该课的 full_dialogue audio
  4. 上传修改过的句子音频 + 新 full audio 到 R2
  5. 更新 JSON 文件 + DB 中的 lesson_audio_assets
"""

import json
import sys
import base64
from pathlib import Path
from psycopg2.extras import Json

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
sys.path.append(str(BACKEND_DIR))
sys.path.append(str(BACKEND_DIR / "content_builder"))
sys.path.append(str(BACKEND_DIR / "content_builder" / "tasks"))

from dotenv import load_dotenv
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

from tasks.dialogue_audio import Task4BLessonAudioRenderer

ARTIFACTS_DIR = BACKEND_DIR / "content_builder" / "artifacts"
SYNCED_DIR    = ARTIFACTS_DIR / "synced_json" / "en"


def _resolve_path(local_path: str) -> Path | None:
    if not local_path:
        return None
    p = Path(local_path)
    if p.exists():
        return p
    parts = p.parts
    try:
        idx = next(i for i, part in enumerate(parts) if part.lower() == "artifacts")
        candidate = ARTIFACTS_DIR / Path(*parts[idx + 1:])
        if candidate.exists():
            return candidate
    except StopIteration:
        pass
    return None


def _update_db(course_id: int, lesson_id: int, lesson_audio_assets: dict):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE lessons SET lesson_audio_assets = %s WHERE course_id = %s AND lesson_id = %s",
            (Json(lesson_audio_assets), course_id, lesson_id),
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()


def repatch_lesson(json_path: Path, renderer: Task4BLessonAudioRenderer, r2) -> dict:
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    meta         = data.get("lesson_metadata", {})
    lesson_id    = meta.get("lesson_id")
    course_id    = meta.get("course_id")
    audio_assets = data.get("lesson_audio_assets", {})

    if not isinstance(audio_assets, dict):
        return {"patched": 0, "skipped": 0}

    items = audio_assets.get("items", [])
    if not isinstance(items, list):
        return {"patched": 0, "skipped": 0}

    default_voice = renderer.voice_type  # 501002
    patched_items = []
    all_sentence_files: list[Path] = []

    for item in items:
        if not isinstance(item, dict):
            all_sentence_files.append(None)
            continue

        role       = (item.get("role") or "").strip()
        voice_used = item.get("voice_type")
        correct_voice = renderer.role_voice_map.get(role, default_voice)

        # Resolve current local file path
        local_file = _resolve_path(item.get("local_audio_file", ""))

        # Only repatch if: used default AND correct voice is now different AND we have the file location
        if voice_used == default_voice and correct_voice != default_voice:
            source_text = item.get("source_text") or item.get("hanzi", "")
            line_ref    = item.get("line_ref", "?")

            # Determine output path (use existing dir if possible, else derive from object_key)
            if local_file:
                out_path = local_file
            else:
                obj_key  = item.get("object_key", "")
                filename = Path(obj_key).name if obj_key else f"lesson{lesson_id}_line{line_ref}.mp3"
                out_dir  = ARTIFACTS_DIR / "output_audio" / f"lesson{lesson_id}"
                out_dir.mkdir(parents=True, exist_ok=True)
                out_path = out_dir / filename

            print(f"  🎙️  line {line_ref} | role={role!r} | {voice_used} → {correct_voice}: {source_text[:30]}")
            try:
                response = renderer._text_to_voice(
                    text=source_text,
                    session_id=f"repatch-{lesson_id}-line-{line_ref}",
                    voice_type=correct_voice,
                )
                audio_b64 = response.get("Audio", "")
                if not audio_b64:
                    raise RuntimeError("API 未返回音频数据")
                out_path.write_bytes(base64.b64decode(audio_b64))

                # Update item fields
                item["voice_type"]      = correct_voice
                item["local_audio_file"] = str(out_path)
                duration = renderer._probe_audio_duration_seconds(out_path)
                item["duration_seconds"] = round(duration, 3)

                patched_items.append((item, out_path))
            except Exception as e:
                print(f"    ⚠️  合成失败: {e}")

        if local_file and local_file.exists():
            all_sentence_files.append(local_file)
        elif item.get("local_audio_file"):
            resolved = _resolve_path(item["local_audio_file"])
            all_sentence_files.append(resolved if resolved else None)
        else:
            all_sentence_files.append(None)

    if not patched_items:
        return {"patched": 0, "skipped": len(items)}

    # Re-compose full dialogue audio from all sentence files (skip None entries)
    valid_files = [f for f in all_sentence_files if f and f.exists()]
    full_audio_filename = f"lesson{lesson_id}_full_dialogue.mp3"
    full_audio_dir  = ARTIFACTS_DIR / "output_audio" / f"lesson{lesson_id}"
    full_audio_dir.mkdir(parents=True, exist_ok=True)
    full_audio_path = full_audio_dir / full_audio_filename

    new_full = renderer._compose_full_lesson_audio(valid_files, full_audio_path)
    if new_full:
        print(f"  🔗 已重新拼接 full_dialogue audio ({len(valid_files)} 句)")

    # Upload patched sentence files to R2
    uploaded = 0
    if r2:
        for item, out_path in patched_items:
            obj_key = item.get("object_key", "")
            if obj_key and out_path.exists():
                try:
                    r2.upload_file(str(out_path), obj_key, content_type="audio/mpeg")
                    print(f"    ☁️  上传 {obj_key}")
                    uploaded += 1
                except Exception as e:
                    print(f"    ⚠️  上传失败: {e}")

        # Upload new full audio
        if new_full:
            full_key = audio_assets.get("full_audio", {}).get("object_key", "")
            if not full_key:
                lesson_folder = f"lesson{lesson_id}"
                full_key = f"zh/audio/{lesson_folder}/full/{full_audio_filename}"
            try:
                r2.upload_file(str(new_full), full_key, content_type="audio/mpeg")
                print(f"    ☁️  上传 full audio → {full_key}")
                # Update full_audio entry
                full_audio_entry = audio_assets.get("full_audio", {})
                if isinstance(full_audio_entry, dict):
                    full_audio_entry["local_audio_file"] = str(new_full)
                    full_audio_entry["object_key"]       = full_key
                    full_audio_duration = renderer._probe_audio_duration_seconds(new_full)
                    full_audio_entry["duration_seconds"] = round(full_audio_duration, 3)
                    full_audio_entry["status"]           = "ready"
                    audio_assets["full_audio"]           = full_audio_entry
            except Exception as e:
                print(f"    ⚠️  full audio 上传失败: {e}")

    # Write back JSON
    data["lesson_audio_assets"] = audio_assets
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Update DB
    _update_db(course_id, lesson_id, audio_assets)
    print(f"  ✅ 补录 {len(patched_items)} 句，上传 {uploaded} 个，数据库已更新")

    return {"patched": len(patched_items), "skipped": len(items) - len(patched_items)}


def main():
    renderer = Task4BLessonAudioRenderer()
    renderer._require_credentials()

    r2 = None
    if get_media_storage:
        r2 = get_media_storage(optional=True)
        if not r2:
            print("⚠️  R2 未配置，将只更新本地文件和数据库，不上传。")

    filter_ids = set(sys.argv[1:])
    json_files = sorted(SYNCED_DIR.glob("*_data.json"))
    if filter_ids:
        json_files = [f for f in json_files if any(lid in f.name for lid in filter_ids)]

    default_voice = renderer.voice_type
    role_map = renderer.role_voice_map

    # Pre-screen: only process lessons that actually have patchable items
    targets = []
    for json_path in json_files:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        items = data.get("lesson_audio_assets", {}).get("items", [])
        needs_patch = any(
            isinstance(it, dict)
            and it.get("voice_type") == default_voice
            and role_map.get((it.get("role") or "").strip(), default_voice) != default_voice
            for it in items
        )
        if needs_patch:
            targets.append(json_path)

    if not targets:
        print("✅ 没有需要补录的句子。")
        return

    print(f"📋 共 {len(targets)} 课需要补录：{[f.stem for f in targets]}\n")

    total_patched = 0
    for json_path in targets:
        print(f"\n📂 {json_path.stem}")
        stats = repatch_lesson(json_path, renderer, r2)
        total_patched += stats["patched"]

    print(f"\n{'='*50}")
    print(f"✅ 共补录 {total_patched} 条对话音频")


if __name__ == "__main__":
    main()
