#!/usr/bin/env python3
"""
localize_vocab_memory.py — Translate global_vocab_memory.json to a target language.

Incremental: if a target-language file already exists, only newly added words
(or words with more senses than previously translated) are processed.

Usage:
    python localize_vocab_memory.py --lang fr              # translate to French
    python localize_vocab_memory.py --lang fr --dry-run    # show what would be translated
"""

import argparse
import copy
import json
import sys
from pathlib import Path

CONTENT_BUILDER_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CONTENT_BUILDER_DIR.parent
sys.path.insert(0, str(CONTENT_BUILDER_DIR))
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(dotenv_path=BACKEND_DIR / ".env")

from llm_providers import LLMFactory

LANG_META = {
    "fr": {"name": "French",   "native": "Français"},
    "de": {"name": "German",   "native": "Deutsch"},
    "es": {"name": "Spanish",  "native": "Español"},
    "ja": {"name": "Japanese", "native": "日本語"},
    "ko": {"name": "Korean",   "native": "한국어"},
    "vi": {"name": "Vietnamese", "native": "Tiếng Việt"},
    "ar": {"name": "Arabic", "native": "العربية"},
}

BATCH_SIZE = 50
SAVE_EVERY = 200   # persist to disk every N translated strings


def _build_prompt(lang_name: str, strings_dict: dict, mode: str = "general") -> str:
    payload = json.dumps(strings_dict, ensure_ascii=False, indent=2)
    if mode == "pos":
        instruction = (
            f"Translate each grammatical part-of-speech label into standard {lang_name} "
            f"grammatical terms (e.g. 'Noun' → 'Nom', 'Verb' → 'Verbe')."
        )
    else:
        instruction = (
            f"Translate each English string into {lang_name}.\n"
            f"- Vocabulary definitions: most natural {lang_name} equivalent (word or short phrase).\n"
            f"- Example sentence translations: translate naturally, not word-by-word."
        )
    return f"""You are a professional translator for Chinese language learning materials.
{instruction}

Rules:
1. Output ONLY valid JSON with the exact same keys. No markdown, no extra text.
2. Keep the result concise and appropriate for a language-learning app.
3. Do not use raw ASCII double quotes (") inside translated string values; use natural target-language quotation marks or no quotes.

Input:
{payload}

Output (JSON only):"""


def _translate_batch(llm, lang_name: str, batch: dict, mode: str = "general") -> dict:
    prompt = _build_prompt(lang_name, batch, mode=mode)
    result = llm.generate_structured_json(prompt, file_path=None)
    if isinstance(result, dict):
        return result
    print(f"  ⚠️  Unexpected result type: {type(result)}, skipping batch.")
    return {}


def _build_pos_lookup(llm, lang_name: str, pending: list) -> dict:
    """
    Collect unique part_of_speech values from pending items, translate them in one
    pass, and return a {english_pos: translated_pos} lookup dict.
    """
    unique_pos = sorted({text for key, text in pending if key.endswith("|||part_of_speech")})
    if not unique_pos:
        return {}

    print(f"  📚 Translating {len(unique_pos)} unique part-of-speech label(s) (1-2 calls)...")
    lookup: dict = {}
    for start in range(0, len(unique_pos), BATCH_SIZE):
        chunk = unique_pos[start:start + BATCH_SIZE]
        batch_dict = {f"p{i:03d}": v for i, v in enumerate(chunk)}
        result = _translate_batch(llm, lang_name, batch_dict, mode="pos")
        for i, pos in enumerate(chunk):
            key = f"p{i:03d}"
            if key in result:
                lookup[pos] = result[key]

    untranslated = [p for p in unique_pos if p not in lookup]
    if untranslated:
        print(f"  ⚠️  {len(untranslated)} POS label(s) not returned by LLM, will keep English: {untranslated}")
        for p in untranslated:
            lookup[p] = p   # fallback: keep original

    return lookup


def _translated_field_missing(target_sense: dict, field: str) -> bool:
    if field == "example.translation":
        return not ((target_sense.get("example") or {}).get("translation") or "").strip()
    return not (target_sense.get(field) or "").strip()


def _copy_source_sense(source_sense: dict) -> dict:
    target_sense = copy.deepcopy(source_sense)
    target_sense["source_definition"] = source_sense.get("definition", "")
    target_sense["source_part_of_speech"] = source_sense.get("part_of_speech", "")
    return target_sense


def _ensure_source_fields(en_data: dict, target_data: dict) -> bool:
    changed = False
    for word, senses in target_data.items():
        if not isinstance(senses, list):
            continue
        source_senses = en_data.get(word, [])
        if not isinstance(source_senses, list):
            continue
        for idx, sense in enumerate(senses):
            if not isinstance(sense, dict) or idx >= len(source_senses):
                continue
            source_sense = source_senses[idx]
            source_definition = source_sense.get("definition", "")
            source_pos = source_sense.get("part_of_speech", "")
            if sense.get("source_definition") != source_definition:
                sense["source_definition"] = source_definition
                changed = True
            if sense.get("source_part_of_speech") != source_pos:
                sense["source_part_of_speech"] = source_pos
                changed = True
    return changed


def _collect_pending(en_data: dict, fr_data: dict) -> list:
    """
    Return list of (flat_key, english_text) for all entries not yet translated.
    flat_key format: "word|||sense_idx|||field"
    Fields: definition, part_of_speech, example.translation
    """
    items = []
    for word, senses in en_data.items():
        if not isinstance(senses, list):
            continue
        fr_senses = fr_data.get(word, [])
        for s_idx, sense in enumerate(senses):
            if not isinstance(sense, dict):
                continue
            target_sense = fr_senses[s_idx] if isinstance(fr_senses, list) and s_idx < len(fr_senses) and isinstance(fr_senses[s_idx], dict) else {}
            base = f"{word}|||{s_idx}"
            if sense.get("definition") and _translated_field_missing(target_sense, "definition"):
                items.append((f"{base}|||definition", sense["definition"]))
            if sense.get("part_of_speech") and _translated_field_missing(target_sense, "part_of_speech"):
                items.append((f"{base}|||part_of_speech", sense["part_of_speech"]))
            if sense.get("example", {}).get("translation") and _translated_field_missing(target_sense, "example.translation"):
                items.append((f"{base}|||example.translation", sense["example"]["translation"]))
    return items


def _apply_translations(en_data: dict, fr_data: dict, translated_map: dict) -> dict:
    """Merge translated fields back into fr_data (modifies in place, returns fr_data)."""
    for flat_key, value in translated_map.items():
        word, s_idx_str, field = flat_key.split("|||")
        s_idx = int(s_idx_str)

        if word not in fr_data:
            # Copy the full sense from English as a base (preserves cn/py/tokens/lesson_id)
            fr_data[word] = []

        # Extend list if needed
        while len(fr_data[word]) <= s_idx:
            src_sense = _copy_source_sense(en_data[word][len(fr_data[word])])
            fr_data[word].append(src_sense)

        sense = fr_data[word][s_idx]
        source_sense = en_data[word][s_idx]
        sense["source_definition"] = source_sense.get("definition", "")
        sense["source_part_of_speech"] = source_sense.get("part_of_speech", "")
        if field == "example.translation":
            sense.setdefault("example", {})["translation"] = value
        else:
            sense[field] = value

    return fr_data


def translate_vocab_memory(lang: str, llm, dry_run: bool = False) -> None:
    lang_name = LANG_META[lang]["name"]
    vocab_dir = CONTENT_BUILDER_DIR / "artifacts" / "integrated_chinese" / "vocab_memory"
    src_path = vocab_dir / "global_vocab_memory.json"
    dst_path = vocab_dir / f"global_vocab_memory_{lang}.json"

    if not src_path.exists():
        print(f"❌ Source file not found: {src_path}")
        sys.exit(1)

    with open(src_path, encoding="utf-8") as f:
        en_data = json.load(f)

    fr_data: dict = {}
    if dst_path.exists():
        with open(dst_path, encoding="utf-8") as f:
            fr_data = json.load(f)
        print(f"📂 Loaded existing {dst_path.name} ({len(fr_data)} words already translated)")
        if _ensure_source_fields(en_data, fr_data) and not dry_run:
            with open(dst_path, "w", encoding="utf-8") as f:
                json.dump(fr_data, f, ensure_ascii=False, indent=2)
            print("  🔖 Added missing source_definition/source_part_of_speech fields.")
    else:
        print(f"🆕 No existing {lang} file — full translation run")

    pending = _collect_pending(en_data, fr_data)
    total = len(pending)

    if total == 0:
        print(f"✅ Nothing to translate — {dst_path.name} is up to date.")
        return

    pos_count = sum(1 for k, _ in pending if k.endswith("|||part_of_speech"))
    other_count = total - pos_count
    print(f"🔍 {total} string(s) to translate: {other_count} definitions/examples, "
          f"{pos_count} part-of-speech (will deduplicate)\n")

    if dry_run:
        for key, text in pending[:20]:
            word, s_idx, field = key.split("|||")
            print(f"  [{word}][{s_idx}][{field}] {text!r}")
        if total > 20:
            print(f"  ... and {total - 20} more")
        unique_pos = {text for key, text in pending if key.endswith("|||part_of_speech")}
        print(f"\n[dry-run] {other_count} strings via batched LLM + "
              f"{len(unique_pos)} unique POS labels (≈{(other_count + BATCH_SIZE - 1) // BATCH_SIZE + 1} calls total).")
        print("[dry-run] File not modified.")
        return

    # ── Step 1: translate unique POS labels once ──────────────────────────────
    pos_lookup = _build_pos_lookup(llm, lang_name, pending)

    # Apply POS translations directly (no LLM call per entry)
    pos_map = {key: pos_lookup[text]
               for key, text in pending
               if key.endswith("|||part_of_speech") and text in pos_lookup}
    if pos_map:
        _apply_translations(en_data, fr_data, pos_map)

    # ── Step 2: translate definitions and example sentences ───────────────────
    other_items = [(key, text) for key, text in pending
                   if not key.endswith("|||part_of_speech")]
    total_other = len(other_items)

    translated_map: dict = {}
    for start in range(0, total_other, BATCH_SIZE):
        batch = other_items[start:start + BATCH_SIZE]
        batch_dict = {f"t{start + i:05d}": text for i, (_, text) in enumerate(batch)}
        batch_num = start // BATCH_SIZE + 1
        total_batches = (total_other + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"  🌐 Batch {batch_num}/{total_batches}: {len(batch)} strings...")

        result = _translate_batch(llm, lang_name, batch_dict)
        for i, (flat_key, _) in enumerate(batch):
            key = f"t{start + i:05d}"
            if key in result:
                translated_map[flat_key] = result[key]

        # Periodic save
        if len(translated_map) >= SAVE_EVERY or (start + BATCH_SIZE) >= total_other:
            _apply_translations(en_data, fr_data, translated_map)
            translated_map = {}
            with open(dst_path, "w", encoding="utf-8") as f:
                json.dump(fr_data, f, ensure_ascii=False, indent=2)
            saved_count = sum(len(v) for v in fr_data.values())
            print(f"  💾 Saved ({saved_count} total word-senses in file)")

    final_count = sum(len(v) for v in fr_data.values())
    print(f"\n✨ Done — {final_count} word-senses in {dst_path.name}")


def main():
    parser = argparse.ArgumentParser(description="Translate global_vocab_memory.json to a target language")
    parser.add_argument("--lang", required=True, help="Target language code: fr, de, es, ja, ko, vi, ar")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be translated without writing")
    args = parser.parse_args()

    if args.lang not in LANG_META:
        print(f"❌ Unknown language '{args.lang}'. Supported: {', '.join(LANG_META.keys())}")
        sys.exit(1)

    llm = None if args.dry_run else LLMFactory.create_provider()
    translate_vocab_memory(args.lang, llm, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
