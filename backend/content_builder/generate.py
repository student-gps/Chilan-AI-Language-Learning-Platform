import sys
import json
import time
import re
import shutil
import argparse
from pathlib import Path

# Force unbuffered stdout so terminal output never appears to freeze
sys.stdout.reconfigure(line_buffering=True)
from dotenv import load_dotenv

from core.paths import default_paths
from core.pipeline import get_pipeline


def main():
    parser = argparse.ArgumentParser(description="Run the content builder pipeline for raw lesson PDFs.")
    parser.add_argument(
        "--pipeline",
        default="integrated_chinese",
        help="教材流水线 ID（默认: integrated_chinese）。",
    )
    args = parser.parse_args()

    # 1. 绝对路径配置
    paths = default_paths()
    BASE_DIR = paths.backend_dir

    # 向上寻找 backend/.env 文件
    load_dotenv(dotenv_path=BASE_DIR / ".env")
    pipeline = get_pipeline(args.pipeline)

    # 2. 引擎初始化
    try:
        provider = pipeline.create_provider()
        agent = pipeline.create_agent(provider=provider, memory_dir=pipeline.artifact_root(paths))
        print(f"🔧 当前激活模型引擎: {type(provider).__name__}")
        print(f"🧭 当前内容流水线: {pipeline.display_name} ({pipeline.pipeline_id})")
    except Exception as e:
        print(f"❌ 系统初始化失败: {e}")
        return

    # 3. 文件夹管理
    raw_dir = pipeline.raw_materials_dir(paths)
    output_dir = pipeline.output_json_dir(paths, pipeline.default_output_lang)
    archive_dir = pipeline.archive_pdfs_dir(paths)
    
    for d in [raw_dir, output_dir, archive_dir]:
        d.mkdir(parents=True, exist_ok=True)
    
    # 4. 扫描执行
    pdf_files = list(raw_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"📭 raw_materials 为空，没有需要处理的 PDF。")
        return

    def extract_lesson_id(pdf_path: Path):
        numbers = re.findall(r'\d+', pdf_path.stem)
        return int(numbers[0]) if numbers else float("inf")

    pdf_files = sorted(pdf_files, key=extract_lesson_id)

    print(f"📦 发现 {len(pdf_files)} 个新教材准备处理！\n" + "="*45)

    for pdf_path in pdf_files:
        file_name = pdf_path.stem
        numbers = re.findall(r'\d+', file_name)
        if not numbers:
            print(f"⚠️ 警告：无法从文件名 {file_name} 提取编号，跳过。")
            continue
            
        lesson_id = int(numbers[0])

        # ── Stage 1：语言无关内容生成 ──────────────────────────────
        result = agent.generate_content(str(pdf_path), lesson_id=lesson_id)

        if result is None:
            print(f"\n🛑 [严重错误] {file_name}.pdf 处理失败！")
            print("为了防止后续数据产生连锁反应，程序已自动终止。请排查报错原因后再重新运行。")
            return

        if result:
            output_file = output_dir / f"lesson{lesson_id}_data.json"

            # Stage 1 落盘（Stage 2 render_narration.py 从磁盘读取此 JSON）
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"✅ Stage 1 完成: {output_file.name}")
            
            # PDF 归档
            try:
                archive_path = archive_dir / pdf_path.name
                if archive_path.exists():
                    archive_path = archive_dir / f"{pdf_path.stem}_{int(time.time())}.pdf"
                shutil.move(str(pdf_path), str(archive_path))
                print(f"📁 教材已安全归档。")
            except Exception as e:
                print(f"⚠️ 归档文件时发生错误: {e}")
        else:
            print(f"❌ {file_name}.pdf 处理失败，保留在原处等待排查。")
        
        print("-" * 45)

if __name__ == "__main__":
    main()
