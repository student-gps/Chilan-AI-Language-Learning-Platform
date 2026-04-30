#!/usr/bin/env python3
"""
One-time migration: rename all "english" and context_examples "en" keys
to "translation" in existing lesson JSON files.

Usage:
    python scripts/migrate_english_to_translation.py
"""

import json
from pathlib import Path


def migrate(obj):
    if isinstance(obj, dict):
        new = {}
        for k, v in obj.items():
            new_k = k
            # Rename top-level and nested "english" keys
            if k == "english":
                new_k = "translation"
            # Rename context_examples[].en  (but NOT internal "en" shorthand in cn/py/en tuples)
            # We identify context_examples entries by checking sibling keys
            migrated = {}
        result = {}
        for k, v in obj.items():
            new_k = "translation" if k == "english" else k
            result[new_k] = migrate(v)
        # Also rename "en" → "translation" when it appears alongside "cn" and "py"
        # (context_examples pattern)
        if "cn" in result and "py" in result and "en" in result:
            result["translation"] = result.pop("en")
        return result
    if isinstance(obj, list):
        return [migrate(item) for item in obj]
    return obj


def main():
    script_dir = Path(__file__).resolve().parent
    content_builder_dir = script_dir.parent
    integrated_chinese_dir = content_builder_dir / "artifacts" / "integrated_chinese"
    json_dirs = [
        integrated_chinese_dir / "output_json",
        integrated_chinese_dir / "synced_json",
    ]
    # Also migrate fr/ subfolder if present
    for base in list(json_dirs):
        for sub in base.iterdir() if base.exists() else []:
            if sub.is_dir():
                json_dirs.append(sub)

    total = 0
    for json_dir in json_dirs:
        if not json_dir.exists():
            continue
        for json_file in sorted(json_dir.glob("*.json")):
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
            migrated = migrate(data)
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(migrated, f, ensure_ascii=False, indent=2)
            print(f"  ✅ {json_file.relative_to(content_builder_dir)}")
            total += 1

    print(f"\n✨ Migrated {total} file(s).")


if __name__ == "__main__":
    main()
