"""
patch_long_segments.py — 对已生成的 lesson JSON 重新运行 Task4CExplanationComposer，
修复 hero_line focus_text 超过 40 汉字未被自动拆分的 segment。

用法：
    python backend/content_builder/scripts/patch_long_segments.py           # 扫描 integrated_chinese/synced_json/en
    python backend/content_builder/scripts/patch_long_segments.py --dry-run # 只报告，不写文件
    python backend/content_builder/scripts/patch_long_segments.py 1601 1701 # 指定 lesson id
"""
import json
import re
import sys
import argparse
from pathlib import Path

CONTENT_BUILDER = Path(__file__).resolve().parent.parent   # backend/content_builder/
ARTIFACTS_DIR = CONTENT_BUILDER / "artifacts" / "integrated_chinese"
sys.path.insert(0, str(CONTENT_BUILDER))

from tasks.render_planner import Task4CExplanationComposer

CN_RE = re.compile(r'[一-鿿]')
MAX_CN = 40


def _max_hero_cn(video_render_plan: dict) -> int:
    segs = (video_render_plan.get("explanation") or {}).get("segments") or []
    worst = 0
    for s in segs:
        for b in (s.get("visual_blocks") or []):
            if b.get("block_type") == "hero_line":
                ft = (b.get("content") or {}).get("focus_text", "")
                worst = max(worst, len(CN_RE.findall(ft)))
    return worst


def patch_file(json_path: Path, dry_run: bool = False) -> bool:
    with open(json_path, encoding="utf-8") as f:
        d = json.load(f)

    # Safety: never re-compose a localized JSON — it would overwrite translated narration.
    if d.get("localization", {}).get("target_lang"):
        target = d["localization"]["target_lang"]
        print(f"  ⛔ 跳过：这是已翻译的 {target.upper()} 版本，重建 video_render_plan 会覆盖翻译旁白。")
        print(f"     如需修复超长 hero_line，请先修英文源 JSON，然后重新运行 localize.py --lang {target}。")
        return False

    worst = _max_hero_cn(d.get("video_render_plan") or {})
    if worst <= MAX_CN:
        print(f"  ✅ 无需修复（最长 hero_line {worst} 字）")
        return False

    print(f"  ⚠️  检测到最长 hero_line {worst} 字，开始修复...")

    metadata = d.get("lesson_metadata") or {}
    explanation = ((d.get("video_plan") or {}).get("explanation")) or {}

    if not explanation.get("segments"):
        print(f"  ❌ video_plan.explanation.segments 为空，无法修复")
        return False

    composer = Task4CExplanationComposer()
    new_explanation = composer.run(metadata, explanation)

    # Verify the split actually happened
    new_worst = _max_hero_cn({"explanation": new_explanation})
    seg_before = len((d.get("video_render_plan") or {}).get("explanation", {}).get("segments") or [])
    seg_after = len(new_explanation.get("segments") or [])
    print(f"  📐 segment 数: {seg_before} → {seg_after}，修复后最长 hero_line: {new_worst} 字")

    if dry_run:
        print(f"  🔍 dry-run 模式，未写入文件")
        return True

    d["video_render_plan"]["explanation"] = new_explanation

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"  💾 已写回: {json_path.name}")
    return True


def main():
    parser = argparse.ArgumentParser(description="修复 video_render_plan 中超长 hero_line segment")
    parser.add_argument("lesson_ids", nargs="*", type=int, help="指定 lesson id（不填则扫描全部）")
    parser.add_argument("--dry-run", action="store_true", help="只报告，不写文件")
    parser.add_argument("--lang", default="en", help="JSON 所在语言子目录（默认 en）")
    args = parser.parse_args()

    synced = ARTIFACTS_DIR / "synced_json" / args.lang
    output = ARTIFACTS_DIR / "output_json" / args.lang
    json_dir = synced if synced.exists() and any(synced.glob("*_data*.json")) else output

    if args.lesson_ids:
        paths = []
        for lid in args.lesson_ids:
            candidates = list(json_dir.glob(f"lesson{lid}_data*.json"))
            if candidates:
                paths.extend(candidates)
            else:
                print(f"⚠️  未找到 lesson{lid} 的 JSON 文件")
    else:
        paths = sorted(json_dir.glob("*_data*.json"))

    if not paths:
        print(f"📭 {json_dir} 下没有找到 JSON 文件")
        return

    fixed, skipped = 0, 0
    for p in paths:
        lesson_id = re.search(r'\d+', p.stem)
        lid = lesson_id.group() if lesson_id else p.stem
        print(f"\nlesson{lid}:")
        if patch_file(p, dry_run=args.dry_run):
            fixed += 1
        else:
            skipped += 1

    print(f"\n{'='*40}")
    print(f"修复: {fixed} 个，无需处理: {skipped} 个")


if __name__ == "__main__":
    main()
