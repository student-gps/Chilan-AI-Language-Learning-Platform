from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator


BOOK_NUMBER = 1
COURSE_ID = 201
COURSE_SLUG = "minna_no_nihongo_1"
TEXTBOOK_NAME = "Minna no Nihongo"
TEXTBOOK_NAME_JA = "みんなの日本語"
TEXTBOOK_NAME_ZH = "大家的日本语"
LESSON_COUNT = 50


@dataclass(frozen=True)
class LessonProfile:
    """Stable app lesson identity for the elementary Minna no Nihongo lessons.

    Page ranges are intentionally not encoded here yet because different
    scans/editions often shift pages. Once the user's PDFs are in place, this
    profile can grow a page map without changing the rest of the pipeline.
    """

    book: int
    lesson_id: int
    lesson_slug: str
    source_lesson: int
    textbook_name: str = TEXTBOOK_NAME
    textbook_name_ja: str = TEXTBOOK_NAME_JA
    textbook_name_zh: str = TEXTBOOK_NAME_ZH
    course_slug: str = COURSE_SLUG
    content_type: str = "sentence_pattern_dialogue"
    pedagogy_profile: str = "elementary_sentence_pattern_dialogue"
    source_sections: tuple[str, ...] = ("文型", "例文", "会話", "練習A/B/C", "問題")


def format_lesson_slug(lesson_id: int) -> str:
    _validate_lesson_id(lesson_id)
    return f"lesson{lesson_id:03d}"


def lesson_profile(lesson_id: int) -> LessonProfile:
    _validate_lesson_id(lesson_id)
    return LessonProfile(
        book=BOOK_NUMBER,
        lesson_id=lesson_id,
        lesson_slug=format_lesson_slug(lesson_id),
        source_lesson=lesson_id,
    )


def iter_lesson_profiles(start: int = 1, end: int = LESSON_COUNT) -> Iterator[LessonProfile]:
    _validate_lesson_id(start)
    _validate_lesson_id(end)
    if start > end:
        raise ValueError(f"start must be <= end; got {start}>{end}")
    for lesson_id in range(start, end + 1):
        yield lesson_profile(lesson_id)


def _validate_lesson_id(lesson_id: int) -> None:
    if not isinstance(lesson_id, int):
        raise TypeError("lesson_id must be an integer")
    if lesson_id < 1 or lesson_id > LESSON_COUNT:
        raise ValueError(f"lesson_id must be between 1 and {LESSON_COUNT}; got {lesson_id}")
