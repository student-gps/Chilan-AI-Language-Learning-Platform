from __future__ import annotations

import re
from typing import Any, Mapping


PRACTICE_SCHEMA_VERSION = 2
CANONICAL_QUESTION_TYPES = {
    "TRANSLATE",
    "SPEAK",
    "LISTEN_WRITE",
    "PATTERN_DRILL",
    "PARTICLE_FILL",
    "CONJUGATION",
    "TONE_MARKING",
    "MEASURE_WORD_FILL",
    "SENTENCE_SOURCE_TO_TARGET",
    "SENTENCE_TARGET_TO_SOURCE",
    "VOCAB_SOURCE_TO_TARGET",
    "VOCAB_TARGET_TO_SOURCE",
}

_LANGUAGE_ALIASES = {
    "cn": "zh",
    "zh": "zh",
    "chinese": "zh",
    "jp": "ja",
    "ja": "ja",
    "japanese": "ja",
    "en": "en",
    "english": "en",
    "fr": "fr",
    "french": "fr",
    "de": "de",
    "german": "de",
    "ko": "ko",
    "korean": "ko",
    "ru": "ru",
    "russian": "ru",
    "es": "es",
    "spanish": "es",
    "pt": "pt",
    "portuguese": "pt",
    "vi": "vi",
    "vietnamese": "vi",
    "th": "th",
    "thai": "th",
    "ar": "ar",
    "arabic": "ar",
    "it": "it",
    "italian": "it",
    "id": "id",
    "indonesian": "id",
    "ms": "ms",
    "malay": "ms",
}

_DIRECTION_PATTERN = re.compile(r"^(?P<prompt>[A-Z]+)_TO_(?P<answer>[A-Z]+)$")
_DIRECTION_SPEAK_PATTERN = re.compile(r"^(?P<prompt>[A-Z]+)_TO_(?P<answer>[A-Z]+)_SPEAK$")


class PracticeItemSchemaError(ValueError):
    """Raised when an exercise cannot be represented by the canonical schema."""


def normalize_language_code(value: Any, *, field_name: str = "language") -> str:
    normalized = str(value or "").strip().lower()
    resolved = _LANGUAGE_ALIASES.get(normalized)
    if not resolved:
        raise PracticeItemSchemaError(f"{field_name} must be a supported language code; got {value!r}")
    return resolved


def build_practice_metadata(
    *,
    prompt_language: str,
    answer_language: str,
    feedback_language: str,
    answer_mode: str,
    speech_language: str | None = None,
    audio_language: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the schema-v2 fields while preserving caller-owned metadata."""
    normalized = dict(metadata) if isinstance(metadata, Mapping) else {}
    normalized.update({
        "practice_schema_version": PRACTICE_SCHEMA_VERSION,
        "prompt_language": normalize_language_code(prompt_language, field_name="prompt_language"),
        "answer_language": normalize_language_code(answer_language, field_name="answer_language"),
        "feedback_language": normalize_language_code(feedback_language, field_name="feedback_language"),
        "answer_mode": str(answer_mode or "").strip().lower(),
    })
    if speech_language:
        normalized["speech_language"] = normalize_language_code(speech_language, field_name="speech_language")
    if audio_language:
        normalized["audio_language"] = normalize_language_code(audio_language, field_name="audio_language")
    return normalized


def _defaults(defaults: Mapping[str, Any] | None) -> dict[str, str]:
    source = defaults if isinstance(defaults, Mapping) else {}
    normalized: dict[str, str] = {}
    for source_key, canonical_key in (
        ("prompt_language", "prompt_language"),
        ("answer_language", "answer_language"),
        ("feedback_language", "feedback_language"),
        ("course_target_language", "course_target_language"),
        ("course_support_language", "course_support_language"),
        ("target_language", "course_target_language"),
        ("support_language", "course_support_language"),
    ):
        if source.get(source_key):
            normalized[canonical_key] = normalize_language_code(source[source_key], field_name=source_key)
    return normalized


def _first_language(metadata: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        if metadata.get(key):
            return normalize_language_code(metadata[key], field_name=key)
    return None


def _legacy_type_context(
    question_type: str,
    metadata: Mapping[str, Any],
    defaults: Mapping[str, str],
) -> tuple[str, str, str, str, str] | None:
    """Return canonical type, prompt, answer, feedback, and answer mode for a legacy type."""
    normalized_type = question_type.strip().upper()
    feedback_language = _first_language(metadata, "feedback_language") or defaults.get("feedback_language")

    if normalized_type == "PATTERN_DRILL":
        prompt = _first_language(metadata, "prompt_language", "support_language", "source_language") or defaults.get("course_support_language")
        answer = _first_language(metadata, "answer_language", "target_language") or defaults.get("course_target_language")
        feedback = feedback_language or prompt
        if not (prompt and answer and feedback):
            return None
        return "PATTERN_DRILL", prompt, answer, feedback, "text"

    if normalized_type == "SUPPORT_TO_TARGET":
        prompt = _first_language(metadata, "prompt_language", "support_language", "source_language") or defaults.get("course_support_language")
        answer = _first_language(metadata, "answer_language", "target_language") or defaults.get("course_target_language")
        feedback = feedback_language or prompt
        if not (prompt and answer and feedback):
            return None
        return "PATTERN_DRILL", prompt, answer, feedback, "text"

    if normalized_type in {"TARGET_TO_SUPPORT", "TARGET_LISTEN_WRITE", "TARGET_SPEAK"}:
        target = _first_language(metadata, "target_language", "answer_language") or defaults.get("course_target_language")
        support = _first_language(metadata, "support_language", "prompt_language", "source_language") or defaults.get("course_support_language")
        feedback = feedback_language or support
        if not (target and support and feedback):
            return None
        if normalized_type == "TARGET_TO_SUPPORT":
            return "TRANSLATE", target, support, feedback, "text"
        if normalized_type == "TARGET_LISTEN_WRITE":
            return "LISTEN_WRITE", support, target, feedback, "text"
        return "SPEAK", support, target, feedback, "speech"

    if normalized_type in {"CN_LISTEN_WRITE", "JA_LISTEN_WRITE"}:
        answer = "zh" if normalized_type == "CN_LISTEN_WRITE" else "ja"
        prompt = _first_language(metadata, "prompt_language", "support_language", "source_language") or defaults.get("course_support_language")
        feedback = feedback_language or prompt
        if not prompt:
            return None
        return "LISTEN_WRITE", prompt, answer, feedback, "text"

    if normalized_type in {"JA_SPEAK"}:
        prompt = _first_language(metadata, "prompt_language", "support_language", "source_language") or defaults.get("course_support_language")
        feedback = feedback_language or prompt
        if not prompt:
            return None
        return "SPEAK", prompt, "ja", feedback, "speech"

    speak_match = _DIRECTION_SPEAK_PATTERN.match(normalized_type)
    if speak_match:
        prompt = normalize_language_code(speak_match.group("prompt"), field_name="legacy question_type")
        answer = normalize_language_code(speak_match.group("answer"), field_name="legacy question_type")
        feedback = feedback_language or defaults.get("course_support_language") or prompt
        return "SPEAK", prompt, answer, feedback, "speech"

    direction_match = _DIRECTION_PATTERN.match(normalized_type)
    if direction_match:
        prompt = normalize_language_code(direction_match.group("prompt"), field_name="legacy question_type")
        answer = normalize_language_code(direction_match.group("answer"), field_name="legacy question_type")
        feedback = feedback_language or defaults.get("course_support_language") or prompt
        return "TRANSLATE", prompt, answer, feedback, "text"

    return None


def canonicalize_practice_item(
    question_type: str,
    metadata: Mapping[str, Any] | None,
    *,
    defaults: Mapping[str, Any] | None = None,
    retire_legacy_fields: bool = False,
) -> tuple[str, dict[str, Any]]:
    """Return a canonical type and validated schema-v2 metadata.

    Legacy direction-encoded types are accepted only to support explicit artifact
    and database migrations. New generators must call this with a canonical type.
    """
    raw_metadata = dict(metadata) if isinstance(metadata, Mapping) else {}
    normalized_type = str(question_type or "").strip().upper()
    if not normalized_type:
        raise PracticeItemSchemaError("question_type is required")

    normalized_defaults = _defaults(defaults)
    canonical_type = normalized_type
    prompt_language = _first_language(raw_metadata, "prompt_language", "support_language", "source_language")
    answer_language = _first_language(raw_metadata, "answer_language", "target_language")
    feedback_language = _first_language(raw_metadata, "feedback_language", "support_language", "source_language")
    answer_mode = str(raw_metadata.get("answer_mode") or "").strip().lower()

    if canonical_type not in CANONICAL_QUESTION_TYPES:
        legacy = _legacy_type_context(normalized_type, raw_metadata, normalized_defaults)
        if legacy is None:
            raise PracticeItemSchemaError(
                f"Cannot canonicalize legacy question_type={normalized_type!r}; "
                "provide explicit language metadata and course defaults."
            )
        canonical_type, prompt_language, answer_language, feedback_language, answer_mode = legacy

    prompt_language = (
        prompt_language
        or normalized_defaults.get("prompt_language")
        or normalized_defaults.get("course_support_language")
    )
    answer_language = (
        answer_language
        or normalized_defaults.get("answer_language")
        or normalized_defaults.get("course_target_language")
    )
    feedback_language = (
        feedback_language
        or normalized_defaults.get("feedback_language")
        or normalized_defaults.get("course_support_language")
    )

    if canonical_type in {
        "TRANSLATE",
        "PATTERN_DRILL",
        "PARTICLE_FILL",
        "CONJUGATION",
        "TONE_MARKING",
        "MEASURE_WORD_FILL",
        "SENTENCE_SOURCE_TO_TARGET",
        "SENTENCE_TARGET_TO_SOURCE",
        "VOCAB_SOURCE_TO_TARGET",
        "VOCAB_TARGET_TO_SOURCE",
    }:
        answer_mode = answer_mode or "text"
    elif canonical_type == "SPEAK":
        answer_mode = answer_mode or "speech"
    elif canonical_type == "LISTEN_WRITE":
        answer_mode = answer_mode or "text"

    if answer_mode not in {"text", "speech"}:
        raise PracticeItemSchemaError(f"answer_mode must be 'text' or 'speech'; got {answer_mode!r}")
    if canonical_type == "SPEAK" and answer_mode != "speech":
        raise PracticeItemSchemaError("SPEAK items must use answer_mode='speech'")
    if canonical_type != "SPEAK" and answer_mode != "text":
        raise PracticeItemSchemaError(f"{canonical_type} items must use answer_mode='text'")
    if not (prompt_language and answer_language and feedback_language):
        raise PracticeItemSchemaError(
            f"{canonical_type} requires prompt_language, answer_language, and feedback_language"
        )

    speech_language = _first_language(raw_metadata, "speech_language")
    audio_language = _first_language(raw_metadata, "audio_language")
    if canonical_type == "SPEAK":
        speech_language = speech_language or answer_language
        if speech_language != answer_language:
            raise PracticeItemSchemaError("speech_language must match answer_language for SPEAK items")
    if canonical_type == "LISTEN_WRITE":
        audio_language = audio_language or answer_language
        if audio_language != answer_language:
            raise PracticeItemSchemaError("audio_language must match answer_language for LISTEN_WRITE items")

    normalized = build_practice_metadata(
        prompt_language=prompt_language,
        answer_language=answer_language,
        feedback_language=feedback_language,
        answer_mode=answer_mode,
        speech_language=speech_language,
        audio_language=audio_language,
        metadata=raw_metadata,
    )
    if retire_legacy_fields:
        for key in ("target_language", "targetLanguage", "support_language", "supportLanguage", "source_language", "sourceLanguage"):
            normalized.pop(key, None)
    return canonical_type, normalized


def canonicalize_database_item(
    item: Mapping[str, Any],
    *,
    defaults: Mapping[str, Any],
    retire_legacy_fields: bool = True,
) -> dict[str, Any]:
    """Return a copy of a persisted exercise with canonical type and metadata."""
    normalized = dict(item)
    question_type, metadata = canonicalize_practice_item(
        normalized.get("question_type", ""),
        normalized.get("metadata"),
        defaults=defaults,
        retire_legacy_fields=retire_legacy_fields,
    )
    normalized["question_type"] = question_type
    normalized["metadata"] = metadata
    return normalized


def canonicalize_database_items(
    items: list[Mapping[str, Any]],
    *,
    defaults: Mapping[str, Any],
    retire_legacy_fields: bool = True,
) -> list[dict[str, Any]]:
    """Canonicalize a generated item list without mutating source objects."""
    return [
        canonicalize_database_item(item, defaults=defaults, retire_legacy_fields=retire_legacy_fields)
        for item in items
        if isinstance(item, Mapping)
    ]
