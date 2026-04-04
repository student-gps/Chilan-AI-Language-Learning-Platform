import os
import sys
import shutil
import json
from pathlib import Path
from dotenv import load_dotenv

# ==========================================
# 1. 跨目录导入设置
# ==========================================
# 获取当前脚本所在目录 (content_builder)
CURRENT_DIR = Path(__file__).resolve().parent
# 获取父目录 (backend)
BACKEND_DIR = CURRENT_DIR.parent

# 将 backend 目录加入系统路径，以便导入 database 文件夹下的模块
sys.path.append(str(BACKEND_DIR))

try:
    from database.connection import get_connection
except ImportError:
    print("❌ 导入失败: 无法找到 database.connection。请确保文件夹结构正确。")
    sys.exit(1)

# ==========================================
# 2. 路径配置初始化
# ==========================================
# 加载 .env (假设在 backend 目录下)
load_dotenv(BACKEND_DIR / ".env")

# 文件夹定义
RAW_MATERIALS_DIR = CURRENT_DIR / "raw_materials"
ARCHIVE_PDFS_DIR = CURRENT_DIR / "archive_pdfs"
SYNCED_JSON_DIR = CURRENT_DIR / "synced_json"
OUTPUT_JSON_DIR = CURRENT_DIR / "output_json"
OUTPUT_AUDIO_DIR = CURRENT_DIR / "output_audio"
VOCAB_MEMORY_FILE = CURRENT_DIR / "global_vocab_memory.json"

def reset_pipeline():
    print(f"🧹 [全系统重置] 正在清理测试数据...")
    print("---------------------------------------------")

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

    # --- 5. 数据库清空 (课程/题目/学习进度) ---
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
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

    print("---------------------------------------------")
    print("✨ [重置完成] 系统已恢复初始状态。")

if __name__ == "__main__":
    confirm = input("⚠️  注意：此操作将物理删除所有生成的 JSON、音频文件和数据库记录！确定继续？(y/n): ")
    if confirm.lower() == 'y':
        reset_pipeline()
    else:
        print("🚪 已取消操作。")
