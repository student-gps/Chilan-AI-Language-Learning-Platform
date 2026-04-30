from dataclasses import dataclass
from typing import Iterator


BOOK_NUMBER = 1
COURSE_ID = 101
COURSE_SLUG = "new_concept_english_1"
FRONT_MATTER_PAGES = 4
FIRST_SOURCE_LESSON = 1
SOURCE_LESSON_COUNT = 144
PAGES_PER_SOURCE_LESSON = 2
SOURCE_LESSONS_PER_APP_LESSON = 2
APP_LESSON_COUNT = SOURCE_LESSON_COUNT // SOURCE_LESSONS_PER_APP_LESSON
# Book 1 contains a four-page "Can you do this test?" review block after
# source Lesson 72. Source Lesson 73 and later are therefore shifted by 4 PDF
# pages compared with the early-book two-pages-per-lesson rhythm.
REVIEW_BLOCK_AFTER_SOURCE_LESSON = 72
REVIEW_BLOCK_PAGES = 4


@dataclass(frozen=True)
class SourceLessonSlice:
    """Page slice for one original New Concept English Book 1 lesson."""

    source_lesson: int
    pdf_pages: tuple[int, ...]
    pdf_page_indices: tuple[int, ...]


@dataclass(frozen=True)
class AppLessonSlice:
    """Normalized app lesson made from an odd/even source lesson pair."""

    book: int
    app_lesson_index: int
    lesson_slug: str
    source_lessons: tuple[int, ...]
    pdf_pages: tuple[int, ...]
    pdf_page_indices: tuple[int, ...]
    source_slices: tuple[SourceLessonSlice, ...]


def format_lesson_slug(app_lesson_index: int) -> str:
    _validate_app_lesson_index(app_lesson_index)
    return f"lesson{app_lesson_index:03d}"


def source_lessons_for_app_lesson(app_lesson_index: int) -> tuple[int, int]:
    _validate_app_lesson_index(app_lesson_index)
    first_source_lesson = FIRST_SOURCE_LESSON + (
        (app_lesson_index - 1) * SOURCE_LESSONS_PER_APP_LESSON
    )
    return first_source_lesson, first_source_lesson + 1


def pdf_pages_for_source_lesson(source_lesson: int) -> tuple[int, int]:
    _validate_source_lesson(source_lesson)
    inserted_page_offset = (
        REVIEW_BLOCK_PAGES
        if source_lesson > REVIEW_BLOCK_AFTER_SOURCE_LESSON
        else 0
    )
    first_page = FRONT_MATTER_PAGES + (
        (source_lesson - FIRST_SOURCE_LESSON) * PAGES_PER_SOURCE_LESSON
    ) + inserted_page_offset + 1
    return first_page, first_page + 1


def source_slice(source_lesson: int) -> SourceLessonSlice:
    pages = pdf_pages_for_source_lesson(source_lesson)
    return SourceLessonSlice(
        source_lesson=source_lesson,
        pdf_pages=pages,
        pdf_page_indices=tuple(page - 1 for page in pages),
    )


def app_lesson_slice(app_lesson_index: int) -> AppLessonSlice:
    source_lessons = source_lessons_for_app_lesson(app_lesson_index)
    source_slices = tuple(source_slice(lesson) for lesson in source_lessons)
    pdf_pages = tuple(page for item in source_slices for page in item.pdf_pages)
    return AppLessonSlice(
        book=BOOK_NUMBER,
        app_lesson_index=app_lesson_index,
        lesson_slug=format_lesson_slug(app_lesson_index),
        source_lessons=source_lessons,
        pdf_pages=pdf_pages,
        pdf_page_indices=tuple(page - 1 for page in pdf_pages),
        source_slices=source_slices,
    )


def app_lesson_index_for_source_lesson(source_lesson: int) -> int:
    _validate_source_lesson(source_lesson)
    return ((source_lesson - FIRST_SOURCE_LESSON) // SOURCE_LESSONS_PER_APP_LESSON) + 1


def iter_app_lesson_slices() -> Iterator[AppLessonSlice]:
    for app_lesson_index in range(1, APP_LESSON_COUNT + 1):
        yield app_lesson_slice(app_lesson_index)


def _validate_source_lesson(source_lesson: int) -> None:
    if not isinstance(source_lesson, int):
        raise TypeError("source_lesson must be an integer")
    last_source_lesson = FIRST_SOURCE_LESSON + SOURCE_LESSON_COUNT - 1
    if source_lesson < FIRST_SOURCE_LESSON or source_lesson > last_source_lesson:
        raise ValueError(
            f"source_lesson must be between {FIRST_SOURCE_LESSON} and "
            f"{last_source_lesson}; got {source_lesson}"
        )


def _validate_app_lesson_index(app_lesson_index: int) -> None:
    if not isinstance(app_lesson_index, int):
        raise TypeError("app_lesson_index must be an integer")
    if app_lesson_index < 1 or app_lesson_index > APP_LESSON_COUNT:
        raise ValueError(
            f"app_lesson_index must be between 1 and {APP_LESSON_COUNT}; "
            f"got {app_lesson_index}"
        )
