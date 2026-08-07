"""Canonical public course identities and course-scoped foundation modules.

The database keeps numeric ``course_id`` values for enrollment and progress. This
registry supplies stable public slugs and the set of frontend foundation modules
for each course family.
"""

from __future__ import annotations

from typing import Any


_LANGUAGE_CODE_BY_CATEGORY = {
    "AR": "ar",
    "CN": "zh",
    "DE": "de",
    "EN": "en",
    "ES": "es",
    "FR": "fr",
    "ID": "id",
    "IT": "it",
    "JA": "ja",
    "JP": "ja",
    "KO": "ko",
    "KR": "ko",
    "MS": "ms",
    "PT": "pt",
    "RU": "ru",
    "TH": "th",
    "VI": "vi",
}


def _normalize_language_code(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""

    exact_codes = {
        "ar": "ar",
        "cn": "zh",
        "de": "de",
        "en": "en",
        "es": "es",
        "fr": "fr",
        "id": "id",
        "it": "it",
        "ja": "ja",
        "jp": "ja",
        "ko": "ko",
        "kr": "ko",
        "ms": "ms",
        "pt": "pt",
        "ru": "ru",
        "th": "th",
        "vi": "vi",
        "zh": "zh",
        "zh-cn": "zh",
        "zh-hans": "zh",
    }
    if text in exact_codes:
        return exact_codes[text]

    contains_codes = (
        (("chinese", "中文", "chinois", "chinesisch", "mandarin"), "zh"),
        (("english", "英语", "anglais", "englisch"), "en"),
        (("japanese", "日本", "日语", "japonais", "japanisch"), "ja"),
        (("korean", "한국", "韩语", "coréen", "koreanisch"), "ko"),
        (("french", "français", "francais", "法语", "französisch"), "fr"),
        (("spanish", "español", "espanol", "西班牙语", "espagnol"), "es"),
        (("german", "deutsch", "德语", "allemand"), "de"),
        (("vietnamese", "tiếng việt", "tieng viet", "越南"), "vi"),
        (("portuguese", "português", "portugues", "葡萄牙"), "pt"),
        (("arabic", "عربية", "阿拉伯"), "ar"),
        (("thai", "ไทย", "泰语"), "th"),
        (("russian", "русский", "俄语"), "ru"),
        (("indonesian", "bahasa indonesia", "印尼"), "id"),
        (("malay", "bahasa melayu", "马来"), "ms"),
        (("italian", "italiano", "意大利"), "it"),
    )
    for markers, code in contains_codes:
        if any(marker in text for marker in markers):
            return code
    return ""


def _language_codes_from_category(category: Any) -> tuple[str, str]:
    parts = str(category or "").strip().upper().split("_TO_")
    if len(parts) != 2:
        return "", ""
    return (
        _LANGUAGE_CODE_BY_CATEGORY.get(parts[0], ""),
        _LANGUAGE_CODE_BY_CATEGORY.get(parts[1], ""),
    )


_CHINESE_FOUNDATIONS = (
    {
        "key": "intro",
        "position": 1,
        "implementation_key": "course-intro-v1",
        "title_key": "course_intro_card_title",
        "description_key": "course_intro_card_sub",
        "icon": "✨",
        "tone": "amber",
    },
    {
        "key": "hanzi",
        "position": 2,
        "implementation_key": "chinese-hanzi-v1",
        "title_key": "course_hanzi_card_title",
        "description_key": "course_hanzi_card_sub",
        "icon": "字",
        "tone": "indigo",
    },
    {
        "key": "pinyin",
        "position": 3,
        "implementation_key": "chinese-pinyin-v1",
        "title_key": "course_pinyin_card_title",
        "description_key": "course_pinyin_card_sub",
        "icon": "abc",
        "tone": "blue",
    },
    {
        "key": "typing",
        "position": 4,
        "implementation_key": "chinese-ime-v1",
        "title_key": "course_typing_card_title",
        "description_key": "course_typing_card_sub",
        "icon": "⌨",
        "tone": "emerald",
    },
)


def _foundation_modules(course_family: str) -> list[dict[str, Any]]:
    if course_family != "integrated_chinese":
        return []
    return [dict(module) for module in _CHINESE_FOUNDATIONS]


def public_course_definition(
    *,
    course_id: Any,
    category: Any = "",
    target_language: Any = "",
    source_language: Any = "",
) -> dict[str, Any]:
    """Return a stable frontend-facing identity for one legacy course row."""
    numeric_course_id = int(course_id)
    category_source, category_target = _language_codes_from_category(category)
    target_code = _normalize_language_code(target_language) or category_target
    support_code = _normalize_language_code(source_language) or category_source or "en"

    if target_code == "zh":
        course_family = "integrated_chinese"
        slug = f"integrated-chinese-{support_code}"
        pipeline_id = "integrated_chinese"
    elif numeric_course_id == 303:
        course_family = "minna_no_nihongo"
        slug = f"minna-no-nihongo-{support_code}"
        pipeline_id = "minna_no_nihongo"
    elif numeric_course_id == 101:
        course_family = "new_concept_english"
        slug = f"new-concept-english-{support_code}"
        pipeline_id = "new_concept_english"
    else:
        course_family = "generic"
        slug = f"course-{numeric_course_id}"
        pipeline_id = None

    return {
        "slug": slug,
        "course_family": course_family,
        "pipeline_id": pipeline_id,
        "target_language_code": target_code,
        "support_language_code": support_code,
        "foundations": _foundation_modules(course_family),
    }
