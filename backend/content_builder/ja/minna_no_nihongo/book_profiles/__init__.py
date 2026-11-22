"""Book profiles for Minna no Nihongo."""

from __future__ import annotations

from . import book1, intermediate
from .book1 import LessonProfile


def lesson_profile(lesson_id: int) -> LessonProfile:
    """Resolve the correct textbook profile from the app lesson id."""

    if lesson_id <= book1.LESSON_COUNT:
        return book1.lesson_profile(lesson_id)
    return intermediate.lesson_profile(lesson_id)


def format_lesson_slug(lesson_id: int) -> str:
    lesson_profile(lesson_id)
    return f"lesson{lesson_id:03d}"


def max_configured_lesson_id() -> int:
    return intermediate.LAST_LESSON_ID


__all__ = [
    "LessonProfile",
    "book1",
    "intermediate",
    "lesson_profile",
    "format_lesson_slug",
    "max_configured_lesson_id",
]
