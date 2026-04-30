#!/usr/bin/env python3
"""
One-time migration: rename example.en → example.translation in global_vocab_memory.json.

Usage:
    python scripts/migrate_global_vocab_en_to_translation.py
    python scripts/migrate_global_vocab_en_to_translation.py --dry-run
"""

import json
import argparse
from pathlib import Path


def migrate(obj):
    if isinstance(obj, dict):
        result = {k: migrate(v) for k, v in obj.items()}
        if "cn" in result and "py" in result and "en" in result:
            result["translation"] = result.pop("en")
        return result
    if isinstance(obj, list):
        return [migrate(item) for item in obj]
    return obj


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print diff without writing")
    args = parser.parse_args()

    target = Path(__file__).resolve().parent.parent / "artifacts" / "integrated_chinese" / "vocab_memory" / "global_vocab_memory.json"
    if not target.exists():
        print(f"❌ 文件不存在: {target}")
        return

    with open(target, encoding="utf-8") as f:
        data = json.load(f)

    migrated = migrate(data)

    # Count how many example.en were renamed
    def count_en(obj):
        n = 0
        if isinstance(obj, dict):
            if "translation" in obj and "cn" in obj and "py" in obj:
                n += 1
            for v in obj.values():
                n += count_en(v)
        elif isinstance(obj, list):
            for item in obj:
                n += count_en(item)
        return n

    changed = count_en(migrated)

    if args.dry_run:
        print(f"[dry-run] 将迁移 {changed} 处 example.en → example.translation")
        print(f"[dry-run] 文件未修改: {target}")
        return

    with open(target, "w", encoding="utf-8") as f:
        json.dump(migrated, f, ensure_ascii=False, indent=2)

    print(f"✅ 已迁移 {changed} 处 example.en → example.translation")
    print(f"   文件: {target.relative_to(target.parent.parent.parent)}")


if __name__ == "__main__":
    main()
