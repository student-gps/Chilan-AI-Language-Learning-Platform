import os
import sys
import shutil
import json
from pathlib import Path
from dotenv import load_dotenv

# ==========================================
# 1. 跨目录导入设置
# ==========================================
# 获取当前脚本所在目录 (content_builder/scripts)
CURRENT_DIR = Path(__file__).resolve().parent
CONTENT_BUILDER_DIR = CURRENT_DIR.parent
ARTIFACTS_DIR = CONTENT_BUILDER_DIR / "artifacts"
# 获取父目录 (backend)
BACKEND_DIR = CONTENT_BUILDER_DIR.parent

# 将 backend 目录加入系统路径，以便导入 database 文件夹下的模块
sys.path.append(str(BACKEND_DIR))

try:
    from database.connection import get_connection
    from services.storage.media_storage import get_media_storage
except ImportError:
    print("❌ 导入失败: 无法找到 database.connection。请确保文件夹结构正确。")
    sys.exit(1)

# ==========================================
# 2. 路径配置初始化
# ==========================================
# 加载 .env (假设在 backend 目录下)
load_dotenv(BACKEND_DIR / ".env")

# 文件夹定义
RAW_MATERIALS_DIR = ARTIFACTS_DIR / "raw_materials"
ARCHIVE_PDFS_DIR = ARTIFACTS_DIR / "archive_pdfs"
SYNCED_JSON_DIR = ARTIFACTS_DIR / "synced_json" / "en"
OUTPUT_JSON_DIR = ARTIFACTS_DIR / "output_json" / "en"
OUTPUT_AUDIO_DIR = ARTIFACTS_DIR / "output_audio"
OUTPUT_VIDEO_DIR = ARTIFACTS_DIR / "output_video"
VOCAB_MEMORY_FILE = ARTIFACTS_DIR / "vocab_memory" / "global_vocab_memory.json"

def _extract_object_keys(payload):
    keys = set()

    def walk(value):
        if isinstance(value, dict):
            object_key = value.get("object_key")
            if isinstance(object_key, str) and object_key.strip():
                keys.add(object_key.strip())
            for nested in value.values():
                walk(nested)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)
    return keys


def _collect_local_object_keys():
    keys = set()
    for folder in [OUTPUT_JSON_DIR, SYNCED_JSON_DIR]:
        if not folder.exists():
            continue
        for json_file in folder.glob("*_data.json"):
            try:
                payload = json.loads(json_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            keys.update(_extract_object_keys(payload))
    return keys


def _collect_db_object_keys(cur):
    keys = set()
    try:
        cur.execute("""
            SELECT lesson_audio_assets, explanation_video_urls,
                   video_render_plan, video_plan
            FROM lessons
        """)
        rows = cur.fetchall()
    except Exception:
        return keys

    for row in rows:
        if isinstance(row, dict):
            for col in ("lesson_audio_assets", "explanation_video_urls",
                        "video_render_plan", "video_plan"):
                payload = row.get(col)
                if isinstance(payload, dict):
                    keys.update(_extract_object_keys(payload))
        elif isinstance(row, (list, tuple)):
            for payload in row:
                if isinstance(payload, dict):
                    keys.update(_extract_object_keys(payload))
    return keys


def _purge_media_objects(object_keys):
    if not object_keys:
        print("ℹ️ 未检测到需要删除的 COS 媒体对象。")
        return

    storage = get_media_storage(optional=True)
    if not storage:
        print("⚠️ 未配置 STORAGE_R2_* 环境变量，跳过云端媒体清理。")
        return

    deleted = 0
    failed = 0
    print(f"☁️ 正在清理 R2 媒体对象，共 {len(object_keys)} 个...")
    for object_key in sorted(object_keys):
        try:
            storage.delete_object(object_key)
            deleted += 1
        except Exception as e:
            failed += 1
            print(f"⚠️ R2 删除失败: {object_key} | {e}")

    print(f"✅ R2 清理完成：成功 {deleted} 个，失败 {failed} 个。")


def reset_pipeline(with_cos: bool = True):
    print(f"🧹 [全系统重置] 正在清理测试数据...")
    print(f"☁️ 云端媒体清理: {'开启' if with_cos else '关闭'}")
    print("---------------------------------------------")

    local_object_keys = _collect_local_object_keys() if with_cos else set()

    # --- 1. 删除本地词汇记忆库 ---
    if VOCAB_MEMORY_FILE.exists():
        VOCAB_MEMORY_FILE.unlink()
        print(f"✅ 已删除生词记忆库: {VOCAB_MEMORY_FILE.name}")
    else:
        print(f"ℹ️ 未发现记忆库文件，跳过。")

    # --- 2. 还原 PDF 文件 (从归档移回原材料区) ---
    if ARCHIVE_PDFS_DIR.exists():
        pdf_files = list(ARCHIVE_PDFS_DIR.glob("*.pdf"))
        if pdf_files:
            RAW_MATERIALS_DIR.mkdir(parents=True, exist_ok=True)
            for pdf in pdf_files:
                shutil.move(str(pdf), str(RAW_MATERIALS_DIR / pdf.name))
            print(f"✅ 已将 {len(pdf_files)} 个 PDF 还原至 raw_materials。")
        else:
            print("ℹ️ archive_pdfs 文件夹为空，无需还原。")
    else:
        # 如果你还没手动建立这个文件夹，先创建一个空的防报错
        ARCHIVE_PDFS_DIR.mkdir(exist_ok=True)

    # --- 3. 清理所有 JSON 文件夹 ---
    for folder in [SYNCED_JSON_DIR, OUTPUT_JSON_DIR]:
        if folder.exists():
            json_files = list(folder.glob("*.json"))
            for j_file in json_files:
                j_file.unlink()
            print(f"✅ 已排空文件夹: {folder.name} (删除了 {len(json_files)} 个文件)")

    # --- 4. 清理所有课文音频产物 ---
    if OUTPUT_AUDIO_DIR.exists():
        lesson_dirs = [p for p in OUTPUT_AUDIO_DIR.iterdir() if p.is_dir()]
        loose_files = [p for p in OUTPUT_AUDIO_DIR.iterdir() if p.is_file()]

        for lesson_dir in lesson_dirs:
            shutil.rmtree(lesson_dir, ignore_errors=True)
        for audio_file in loose_files:
            audio_file.unlink(missing_ok=True)

        print(
            f"✅ 已清理音频产物目录: {OUTPUT_AUDIO_DIR.name} "
            f"(删除了 {len(lesson_dirs)} 个子目录, {len(loose_files)} 个散落文件)"
        )
    OUTPUT_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    # --- 5. 清理所有讲解视频产物 ---
    if OUTPUT_VIDEO_DIR.exists():
        video_files = [p for p in OUTPUT_VIDEO_DIR.iterdir() if p.is_file()]
        video_dirs = [p for p in OUTPUT_VIDEO_DIR.iterdir() if p.is_dir()]

        for video_file in video_files:
            video_file.unlink(missing_ok=True)
        for video_dir in video_dirs:
            shutil.rmtree(video_dir, ignore_errors=True)

        print(
            f"✅ 已清理视频产物目录: {OUTPUT_VIDEO_DIR.name} "
            f"(删除了 {len(video_files)} 个文件, {len(video_dirs)} 个子目录)"
        )
    OUTPUT_VIDEO_DIR.mkdir(parents=True, exist_ok=True)

    # --- 6. 数据库清空 (课程/题目/学习进度) ---
    conn = None
    cur = None
    db_object_keys = set()
    try:
        conn = get_connection()
        cur = conn.cursor()

        if with_cos:
            db_object_keys = _collect_db_object_keys(cur)

        print("🎯 正在清空数据库表 [lessons]、[language_items]、[vocabulary_knowledge]、[user_progress_of_lessons] 和 [user_progress_of_language_items]...")
        # TRUNCATE 是最干净的方式，RESTART IDENTITY 会让自增 ID 回到 1
        cur.execute(
            "TRUNCATE TABLE user_progress_of_language_items, "
            "user_progress_of_lessons, "
            "vocabulary_knowledge, "
            "language_items, "
            "lessons "
            "RESTART IDENTITY CASCADE;"
        )
        
        conn.commit()
        print("✅ 数据库课程表、题目表与学习进度表已完全清空，自增 ID 已重置。")
        
    except Exception as e:
        print(f"❌ 数据库清理失败: {e}")
        if conn: conn.rollback()
    finally:
        if cur: cur.close()
        if conn: conn.close()

    if with_cos:
        _purge_media_objects(local_object_keys.union(db_object_keys))

    print("---------------------------------------------")
    print("✨ [重置完成] 系统已恢复初始状态。")


def reset_narration():
    """仅清除 Stage 2 旁白音轨产物（*_narration/ 目录），保留 Stage 1 内容不动。"""
    print("🎙️ [旁白重置] 正在清理旁白音轨产物...")
    print("---------------------------------------------")

    if not OUTPUT_AUDIO_DIR.exists():
        print("ℹ️ output_audio 目录不存在，无需清理。")
        return

    narration_dirs = [p for p in OUTPUT_AUDIO_DIR.iterdir() if p.is_dir() and p.name.endswith("_narration")]
    if not narration_dirs:
        print("ℹ️ 未发现旁白音轨目录，无需清理。")
        return

    for d in narration_dirs:
        shutil.rmtree(d, ignore_errors=True)

    print(f"✅ 已清除 {len(narration_dirs)} 个旁白目录: {', '.join(d.name for d in narration_dirs)}")
    print("---------------------------------------------")
    print("✨ [旁白重置完成] Stage 1 内容保持不变，可重新运行 render_narration.py。")


if __name__ == "__main__":
    print("=" * 48)
    print("  🧹 Content Builder 重置工具")
    print("=" * 48)
    print()
    print("  [1] 全量重置（含 COS 云端媒体）")
    print("      清除: JSON / 音频 / 视频 / 数据库 / COS")
    print()
    print("  [2] 全量重置（跳过 COS）")
    print("      清除: JSON / 音频 / 视频 / 数据库")
    print()
    print("  [3] 仅重置旁白（Stage 2）")
    print("      清除: output_audio/*_narration/ 目录")
    print()
    print("  [0] 取消")
    print()

    choice = input("  请输入选项: ").strip()

    if choice == "0" or choice == "":
        print("🚪 已取消操作。")
    elif choice == "1":
        confirm = input("⚠️  将物理删除所有 JSON、音频、视频、数据库记录及 COS 媒体对象！确定继续？(y/n): ")
        if confirm.lower() == "y":
            reset_pipeline(with_cos=True)
        else:
            print("🚪 已取消操作。")
    elif choice == "2":
        confirm = input("⚠️  将物理删除所有 JSON、音频、视频及数据库记录！确定继续？(y/n): ")
        if confirm.lower() == "y":
            reset_pipeline(with_cos=False)
        else:
            print("🚪 已取消操作。")
    elif choice == "3":
        confirm = input("⚠️  将删除所有旁白音轨目录（*_narration/），Stage 1 内容保持不变。确定继续？(y/n): ")
        if confirm.lower() == "y":
            reset_narration()
        else:
            print("🚪 已取消操作。")
    else:
        print("❌ 无效选项，已退出。")
