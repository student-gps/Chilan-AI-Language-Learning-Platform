from __future__ import annotations

from typing import Iterator

from content_builder.ja.minna_no_nihongo.book_profiles.book1 import LessonProfile


BOOK_NUMBER = 3
COURSE_ID = 201
COURSE_SLUG = "minna_no_nihongo_intermediate"
TEXTBOOK_NAME = "Minna no Nihongo Intermediate"
TEXTBOOK_NAME_JA = "みんなの日本語 中級"
TEXTBOOK_NAME_ZH = "大家的日语 中级"
FIRST_LESSON_ID = 51
LAST_LESSON_ID = 74
LESSON_COUNT = LAST_LESSON_ID - FIRST_LESSON_ID + 1
SOURCE_SECTIONS = ("読む・書く", "話す・聞く", "文法・練習")


def source_lesson_id(lesson_id: int) -> int:
    _validate_lesson_id(lesson_id)
    return lesson_id


def format_lesson_slug(lesson_id: int) -> str:
    _validate_lesson_id(lesson_id)
    return f"lesson{lesson_id:03d}"


def lesson_profile(lesson_id: int) -> LessonProfile:
    _validate_lesson_id(lesson_id)
    return LessonProfile(
        book=BOOK_NUMBER,
        lesson_id=lesson_id,
        lesson_slug=format_lesson_slug(lesson_id),
        source_lesson=source_lesson_id(lesson_id),
        textbook_name=TEXTBOOK_NAME,
        textbook_name_ja=TEXTBOOK_NAME_JA,
        textbook_name_zh=TEXTBOOK_NAME_ZH,
        course_slug=COURSE_SLUG,
        content_type="integrated_skills_intermediate",
        pedagogy_profile="intermediate_read_write_speak_listen_grammar",
        source_sections=SOURCE_SECTIONS,
    )


def iter_lesson_profiles(
    start: int = FIRST_LESSON_ID,
    end: int = LAST_LESSON_ID,
) -> Iterator[LessonProfile]:
    _validate_lesson_id(start)
    _validate_lesson_id(end)
    if start > end:
        raise ValueError(f"start must be <= end; got {start}>{end}")
    for lesson_id in range(start, end + 1):
        yield lesson_profile(lesson_id)


def _validate_lesson_id(lesson_id: int) -> None:
    if not isinstance(lesson_id, int):
        raise TypeError("lesson_id must be an integer")
    if lesson_id < FIRST_LESSON_ID or lesson_id > LAST_LESSON_ID:
        raise ValueError(
            f"lesson_id must be between {FIRST_LESSON_ID} and {LAST_LESSON_ID}; got {lesson_id}"
        )
