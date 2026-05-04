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
import re
import sys
from pathlib import Path

CONTENT_BUILDER_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CONTENT_BUILDER_DIR.parent
sys.path.insert(0, str(CONTENT_BUILDER_DIR))
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(dotenv_path=BACKEND_DIR / ".env")

from core.paths import default_paths
from core.pipeline import get_pipeline

LANG_META = {
    "fr": {"name": "French", "native": "Français"},
    "de": {"name": "German", "native": "Deutsch"},
    "es": {"name": "Spanish", "native": "Español"},
    "ja": {"name": "Japanese", "native": "日本語"},
    "ko": {"name": "Korean", "native": "한국어"},
    "vi": {"name": "Vietnamese", "native": "Tiếng Việt"},
    "ar": {"name": "Arabic", "native": "العربية"},
}

SHORT_BATCH_SIZE = 30   # strings per call for short fields
NARRATION_BATCH_SIZE = 3  # subtitle_en segments per call (longer text)

# question_type remap per target language (EN-based types → language-specific types)
_TYPE_REMAP: dict[str, dict[str, str]] = {
    "fr": {"CN_TO_EN": "CN_TO_FR", "EN_TO_CN": "FR_TO_CN", "EN_TO_CN_SPEAK": "FR_TO_CN_SPEAK"},
    "de": {"CN_TO_EN": "CN_TO_DE", "EN_TO_CN": "DE_TO_CN", "EN_TO_CN_SPEAK": "DE_TO_CN_SPEAK"},
    "es": {"CN_TO_EN": "CN_TO_ES", "EN_TO_CN": "ES_TO_CN", "EN_TO_CN_SPEAK": "ES_TO_CN_SPEAK"},
    "ja": {"CN_TO_EN": "CN_TO_JA", "EN_TO_CN": "JA_TO_CN", "EN_TO_CN_SPEAK": "JA_TO_CN_SPEAK"},
    "ko": {"CN_TO_EN": "CN_TO_KO", "EN_TO_CN": "KO_TO_CN", "EN_TO_CN_SPEAK": "KO_TO_CN_SPEAK"},
    "vi": {"CN_TO_EN": "CN_TO_VI", "EN_TO_CN": "VI_TO_CN", "EN_TO_CN_SPEAK": "VI_TO_CN_SPEAK"},
    "ar": {"CN_TO_EN": "CN_TO_AR", "EN_TO_CN": "AR_TO_CN", "EN_TO_CN_SPEAK": "AR_TO_CN_SPEAK"},
}


# ── Prompt ───────────────────────────────────────────────────────────────────

def _build_translate_prompt(
    lang_name: str,
    strings_dict: dict,
    mode: str = "general",
    marker_glossary: dict[str, dict[str, str]] | None = None,
) -> str:
    payload = json.dumps(strings_dict, ensure_ascii=False, indent=2)
    glossary_lines = []
    for key, token_map in (marker_glossary or {}).items():
        if token_map:
            entries = "; ".join(f"{token} = {marker}" for token, marker in token_map.items())
            glossary_lines.append(f"- {key}: {entries}")
    glossary_text = "\n".join(glossary_lines) if glossary_lines else "(none)"
    if mode == "narration":
        field_rules = f"""
Narration-specific rules for TTS subtitles:
8. These strings are video voice-over scripts. Translate and lightly adapt them into natural spoken {lang_name}; do not translate word-for-word if that creates stiff or long sentences.
9. Keep each sentence subtitle-friendly: prefer short spoken sentences, usually under 18–24 words. Split long source sentences into two natural target-language sentences when helpful.
10. Do NOT place multiple complete sentences inside one quoted span. If the source has a multi-sentence quote, move the explanation outside the quote or split it into separate spoken sentences.
11. Use standard quotation marks for the target language consistently, but keep quoted examples short. Preferred styles: French « … »; German „…“; Spanish « … »; Italian « … »; Arabic « … »; Japanese 「…」; Korean “…”; Vietnamese “…”; Portuguese « … » or “…” consistently; Russian « … »; Chinese 「…」 or “…” consistently. If the target language is not listed, use the most natural quotation style for that language and use it consistently.
12. Avoid parentheses, long dash asides, semicolon chains, and deeply nested clauses. They make TTS and subtitle timing fragile.
13. Avoid ellipses unless they are part of a fixed teaching pattern such as "some... others..."; never use ellipses as dramatic punctuation.
14. Some Chinese TTS markers may have been replaced by opaque marker tokens. Use the marker glossary below to understand what each token refers to, but keep any token already present in the input exactly as written in your output.
15. The period, question mark, or exclamation mark in your output will become a timing boundary for subtitles. Make every sentence boundary meaningful."""
    else:
        field_rules = f"""
Field-specific rules:
8. For short UI labels, vocabulary definitions, grammar notes, quiz answers, and examples, stay concise and faithful to the source meaning.
9. Keep the result appropriate for a language-learning app: clear, learner-friendly, and not overly literary.
10. If a field is a single word or short phrase, return a single word or short phrase when possible."""
    return f"""You are a professional translator for Chinese language learning materials. Translate each English string below into {lang_name}.

Rules:
1. Output ONLY valid JSON with the exact same keys. No markdown, no extra text.
2. Preserve every opaque marker token byte-for-byte exactly as-is. These tokens protect Chinese/pinyin TTS markers. Never translate, transliterate, romanize, respell, reorder, delete, duplicate, or localize punctuation inside these tokens.
2a. Never invent marker tokens. If a source string has Chinese words written as plain text, keep those Chinese words as plain text; do not wrap them, replace them with marker tokens, or copy marker tokens from another key.
3. Write as a native {lang_name} speaker would naturally say it — prioritise idiomatic fluency over literal accuracy. Adapt sentence structure, phrasing, and examples to feel at home in {lang_name}.
4. NEVER keep English words or phrases in the output. When the source cites an English expression as an example (e.g. 'like "and you?" in English'), replace it with the natural {lang_name} equivalent and drop any reference to English.
5. Avoid parentheses ( ), brackets [ ], and dashes used only for clarification — they interrupt TTS rhythm. Fold the clarifying content into the sentence naturally instead (e.g. "X, qui signifie Y," rather than "X (Y)").
6. For single-word vocabulary answers, give the most natural single-word (or short phrase) {lang_name} equivalent.
7. Keep narration text conversational and spoken-friendly — it will be read aloud by a TTS voice.
8. Because your answer must be machine-parsed as JSON, do not use raw ASCII double quotes (") inside translated string values. Use the target language quotation marks instead, such as « … », “ … ”, 「…」, or no quotes.
9. Before returning, verify that every opaque marker token in each value is identical to the corresponding input token. If any token changed, fix it before output.
{field_rules}

Marker glossary for understanding only. Do not output glossary lines. Keep tokens in the translated strings exactly as tokens:
{glossary_text}

Input:
{payload}

Output (JSON only):"""


# ── JSON walker ───────────────────────────────────────────────────────────────

def _collect_translatable(data: dict) -> list:
    """Return list of (dotted_path, english_text) for all translatable fields."""
    items = []

    # 0. Lesson title
    if data.get("lesson_metadata", {}).get("title_localized"):
        items.append(("lesson_metadata.title_localized", data["lesson_metadata"]["title_localized"]))

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
        # example_sentence: some lessons use "translation", older ones use "en"
        es = vocab.get("example_sentence", {})
        if isinstance(es, dict):
            es_text = es.get("translation") or es.get("en", "")
            if es_text:
                es_field = "translation" if "translation" in es else "en"
                items.append((f"{base}.example_sentence.{es_field}", es_text))
        # historical_usages: translate display fields while preserving Chinese anchors.
        for hu_idx, hu in enumerate(vocab.get("historical_usages", [])):
            if not isinstance(hu, dict):
                continue
            hu_base = f"{base}.historical_usages.{hu_idx}"
            if hu.get("definition"):
                items.append((f"{hu_base}.definition", hu["definition"]))
            if hu.get("part_of_speech"):
                items.append((f"{hu_base}.part_of_speech", hu["part_of_speech"]))
            for ex_key in ("representative_example", "example"):
                ex = hu.get(ex_key)
                if not isinstance(ex, dict):
                    continue
                ex_text = ex.get("translation") or ex.get("en", "")
                if ex_text:
                    ex_field = "translation" if "translation" in ex else "en"
                    items.append((f"{hu_base}.{ex_key}.{ex_field}", ex_text))

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
        # Newer lessons use "translation", older ones use "en"
        for cx_idx, cx in enumerate(item.get("context_examples", [])):
            cx_text = cx.get("translation") or cx.get("en", "")
            if cx_text:
                items.append((f"{base}.context_examples.{cx_idx}.translation", cx_text))
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

_ZH_MARKER_RE = re.compile(r"\[zh:[^\]]*\]")
_ZH_TOKEN_RE = re.compile(r"__ZH_[A-Z0-9]+_\d{4}__")


def _zh_markers(text: object) -> list[str]:
    return _ZH_MARKER_RE.findall(text) if isinstance(text, str) else []


def _protect_zh_markers(text: object, key: str) -> tuple[object, dict[str, str]]:
    if not isinstance(text, str):
        return text, {}

    marker_map: dict[str, str] = {}
    token_key = re.sub(r"[^A-Za-z0-9]", "", key).upper() or "T0000"

    def replace(match: re.Match) -> str:
        token = f"__ZH_{token_key}_{len(marker_map):04d}__"
        marker_map[token] = match.group(0)
        return token

    return _ZH_MARKER_RE.sub(replace, text), marker_map


def _restore_zh_markers(text: object, marker_map: dict[str, str]) -> object:
    if not isinstance(text, str):
        return text
    restored = text
    for token, marker in marker_map.items():
        restored = restored.replace(token, marker)
    return restored


def _marker_inner(marker: str) -> str:
    return marker[4:-1] if marker.startswith("[zh:") and marker.endswith("]") else marker


def _downgrade_unexpected_tokens(
    text: object,
    allowed_tokens: set[str],
    all_marker_maps: dict[str, dict[str, str]],
) -> object:
    if not isinstance(text, str):
        return text
    global_markers = {
        token: marker
        for marker_map in all_marker_maps.values()
        for token, marker in marker_map.items()
    }

    def replace(match: re.Match) -> str:
        token = match.group(0)
        if token in allowed_tokens:
            return token
        marker = global_markers.get(token)
        return _marker_inner(marker) if marker else token

    return _ZH_TOKEN_RE.sub(replace, text)


def _token_mismatches(source: dict, result: dict) -> list[str]:
    problems = []
    for key, source_text in source.items():
        if key not in result:
            continue
        expected = _ZH_TOKEN_RE.findall(source_text) if isinstance(source_text, str) else []
        actual = _ZH_TOKEN_RE.findall(result[key]) if isinstance(result.get(key), str) else []
        missing = [token for token in expected if actual.count(token) < expected.count(token)]
        unexpected = [token for token in actual if token not in expected]
        if missing or unexpected:
            detail = f"expected marker tokens present: {expected}, got {actual}"
            if missing:
                detail += f", missing tokens: {missing}"
            if unexpected:
                detail += f", unexpected tokens: {unexpected}"
            problems.append(f"{key}: {detail}")
    return problems


def _translate_batch(llm, lang_name: str, batch_dict: dict, mode: str = "general", fallback_llm=None) -> dict:
    protected_batch = {}
    marker_maps: dict[str, dict[str, str]] = {}
    for key, value in batch_dict.items():
        protected, marker_map = _protect_zh_markers(value, key)
        protected_batch[key] = protected
        marker_maps[key] = marker_map

    prompt = _build_translate_prompt(lang_name, protected_batch, mode=mode, marker_glossary=marker_maps)
    last_result = {}
    for attempt in range(1, 4):
        # 第 1 次用主模型（fast/cheap）；一旦失败立即升级到 fallback（更强模型）
        current_llm = fallback_llm if (attempt > 1 and fallback_llm is not None) else llm
        if attempt == 2 and fallback_llm is not None:
            print(f"  🔼 升级到备用模型重试: {getattr(current_llm, 'model_id', type(current_llm).__name__)}")
        result = current_llm.generate_structured_json(prompt, file_path=None)
        if isinstance(result, dict):
            last_result = result
            mismatches = _token_mismatches(protected_batch, result)
            if not mismatches:
                restored = {}
                for key, value in result.items():
                    restored[key] = _restore_zh_markers(value, marker_maps.get(key, {}))
                return restored
            preview = "; ".join(mismatches[:3])
            print(f"  ⚠️  [zh:] placeholder 被改写，重试 batch ({attempt}/3): {preview}")
            continue
        print(f"  ⚠️  Unexpected translation result type: {type(result)}, retrying batch ({attempt}/3).")

    if isinstance(last_result, dict) and last_result:
        restored = {}
        for key, source_value in batch_dict.items():
            candidate = last_result.get(key)
            expected_tokens = set(_ZH_TOKEN_RE.findall(protected_batch.get(key, "")))
            candidate = _downgrade_unexpected_tokens(candidate, expected_tokens, marker_maps)
            if key in last_result and not _token_mismatches({key: protected_batch[key]}, {key: candidate}):
                restored[key] = _restore_zh_markers(candidate, marker_maps.get(key, {}))
            else:
                restored[key] = source_value
        print("  ⚠️  [zh:] placeholder 多次重试后仍不一致；已降级误加 token，仍异常的字段保留源文本。")
        return restored

    print("  ⚠️  翻译 batch 多次失败；保留源文本。")
    return dict(batch_dict)


def _run_translation(llm, lang_name: str, items: list, fallback_llm=None) -> dict:
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
        result = _translate_batch(llm, lang_name, batch_dict, mode="general", fallback_llm=fallback_llm)
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
        result = _translate_batch(llm, lang_name, batch_dict, mode="narration", fallback_llm=fallback_llm)
        for i, (path, _) in enumerate(batch):
            key = f"n{start + i:04d}"
            if key in result:
                translated_map[path] = result[key]

    return translated_map


# ── Main per-file logic ───────────────────────────────────────────────────────

def translate_lesson(source_path: Path, lang: str, llm, fallback_llm=None) -> dict:
    lang_name = LANG_META[lang]["name"]

    with open(source_path, encoding="utf-8") as f:
        data = json.load(f)

    translated = copy.deepcopy(data)
    items = _collect_translatable(data)
    print(f"  🔍 Found {len(items)} translatable strings ({sum(1 for p, _ in items if 'subtitle_en' in p)} narration segments)")

    translated_map = _run_translation(llm, lang_name, items, fallback_llm=fallback_llm)
    hits = len(translated_map)
    print(f"  ✅ Translated {hits}/{len(items)} strings")

    for path, value in translated_map.items():
        _set_by_path(translated, path, value)

    # Remap question_type for each database_item
    type_remap = _TYPE_REMAP.get(lang, {})
    if type_remap:
        for item in translated.get("database_items", []):
            if isinstance(item, dict) and item.get("question_type") in type_remap:
                item["question_type"] = type_remap[item["question_type"]]
        remapped = sum(1 for item in translated.get("database_items", [])
                       if isinstance(item, dict) and item.get("question_type", "").startswith(lang.upper()))
        print(f"  🔁 question_type 已重命名（{remapped} 项 → {lang.upper()}_* 格式）")

    translated["localization"] = {
        "source_lang": "en",
        "target_lang": lang,
        "target_lang_name": lang_name,
        "target_lang_native": LANG_META[lang]["native"],
    }
    _reset_render_outputs(translated)

    return translated


def _reset_render_outputs(data: dict) -> None:
    """Remove generated render artifacts from a localized JSON draft.

    Localization starts from the English source JSON, which may already contain
    English narration timings, sentence text lists, audio paths, or video paths.
    Target-language JSON should keep only the translated render plan; Stage 2
    writes target-language sentence_texts, timings, durations, and artifact paths.
    """
    data.pop("explanation_narration_audio", None)
    data.pop("explanation_video_urls", None)

    explanation = data.get("video_render_plan", {}).get("explanation", {})
    segments = explanation.get("segments", []) if isinstance(explanation, dict) else []
    for seg in segments if isinstance(segments, list) else []:
        if not isinstance(seg, dict):
            continue
        seg.pop("sentence_texts", None)
        seg.pop("sentence_timings_seconds", None)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Translate lesson JSON to a target language")
    parser.add_argument("--lang", required=True, help="Target language code: fr, de, es, ja, ko")
    parser.add_argument("--lesson", help="Lesson ID (e.g. 101 → lesson101_data.json)")
    parser.add_argument(
        "--pipeline",
        default="integrated_chinese",
        help="教材流水线 ID（默认: integrated_chinese）。",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing localized JSON files instead of skipping them.",
    )
    parser.add_argument("files", nargs="*", help="JSON file name(s) in output_json/ (default: all)")
    args = parser.parse_args()

    lang = args.lang
    if lang not in LANG_META:
        print(f"❌ Unknown language '{lang}'. Supported: {', '.join(LANG_META.keys())}")
        sys.exit(1)

    paths = default_paths()
    pipeline = get_pipeline(args.pipeline)
    json_dir = pipeline.output_json_dir(paths, "en")
    if not list(json_dir.glob("lesson*_data.json")):
        fallback_json_dir = pipeline.synced_json_dir(paths, "en")
        if fallback_json_dir.exists() and list(fallback_json_dir.glob("lesson*_data.json")):
            print(f"ℹ️ output_json/en 为空，改用 synced_json/en 作为英文源: {fallback_json_dir}")
            json_dir = fallback_json_dir
    out_dir = pipeline.output_json_dir(paths, lang)
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

    from core.llm_providers import LLMFactory
    llm = pipeline.create_provider()
    fallback_llm = LLMFactory.create_fallback_provider()
    lang_display = f"{LANG_META[lang]['name']} ({LANG_META[lang]['native']})"
    print(f"🧭 Pipeline: {pipeline.display_name} ({pipeline.pipeline_id})")
    print(f"🤖 主模型: {getattr(llm, 'model_id', type(llm).__name__)}", end="")
    if fallback_llm:
        print(f"  |  备用模型: {getattr(fallback_llm, 'model_id', type(fallback_llm).__name__)}")
    else:
        print("  |  备用模型: 未配置（LLM_CONTENT_GEMINI_FALLBACK_MODEL_ID）")
    print(f"\n🌐 Localizing {len(files)} file(s) → {lang_display}\n")

    for source_path in files:
        if not source_path.exists():
            print(f"⚠️  Not found: {source_path.name}, skipping.")
            continue
        stem = source_path.stem  # e.g. lesson101_data
        out_path = out_dir / f"{stem}_{lang}.json"
        if out_path.exists() and not args.force:
            print(f"⏭️  Already exists: {out_path.name}, skipping.")
            continue
        if out_path.exists() and args.force:
            print(f"♻️  Overwriting existing: {out_path.name}")

        print(f"📝 {source_path.name}  →  {out_path.name}")
        result = translate_lesson(source_path, lang, llm, fallback_llm=fallback_llm)
        result["pipeline_id"] = pipeline.pipeline_id
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  💾 Saved → {out_path}\n")

    print("✨ Done.")


if __name__ == "__main__":
    main()
