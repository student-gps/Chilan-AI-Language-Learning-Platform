"""Generate reviewed learner-language copy for the Japanese foundation pages.

The English foundation and course-introduction objects are the schema and
meaning source. Translations are cached beside the ignored local audio output,
then compiled into one frontend ES module after every locale validates.

Examples:
    python generate_japanese_foundation_translations.py
    python generate_japanese_foundation_translations.py --languages ja fr de
    python generate_japanese_foundation_translations.py --overwrite
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parent
FRONTEND_DIR = REPO_ROOT / "frontend"
FOUNDATION_CONTENT = FRONTEND_DIR / "src" / "pages" / "japaneseFoundation" / "foundationContent.js"
INTRO_CONTENT = FRONTEND_DIR / "src" / "videoTemplates" / "courseIntro" / "japaneseCourseIntroContent.js"
OUTPUT_MODULE = FRONTEND_DIR / "src" / "japaneseFoundationTranslations.generated.js"
CACHE_DIR = FRONTEND_DIR / "public" / "audio" / "japanese-foundations" / ".translation-cache"

sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from config.env import get_env  # noqa: E402
from content_builder.core.llm_providers import OpenAIProvider  # noqa: E402


TARGET_LANGUAGES = {
    "ja": "Japanese (日本語)",
    "fr": "French (Français)",
    "de": "German (Deutsch)",
    "ko": "Korean (한국어)",
    "es": "Spanish (Español)",
    "vi": "Vietnamese (Tiếng Việt)",
    "pt": "Brazilian Portuguese (Português do Brasil)",
    "ar": "Modern Standard Arabic (العربية الفصحى)",
    "th": "Thai (ไทย)",
    "ru": "Russian (Русский)",
    "id": "Indonesian (Bahasa Indonesia)",
    "ms": "Malay (Bahasa Melayu)",
    "it": "Italian (Italiano)",
}

CARD_SOURCE = {
    "course_japanese_intro_card_title": "Japanese Course Guide",
    "course_japanese_intro_card_sub": "Writing systems · method · path",
    "course_japanese_kana_card_title": "Kana Basics",
    "course_japanese_kana_card_sub": "Hiragana · katakana · combinations",
    "course_japanese_pronunciation_card_title": "Pronunciation",
    "course_japanese_pronunciation_card_sub": "Vowels · morae · special sounds",
    "course_japanese_kanji_card_title": "Japanese Kanji",
    "course_japanese_kanji_card_sub": "Readings · components · context",
    "course_japanese_typing_card_title": "Japanese Typing",
    "course_japanese_typing_card_sub": "IME · romaji · kana-to-kanji",
}

# Small human-reviewed corrections for strings that should follow the user's
# operating-system locale rather than remain as English UI labels.
CURATED_SCORE_LABELS = {
    "fr": "Résultat : {{score}} / {{total}}",
}

CURATED_PLATFORM_FIRST_STEPS = {
    "de": [
        "Einstellungen → Zeit und Sprache → Sprache und Region.",
        "Systemeinstellungen → Tastatur → Texteingabe → Bearbeiten.",
        "Einstellungen → Allgemein → Tastatur → Tastaturen.",
        "Gboard-Einstellungen → Sprachen öffnen.",
    ],
    "ko": [
        "설정 → 시간 및 언어 → 언어 및 지역.",
        "시스템 설정 → 키보드 → 텍스트 입력 → 편집.",
        "설정 → 일반 → 키보드 → 키보드.",
        "Gboard 설정 → 언어를 여세요.",
    ],
    "vi": [
        "Cài đặt → Thời gian & ngôn ngữ → Ngôn ngữ & khu vực.",
        "Cài đặt hệ thống → Bàn phím → Nhập văn bản → Sửa.",
        "Cài đặt → Cài đặt chung → Bàn phím → Bàn phím.",
        "Mở phần Cài đặt Gboard → Ngôn ngữ.",
    ],
    "ar": [
        "الإعدادات ← الوقت واللغة ← اللغة والمنطقة.",
        "إعدادات النظام ← لوحة المفاتيح ← إدخال النص ← تحرير.",
        "الإعدادات ← عام ← لوحة المفاتيح ← لوحات المفاتيح.",
        "افتح إعدادات Gboard ← اللغات.",
    ],
    "th": [
        "การตั้งค่า → เวลาและภาษา → ภาษาและภูมิภาค",
        "การตั้งค่าระบบ → แป้นพิมพ์ → การป้อนข้อความ → แก้ไข",
        "การตั้งค่า → ทั่วไป → แป้นพิมพ์ → แป้นพิมพ์",
        "เปิดการตั้งค่า Gboard → ภาษา",
    ],
    "ru": [
        "Параметры → Время и язык → Язык и регион.",
        "Системные настройки → Клавиатура → Ввод текста → Изменить.",
        "Настройки → Основные → Клавиатура → Клавиатуры.",
        "Откройте настройки Gboard → Языки.",
    ],
    "id": [
        "Pengaturan → Waktu & bahasa → Bahasa & wilayah.",
        "Pengaturan Sistem → Papan Ketik → Input Teks → Edit.",
        "Pengaturan → Umum → Papan Ketik → Papan Ketik.",
        "Buka Setelan Gboard → Bahasa.",
    ],
    "ms": [
        "Tetapan → Masa & bahasa → Bahasa & rantau.",
        "Tetapan Sistem → Papan Kekunci → Input Teks → Edit.",
        "Tetapan → Umum → Papan Kekunci → Papan Kekunci.",
        "Buka Tetapan Gboard → Bahasa.",
    ],
}


def load_source_payload() -> dict[str, Any]:
    script = f"""
import {{ FOUNDATION_COPY }} from {json.dumps(FOUNDATION_CONTENT.as_uri())};
import {{ JAPANESE_COURSE_INTRO_COPY }} from {json.dumps(INTRO_CONTENT.as_uri())};
process.stdout.write(JSON.stringify({{
  foundation: FOUNDATION_COPY.en,
  intro: JAPANESE_COURSE_INTRO_COPY.en,
  cards: {json.dumps(CARD_SOURCE, ensure_ascii=False)},
}}));
"""
    result = subprocess.run(
        ["node", "--input-type=module", "--eval", script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return json.loads(result.stdout)


def build_provider() -> OpenAIProvider:
    api_key = get_env("LLM_CONTENT_OPENAI_API_KEY", "LLM_OPENAI_API_KEY")
    model_id = get_env("LLM_CONTENT_OPENAI_MODEL_ID")
    base_url = get_env("LLM_CONTENT_OPENAI_BASE_URL", default="")
    if not api_key or not model_id:
        raise ValueError("Missing LLM_CONTENT_OPENAI_API_KEY or LLM_CONTENT_OPENAI_MODEL_ID")
    return OpenAIProvider(api_key, model_id, base_url=base_url)


def translation_prompt(language_code: str, language_name: str, source: dict[str, Any]) -> str:
    source_json = json.dumps(source, ensure_ascii=False, separators=(",", ":"))
    return f"""You are a senior localization editor and a specialist in teaching Japanese to speakers of {language_name}.

Translate the learner-facing English in the JSON below into natural, accurate {language_name}. Silently review the complete translation for pedagogy, terminology, fluency, consistency, and slide length before returning it.

Mandatory rules:
1. Return exactly one JSON object with the same keys, nesting, array lengths, value types, and ordering. Never add or remove content.
2. Translate all learner-facing prose and labels. Do not leave ordinary English behind. Keep only established technical names or keyboard labels such as AI, FSRS, IME, Windows, macOS, iPhone, Android, Gboard, Space, Enter, Esc, and romaji where locally conventional.
3. Preserve Japanese characters, Japanese words and sentences, kana/kanji readings, romaji input sequences, IPA, URLs, emoji, color strings, numbering, symbols, and template tokens such as {{{{score}}}} exactly. Translate meanings and explanatory text around them.
4. Use the standard Japanese-learning terminology of {language_name}. Distinguish kana, morae, vowel length, small っ, ん, contracted sounds, on/kun readings, okurigana, and pitch accent precisely.
5. Write for a beginner learning Japanese, not as a literal machine translation. Keep instructions direct and reassuring. Keep slide titles, card labels, and slide body copy concise enough for a 16:9 presentation; narration may be conversational.
6. The source section named chineseTitle/chinesePairs was originally written for Chinese readers. For this non-Chinese localization, keep the JSON keys but adapt the displayed title and warnings into a useful general warning about deceptive or unexpected kanji vocabulary. Do not tell {language_name} readers to compare modern Chinese meanings.
7. Preserve the intended locale: code={language_code}. Use native punctuation and grammar. For Arabic, use clear Modern Standard Arabic while preserving Japanese and Latin technical tokens in readable form.

SOURCE JSON:
{source_json}
"""


def assert_same_shape(source: Any, translated: Any, path: str = "root") -> None:
    if isinstance(source, dict):
        if not isinstance(translated, dict):
            raise ValueError(f"{path}: expected object")
        if list(source) != list(translated):
            raise ValueError(f"{path}: object keys/order changed")
        for key in source:
            assert_same_shape(source[key], translated[key], f"{path}.{key}")
        return
    if isinstance(source, list):
        if not isinstance(translated, list) or len(source) != len(translated):
            raise ValueError(f"{path}: array shape changed")
        for index, (source_item, translated_item) in enumerate(zip(source, translated, strict=True)):
            assert_same_shape(source_item, translated_item, f"{path}[{index}]")
        return
    if type(source) is not type(translated):
        raise ValueError(f"{path}: scalar type changed")
    if isinstance(source, str):
        source_tokens = sorted(re.findall(r"\{\{[^{}]+\}\}", source))
        translated_tokens = sorted(re.findall(r"\{\{[^{}]+\}\}", translated))
        if source_tokens != translated_tokens:
            raise ValueError(f"{path}: template tokens changed")
        if source.startswith(("https://", "http://")) and translated != source:
            raise ValueError(f"{path}: URL changed")


def repair_known_wrapper_shape(source: Any, translated: Any) -> Any:
    """Repair a model's harmless early-close of the single foundation wrapper.

    Some otherwise complete responses close ``foundation`` between its two
    requested sections. Only repair when every top-level key is accounted for
    by the source's foundation keys and the reconstructed object is exact.
    """
    if not (
        isinstance(source, dict)
        and list(source) == ["foundation"]
        and isinstance(source["foundation"], dict)
        and isinstance(translated, dict)
        and isinstance(translated.get("foundation"), dict)
    ):
        return translated

    expected_inner_keys = list(source["foundation"])
    translated_inner = translated["foundation"]
    available_keys = set(translated_inner) | (set(translated) - {"foundation"})
    if available_keys != set(expected_inner_keys):
        return translated
    repaired = {
        "foundation": {
            key: translated_inner[key] if key in translated_inner else translated[key]
            for key in expected_inner_keys
        }
    }
    return repaired


def source_chunks(source: dict[str, Any]) -> dict[str, dict[str, Any]]:
    foundation = source["foundation"]
    return {
        "guide": {"foundation": {key: foundation[key] for key in ("common", "intro")}},
        "sound": {"foundation": {key: foundation[key] for key in ("kana", "pronunciation")}},
        "literacy": {"foundation": {key: foundation[key] for key in ("kanji", "typing")}},
        "slides": {"intro": source["intro"], "cards": source["cards"]},
    }


def assemble_chunks(source: dict[str, Any], chunks: dict[str, dict[str, Any]]) -> dict[str, Any]:
    translated_foundation_sections: dict[str, Any] = {}
    for chunk_name in ("guide", "sound", "literacy"):
        translated_foundation_sections.update(chunks[chunk_name]["foundation"])
    translated = {
        "foundation": {
            key: translated_foundation_sections[key]
            for key in source["foundation"]
        },
        "intro": chunks["slides"]["intro"],
        "cards": chunks["slides"]["cards"],
    }
    assert_same_shape(source, translated)
    return translated


def translate_locale(code: str, source: dict[str, Any], overwrite: bool) -> tuple[str, dict[str, Any], bool]:
    cache_path = CACHE_DIR / f"{code}.json"
    if cache_path.is_file() and not overwrite:
        try:
            translated = json.loads(cache_path.read_text(encoding="utf-8"))
            translated = repair_known_wrapper_shape(source, translated)
            assert_same_shape(source, translated)
            return code, translated, True
        except (ValueError, json.JSONDecodeError) as exc:
            print(f"  {code}: ignoring invalid full cache ({exc})", flush=True)

    provider = build_provider()
    translated_chunks: dict[str, dict[str, Any]] = {}
    generated_any = False
    for chunk_name, chunk_source in source_chunks(source).items():
        chunk_cache_path = CACHE_DIR / f"{code}.{chunk_name}.json"
        translated_chunk = None
        if chunk_cache_path.is_file() and not overwrite:
            try:
                cached_chunk = json.loads(chunk_cache_path.read_text(encoding="utf-8"))
                cached_chunk = repair_known_wrapper_shape(chunk_source, cached_chunk)
                assert_same_shape(chunk_source, cached_chunk)
                translated_chunk = cached_chunk
            except (ValueError, json.JSONDecodeError) as exc:
                print(f"  {code}.{chunk_name}: regenerating invalid cache ({exc})", flush=True)
        if translated_chunk is None:
            translated_chunk = provider.generate_structured_json(
                translation_prompt(code, TARGET_LANGUAGES[code], chunk_source)
            )
            translated_chunk = repair_known_wrapper_shape(chunk_source, translated_chunk)
            assert_same_shape(chunk_source, translated_chunk)
            chunk_cache_path.write_text(
                json.dumps(translated_chunk, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            generated_any = True
        translated_chunks[chunk_name] = translated_chunk
        print(f"  {code}.{chunk_name}: ready", flush=True)

    translated = assemble_chunks(source, translated_chunks)
    cache_path.write_text(
        json.dumps(translated, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return code, translated, not generated_any


def write_output(translations: dict[str, dict[str, Any]]) -> None:
    for code, score_label in CURATED_SCORE_LABELS.items():
        translations[code]["foundation"]["common"]["score"] = score_label
    for code, first_steps in CURATED_PLATFORM_FIRST_STEPS.items():
        platforms = translations[code]["foundation"]["typing"]["platforms"]
        if len(platforms) != len(first_steps):
            raise ValueError(f"Unexpected platform count for curated {code} steps")
        for platform, first_step in zip(platforms, first_steps, strict=True):
            platform["steps"][0] = first_step

    foundations = {code: item["foundation"] for code, item in translations.items()}
    intros = {code: item["intro"] for code, item in translations.items()}
    cards = {code: item["cards"] for code, item in translations.items()}
    preamble = (
        "// Generated by backend/generate_japanese_foundation_translations.py.\n"
        "// Do not edit individual strings here; update the English source or generator and regenerate.\n"
    )
    sections = [
        ("JAPANESE_FOUNDATION_TRANSLATIONS", foundations),
        ("JAPANESE_COURSE_INTRO_TRANSLATIONS", intros),
        ("JAPANESE_FOUNDATION_CARD_TRANSLATIONS", cards),
    ]
    body = "\n".join(
        f"export const {name} = {json.dumps(value, ensure_ascii=False, indent=2)};\n"
        for name, value in sections
    )
    OUTPUT_MODULE.write_text(preamble + body, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate all Japanese foundation translations")
    parser.add_argument("--languages", nargs="+", choices=TARGET_LANGUAGES, default=list(TARGET_LANGUAGES))
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    source = load_source_payload()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    translations: dict[str, dict[str, Any]] = {}
    existing_output_codes = set()
    failures: dict[str, str] = {}

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {
            executor.submit(translate_locale, code, source, args.overwrite): code
            for code in args.languages
        }
        for future in as_completed(futures):
            requested_code = futures[future]
            try:
                code, translated, cached = future.result()
                translations[code] = translated
                existing_output_codes.add(code)
                print(f"[{len(existing_output_codes)}/{len(args.languages)}] {code}: {'cache' if cached else 'generated'}", flush=True)
            except Exception as exc:  # keep other locale workers and caches progressing
                failures[requested_code] = str(exc)
                print(f"[FAILED] {requested_code}: {exc}", flush=True)

    if failures:
        details = "; ".join(f"{code}={message}" for code, message in failures.items())
        raise RuntimeError(f"Translation generation failed for {len(failures)} locale(s): {details}")

    missing = [code for code in TARGET_LANGUAGES if code not in translations]
    for code in missing:
        cache_path = CACHE_DIR / f"{code}.json"
        if not cache_path.is_file():
            raise ValueError(f"Missing translation cache for {code}; run without --languages to generate all locales")
        translated = json.loads(cache_path.read_text(encoding="utf-8"))
        assert_same_shape(source, translated)
        translations[code] = translated

    ordered = {code: translations[code] for code in TARGET_LANGUAGES}
    write_output(ordered)
    print(f"Wrote {OUTPUT_MODULE} with {len(ordered)} learner languages", flush=True)


if __name__ == "__main__":
    main()
