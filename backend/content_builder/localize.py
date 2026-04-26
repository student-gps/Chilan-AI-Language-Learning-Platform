#!/usr/bin/env python3
"""
localize.py — Translate a lesson JSON from English to another target language.

Usage:
    python localize.py --lang fr --lesson 101          # translate lesson101
    python localize.py --lang fr lesson101_data.json   # explicit file
    python localize.py --lang fr                       # translate all output_json files
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
    "fr": {"name": "French", "native": "Français"},
    "de": {"name": "German", "native": "Deutsch"},
    "es": {"name": "Spanish", "native": "Español"},
    "ja": {"name": "Japanese", "native": "日本語"},
    "ko": {"name": "Korean", "native": "한국어"},
}

SHORT_BATCH_SIZE = 30   # strings per call for short fields
NARRATION_BATCH_SIZE = 3  # subtitle_en segments per call (longer text)


# ── Prompt ───────────────────────────────────────────────────────────────────

def _build_translate_prompt(lang_name: str, strings_dict: dict) -> str:
    payload = json.dumps(strings_dict, ensure_ascii=False, indent=2)
    return f"""You are a professional translator for Chinese language learning materials. Translate each English string below into {lang_name}.

Rules:
1. Output ONLY valid JSON with the exact same keys. No markdown, no extra text.
2. Preserve [zh:...] markers exactly as-is — they contain Chinese pronunciation cues and must not be translated or modified.
3. Use clear, natural {lang_name} appropriate for adult language learners.
4. Translate meaning naturally — do not translate word-by-word.
5. For single-word vocabulary answers, give the most natural single-word (or short phrase) {lang_name} equivalent.

Input:
{payload}

Output (JSON only):"""


# ── JSON walker ───────────────────────────────────────────────────────────────

def _collect_translatable(data: dict) -> list:
    """Return list of (dotted_path, english_text) for all translatable fields."""
    items = []

    # 1. Dialogue line translations
    for d_idx, dialogue in enumerate(data.get("course_content", {}).get("dialogues", [])):
        for l_idx, line in enumerate(dialogue.get("lines", [])):
            if line.get("translation"):
                items.append((f"course_content.dialogues.{d_idx}.lines.{l_idx}.translation", line["translation"]))

    # 1b. Vocabulary list
    for v_idx, vocab in enumerate(data.get("course_content", {}).get("vocabulary", [])):
        base = f"course_content.vocabulary.{v_idx}"
        if vocab.get("definition"):
            items.append((f"{base}.definition", vocab["definition"]))
        if vocab.get("part_of_speech"):
            items.append((f"{base}.part_of_speech", vocab["part_of_speech"]))
        if vocab.get("example_sentence", {}).get("translation"):
            items.append((f"{base}.example_sentence.translation", vocab["example_sentence"]["translation"]))

    # 2. Language notes
    for n_idx, note in enumerate(data.get("teaching_materials", {}).get("language_notes", [])):
        if note.get("explanation_en"):
            items.append((f"teaching_materials.language_notes.{n_idx}.explanation_en", note["explanation_en"]))

    # 3. Grammar sections
    for g_idx, gs in enumerate(data.get("teaching_materials", {}).get("grammar_sections", [])):
        base = f"teaching_materials.grammar_sections.{g_idx}"
        if gs.get("title") and not gs["title"].startswith("G-"):
            items.append((f"{base}.title", gs["title"]))
        if gs.get("explanation_en"):
            items.append((f"{base}.explanation_en", gs["explanation_en"]))
        for p_idx, p in enumerate(gs.get("patterns", [])):
            if p.get("meaning_en"):
                items.append((f"{base}.patterns.{p_idx}.meaning_en", p["meaning_en"]))
        for e_idx, e in enumerate(gs.get("examples", [])):
            if e.get("translation"):
                items.append((f"{base}.examples.{e_idx}.translation", e["translation"]))
        for u_idx, u in enumerate(gs.get("usage_notes", [])):
            if u and isinstance(u, str):
                items.append((f"{base}.usage_notes.{u_idx}", u))
        for c_idx, c in enumerate(gs.get("common_errors", [])):
            if c.get("explanation_en"):
                items.append((f"{base}.common_errors.{c_idx}.explanation_en", c["explanation_en"]))

    # 4. Database items
    for i_idx, item in enumerate(data.get("database_items", [])):
        qtype = item.get("question_type", "")
        base = f"database_items.{i_idx}"
        # Context example English captions — always translate
        for cx_idx, cx in enumerate(item.get("context_examples", [])):
            if cx.get("en"):
                items.append((f"{base}.context_examples.{cx_idx}.translation", cx["en"]))
        # CN_TO_EN: standard_answers are English words/phrases → translate to target lang
        if qtype == "CN_TO_EN":
            for a_idx, ans in enumerate(item.get("standard_answers", [])):
                if ans and isinstance(ans, str):
                    items.append((f"{base}.standard_answers.{a_idx}", ans))
        # EN_TO_CN / EN_TO_CN_SPEAK: original_text is the English prompt → translate
        elif qtype in ("EN_TO_CN", "EN_TO_CN_SPEAK"):
            ot = item.get("original_text")
            if ot and isinstance(ot, str):
                items.append((f"{base}.original_text", ot))
        # CN_LISTEN_WRITE: original_text is an English hint shown to the learner → translate
        elif qtype == "CN_LISTEN_WRITE":
            ot = item.get("original_text")
            if ot and isinstance(ot, str):
                items.append((f"{base}.original_text", ot))

    # 5. Video render plan — segment titles, teaching goals, narration, word glosses
    exp = data.get("video_render_plan", {}).get("explanation", {})
    if exp.get("target_audience"):
        items.append(("video_render_plan.explanation.target_audience", exp["target_audience"]))
    for s_idx, seg in enumerate(exp.get("segments", [])):
        base = f"video_render_plan.explanation.segments.{s_idx}"
        if seg.get("segment_title"):
            items.append((f"{base}.segment_title", seg["segment_title"]))
        if seg.get("teaching_goal"):
            items.append((f"{base}.teaching_goal", seg["teaching_goal"]))
        if seg.get("visual_notes"):
            items.append((f"{base}.visual_notes", seg["visual_notes"]))
        subtitle = seg.get("narration_track", {}).get("subtitle_en", "")
        if subtitle:
            items.append((f"{base}.narration_track.subtitle_en", subtitle))
        # highlight_words on the segment level
        for w_idx, w in enumerate(seg.get("highlight_words", [])):
            wb = f"{base}.highlight_words.{w_idx}"
            if w.get("translation"):
                items.append((f"{wb}.translation", w["translation"]))
            if w.get("explanation_en"):
                items.append((f"{wb}.explanation_en", w["explanation_en"]))
        # visual_blocks — focus gloss, notes, highlight_words, grammar_points
        for vb_idx, vb in enumerate(seg.get("visual_blocks", [])):
            vb_base = f"{base}.visual_blocks.{vb_idx}.content"
            content = vb.get("content", {})
            if content.get("focus_gloss_en"):
                items.append((f"{vb_base}.focus_gloss_en", content["focus_gloss_en"]))
            if content.get("notes"):
                items.append((f"{vb_base}.notes", content["notes"]))
            for vw_idx, vw in enumerate(content.get("highlight_words", [])):
                vwb = f"{vb_base}.highlight_words.{vw_idx}"
                if vw.get("translation"):
                    items.append((f"{vwb}.translation", vw["translation"]))
                if vw.get("explanation_en"):
                    items.append((f"{vwb}.explanation_en", vw["explanation_en"]))
            for gp_idx, gp in enumerate(content.get("grammar_points", [])):
                gpb = f"{vb_base}.grammar_points.{gp_idx}"
                if gp.get("explanation_en"):
                    items.append((f"{gpb}.explanation_en", gp["explanation_en"]))
        # segment-level grammar_points
        for gp_idx, gp in enumerate(seg.get("grammar_points", [])):
            gpb = f"{base}.grammar_points.{gp_idx}"
            if gp.get("explanation_en"):
                items.append((f"{gpb}.explanation_en", gp["explanation_en"]))

    return items


def _set_by_path(obj, path: str, value):
    """Set a value in a nested dict/list by dotted string path."""
    parts = path.split(".")
    for part in parts[:-1]:
        obj = obj[int(part)] if part.isdigit() else obj[part]
    last = parts[-1]
    if last.isdigit():
        obj[int(last)] = value
    else:
        obj[last] = value


# ── Translation engine ────────────────────────────────────────────────────────

def _translate_batch(llm, lang_name: str, batch_dict: dict) -> dict:
    prompt = _build_translate_prompt(lang_name, batch_dict)
    result = llm.generate_structured_json(prompt, file_path=None)
    if isinstance(result, dict):
        return result
    print(f"  ⚠️  Unexpected translation result type: {type(result)}, skipping batch.")
    return {}


def _run_translation(llm, lang_name: str, items: list) -> dict:
    """Translate all collected (path, text) items; return {path: translated_text}."""
    narration_items = [(p, v) for p, v in items if "subtitle_en" in p]
    short_items = [(p, v) for p, v in items if "subtitle_en" not in p]

    translated_map = {}

    # Short strings — large batches
    for start in range(0, len(short_items), SHORT_BATCH_SIZE):
        batch = short_items[start:start + SHORT_BATCH_SIZE]
        batch_dict = {f"t{start + i:04d}": v for i, (_, v) in enumerate(batch)}
        batch_num = start // SHORT_BATCH_SIZE + 1
        total_batches = (len(short_items) + SHORT_BATCH_SIZE - 1) // SHORT_BATCH_SIZE
        print(f"  🌐 Batch {batch_num}/{total_batches}: translating {len(batch)} strings...")
        result = _translate_batch(llm, lang_name, batch_dict)
        for i, (path, _) in enumerate(batch):
            key = f"t{start + i:04d}"
            if key in result:
                translated_map[path] = result[key]

    # Narration — small batches (long text)
    for start in range(0, len(narration_items), NARRATION_BATCH_SIZE):
        batch = narration_items[start:start + NARRATION_BATCH_SIZE]
        batch_dict = {f"n{start + i:04d}": v for i, (_, v) in enumerate(batch)}
        batch_num = start // NARRATION_BATCH_SIZE + 1
        total_batches = (len(narration_items) + NARRATION_BATCH_SIZE - 1) // NARRATION_BATCH_SIZE
        print(f"  🎙️  Narration batch {batch_num}/{total_batches}: {len(batch)} segment(s)...")
        result = _translate_batch(llm, lang_name, batch_dict)
        for i, (path, _) in enumerate(batch):
            key = f"n{start + i:04d}"
            if key in result:
                translated_map[path] = result[key]

    return translated_map


# ── Main per-file logic ───────────────────────────────────────────────────────

def translate_lesson(source_path: Path, lang: str, llm) -> dict:
    lang_name = LANG_META[lang]["name"]

    with open(source_path, encoding="utf-8") as f:
        data = json.load(f)

    translated = copy.deepcopy(data)
    items = _collect_translatable(data)
    print(f"  🔍 Found {len(items)} translatable strings ({sum(1 for p, _ in items if 'subtitle_en' in p)} narration segments)")

    translated_map = _run_translation(llm, lang_name, items)
    hits = len(translated_map)
    print(f"  ✅ Translated {hits}/{len(items)} strings")

    for path, value in translated_map.items():
        _set_by_path(translated, path, value)

    translated["localization"] = {
        "source_lang": "en",
        "target_lang": lang,
        "target_lang_name": lang_name,
        "target_lang_native": LANG_META[lang]["native"],
    }

    return translated


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Translate lesson JSON to a target language")
    parser.add_argument("--lang", required=True, help="Target language code: fr, de, es, ja, ko")
    parser.add_argument("--lesson", help="Lesson ID (e.g. 101 → lesson101_data.json)")
    parser.add_argument("files", nargs="*", help="JSON file name(s) in output_json/ (default: all)")
    args = parser.parse_args()

    lang = args.lang
    if lang not in LANG_META:
        print(f"❌ Unknown language '{lang}'. Supported: {', '.join(LANG_META.keys())}")
        sys.exit(1)

    json_dir = CONTENT_BUILDER_DIR / "artifacts" / "output_json" / "en"
    out_dir = CONTENT_BUILDER_DIR / "artifacts" / "output_json" / lang
    out_dir.mkdir(parents=True, exist_ok=True)

    # Resolve input files
    if args.lesson:
        files = [json_dir / f"lesson{args.lesson}_data.json"]
    elif args.files:
        files = [Path(f) if Path(f).is_absolute() else json_dir / f for f in args.files]
    else:
        files = sorted(json_dir.glob("lesson*_data.json"))

    if not files:
        print("❌ No input files found.")
        sys.exit(1)

    llm = LLMFactory.create_provider()
    lang_display = f"{LANG_META[lang]['name']} ({LANG_META[lang]['native']})"
    print(f"\n🌐 Localizing {len(files)} file(s) → {lang_display}\n")

    for source_path in files:
        if not source_path.exists():
            print(f"⚠️  Not found: {source_path.name}, skipping.")
            continue
        stem = source_path.stem  # e.g. lesson101_data
        out_path = out_dir / f"{stem}_{lang}.json"
        if out_path.exists():
            print(f"⏭️  Already exists: {out_path.name}, skipping.")
            continue

        print(f"📝 {source_path.name}  →  {out_path.name}")
        result = translate_lesson(source_path, lang, llm)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  💾 Saved → {out_path}\n")

    print("✨ Done.")


if __name__ == "__main__":
    main()
