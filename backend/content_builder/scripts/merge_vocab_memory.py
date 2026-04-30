"""
合并两个 global_vocab_memory.json 文件。

用法：
  python merge_vocab_memory.py <另一台电脑的文件路径>

例如：
  python merge_vocab_memory.py C:/Users/gaope/Desktop/global_vocab_memory_1101_1601.json
"""
import json
import sys
from pathlib import Path

MAIN_FILE = Path(__file__).parent.parent / "artifacts" / "integrated_chinese" / "vocab_memory" / "global_vocab_memory.json"

def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def merge(base: dict, other: dict) -> tuple[dict, int]:
    added = 0
    for word, entries in other.items():
        if word not in base:
            base[word] = []
        existing_defs = {e["definition"] for e in base[word]}
        for entry in entries:
            if entry["definition"] not in existing_defs:
                base[word].append(entry)
                existing_defs.add(entry["definition"])
                added += 1
    return base, added

def main():
    if len(sys.argv) < 2:
        print("用法: python merge_vocab_memory.py <另一个文件路径>")
        sys.exit(1)

    other_path = Path(sys.argv[1])
    if not other_path.exists():
        print(f"❌ 文件不存在: {other_path}")
        sys.exit(1)

    base = load(MAIN_FILE) if MAIN_FILE.exists() else {}
    other = load(other_path)

    print(f"本机词条数: {len(base)} 词")
    print(f"另一台电脑词条数: {len(other)} 词")

    merged, added = merge(base, other)

    with open(MAIN_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"✅ 合并完成！共 {len(merged)} 词，新增 {added} 条释义记录。")
    print(f"   已写入: {MAIN_FILE}")

if __name__ == "__main__":
    main()
