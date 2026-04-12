import os
import sys
import json
import time
import re
import shutil
import subprocess
import argparse
from pathlib import Path

# Force unbuffered stdout so terminal output never appears to freeze
sys.stdout.reconfigure(line_buffering=True)
from dotenv import load_dotenv

# 引入我们刚才拆分好的工厂和总代理
from llm_providers import LLMFactory
from content_agent import ContentCreatorAgent

def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def render_explanation_video(base_dir: Path, lesson_id: int, lesson_data: dict | None = None) -> dict:
    """
    Render the explanation video, merge narration audio, and upload to COS.

    Returns:
        {
            "cos_url":        str,   # public/signed COS URL (empty if upload failed or COS not configured)
            "cos_object_key": str,   # COS object key
            "local_path":     str,   # absolute local path to the final mp4
        }
    """
    result = {"cos_url": "", "cos_object_key": "", "local_path": ""}

    frontend_dir = base_dir.parent / "frontend"
    render_script = frontend_dir / "scripts" / "render-explanation-video.mjs"

    if not frontend_dir.exists() or not render_script.exists():
        print(f"⚠️ 未找到前端 Remotion 渲染脚本，跳过 lesson{lesson_id} 讲解视频渲染。")
        return result

    output_dir = base_dir / "content_builder" / "output_video"
    output_dir.mkdir(parents=True, exist_ok=True)
    silent_video = output_dir / f"lesson{lesson_id}_explanation.mp4"

    print(f"🎞️ 开始渲染 lesson{lesson_id} 教学讲解视频（无声）...")
    try:
        subprocess.run(
            ["node", str(render_script), str(lesson_id)],
            cwd=str(frontend_dir),
            check=True,
        )
        print(f"✅ lesson{lesson_id} 无声视频渲染完成。")
    except FileNotFoundError:
        print("⚠️ 当前环境缺少 node 命令，跳过讲解视频渲染。")
        return result
    except subprocess.CalledProcessError as e:
        print(f"⚠️ lesson{lesson_id} 讲解视频渲染失败（退出码 {e.returncode}），已跳过。")
        return result

    # Merge narration audio if available
    narration_info = (lesson_data or {}).get("explanation_narration_audio", {})
    narration_file = narration_info.get("audio_file", "") if narration_info.get("status") == "ok" else ""

    if narration_file and Path(narration_file).exists() and silent_video.exists():
        final_video = output_dir / f"lesson{lesson_id}_explanation_final.mp4"
        print(f"🎙️ 合并旁白音轨 → {final_video.name}...")
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", str(silent_video),
                    "-i", narration_file,
                    "-map", "0:v",
                    "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac",
                    "-shortest",
                    str(final_video),
                ],
                check=True,
            )
            print(f"✅ lesson{lesson_id} 讲解视频（含旁白）已生成: {final_video.name}")
            result["local_path"] = str(final_video)
        except Exception as e:
            print(f"⚠️ ffmpeg 合并失败，无声版本仍可用: {e}")
            result["local_path"] = str(silent_video) if silent_video.exists() else ""
    else:
        if not narration_file:
            print(f"ℹ️ 无旁白音轨，输出无声版本: {silent_video.name}")
        result["local_path"] = str(silent_video) if silent_video.exists() else ""

    # Upload final video to Tencent COS
    local_path = Path(result["local_path"]) if result["local_path"] else None
    if local_path and local_path.exists():
        try:
            import sys as _sys
            if str(base_dir) not in _sys.path:
                _sys.path.insert(0, str(base_dir))
            from services.storage.tencent_cos_storage import TencentCOSStorage
            cos = TencentCOSStorage.from_env(optional=True)
            if cos:
                object_key = f"videos/lesson{lesson_id}_explanation_final.mp4"
                upload_result = cos.upload_file(
                    str(local_path), object_key, content_type="video/mp4"
                )
                result["cos_url"] = ""   # cleared — study router generates signed URL on request
                result["cos_object_key"] = upload_result.get("object_key", object_key)
                print(f"☁️ 讲解视频已上传 COS: {result['cos_object_key']}")
            else:
                print("ℹ️ COS 未配置，视频仅本地可用。")
        except Exception as e:
            print(f"⚠️ 视频 COS 上传失败，仅本地可用: {e}")

    return result


def sync_to_db(base_dir: Path, lesson_id: int) -> bool:
    sync_script = base_dir / "database" / "sync_to_db.py"
    if not sync_script.exists():
        print(f"⚠️ 未找到 sync_to_db.py，跳过入库。")
        return False
    print(f"🗄️ 开始将 lesson{lesson_id} 同步入库...")
    try:
        subprocess.run(
            ["python", str(sync_script)],
            cwd=str(base_dir),
            check=True,
        )
        print(f"✅ lesson{lesson_id} 入库完成。")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️ lesson{lesson_id} 入库失败（退出码 {e.returncode}），请手动执行 sync_to_db.py。")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run the content builder pipeline for raw lesson PDFs.")
    parser.add_argument(
        "--render-explanation-video",
        action="store_true",
        help="在生成 lesson JSON 后，顺带渲染该课的教学讲解视频。",
    )
    parser.add_argument(
        "--skip-sync",
        action="store_true",
        help="跳过自动入库步骤（默认完成后自动同步到数据库）。",
    )
    args = parser.parse_args()

    # 1. 绝对路径配置
    CURRENT_DIR = Path(__file__).resolve().parent          # backend/content_builder/
    BASE_DIR = CURRENT_DIR.parent                          # backend/
    
    # 向上寻找 backend/.env 文件
    load_dotenv(dotenv_path=BASE_DIR / ".env")
    should_render_explanation_video = args.render_explanation_video or _env_flag(
        "CB_RENDER_EXPLANATION_VIDEO",
        default=False,
    )
    should_sync = not args.skip_sync
    
    # 2. 引擎初始化
    try:
        provider = LLMFactory.create_provider()
        agent = ContentCreatorAgent(provider=provider, memory_dir=CURRENT_DIR)
        print(f"🔧 当前激活模型引擎: {type(provider).__name__}")
        print(
            "🎬 讲解视频渲染: "
            f"{'开启' if should_render_explanation_video else '关闭'}"
        )
    except Exception as e:
        print(f"❌ 系统初始化失败: {e}")
        return

    # 3. 文件夹管理
    raw_dir = CURRENT_DIR / "raw_materials"
    output_dir = CURRENT_DIR / "output_json"
    archive_dir = CURRENT_DIR / "archive_pdfs"
    
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
        result = agent.parse_textbook(str(pdf_path), lesson_id=lesson_id)

        if result is None:
            print(f"\n🛑 [严重错误] {file_name}.pdf 处理失败！")
            print("为了防止后续数据产生连锁反应，程序已自动终止。请排查报错原因后再重新运行。")
            return
        
        if result:
            output_file = output_dir / f"lesson{lesson_id}_data.json"

            # 先落盘（渲染脚本需要从磁盘读取 JSON）
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

            # 渲染视频（读取刚落盘的 JSON + lesson_data 中的旁白路径）
            if should_render_explanation_video:
                video_info = render_explanation_video(BASE_DIR, lesson_id, lesson_data=result)
                result["explanation_video_urls"] = {
                    "cos_url":        video_info.get("cos_url", ""),
                    "cos_object_key": video_info.get("cos_object_key", ""),
                    "local_path":     video_info.get("local_path", ""),
                    "youtube_url":    "",
                    "bilibili_url":   "",
                }
                # 更新落盘文件（含视频 URL）
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)

            print(f"✅ 管线全部完成，数据落盘: {output_file.name}")

            if should_sync:
                sync_to_db(BASE_DIR, lesson_id)
            
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
