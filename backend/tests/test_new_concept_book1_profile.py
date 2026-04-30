import sys
import unittest
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
CONTENT_BUILDER_DIR = BACKEND_DIR / "content_builder"

for path in (BACKEND_DIR, CONTENT_BUILDER_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.append(path_str)

from content_builder.pipelines.new_concept_english.book_profiles.book1 import (
    APP_LESSON_COUNT,
    app_lesson_index_for_source_lesson,
    app_lesson_slice,
    format_lesson_slug,
    pdf_pages_for_source_lesson,
)


class NewConceptBook1ProfileTests(unittest.TestCase):
    def test_source_lesson_pages_are_two_page_slices_after_front_matter(self):
        self.assertEqual(pdf_pages_for_source_lesson(1), (5, 6))
        self.assertEqual(pdf_pages_for_source_lesson(2), (7, 8))
        self.assertEqual(pdf_pages_for_source_lesson(3), (9, 10))

    def test_odd_even_source_lessons_are_grouped_as_app_lessons(self):
        first = app_lesson_slice(1)
        self.assertEqual(first.lesson_slug, "lesson001")
        self.assertEqual(first.source_lessons, (1, 2))
        self.assertEqual(first.pdf_pages, (5, 6, 7, 8))
        self.assertEqual(first.pdf_page_indices, (4, 5, 6, 7))

        second = app_lesson_slice(2)
        self.assertEqual(second.lesson_slug, "lesson002")
        self.assertEqual(second.source_lessons, (3, 4))
        self.assertEqual(second.pdf_pages, (9, 10, 11, 12))

    def test_review_block_offsets_late_book_pages(self):
        before_review = app_lesson_slice(36)
        self.assertEqual(before_review.source_lessons, (71, 72))
        self.assertEqual(before_review.pdf_pages, (145, 146, 147, 148))

        after_review = app_lesson_slice(37)
        self.assertEqual(after_review.source_lessons, (73, 74))
        self.assertEqual(after_review.pdf_pages, (153, 154, 155, 156))

        late_mid_book = app_lesson_slice(51)
        self.assertEqual(late_mid_book.source_lessons, (101, 102))
        self.assertEqual(late_mid_book.pdf_pages, (209, 210, 211, 212))

        late_book = app_lesson_slice(58)
        self.assertEqual(late_book.source_lessons, (115, 116))
        self.assertEqual(late_book.pdf_pages, (237, 238, 239, 240))

    def test_source_lesson_to_app_lesson_index(self):
        self.assertEqual(app_lesson_index_for_source_lesson(1), 1)
        self.assertEqual(app_lesson_index_for_source_lesson(2), 1)
        self.assertEqual(app_lesson_index_for_source_lesson(3), 2)
        self.assertEqual(app_lesson_index_for_source_lesson(4), 2)

    def test_last_book1_lesson(self):
        self.assertEqual(APP_LESSON_COUNT, 72)
        last = app_lesson_slice(APP_LESSON_COUNT)
        self.assertEqual(last.lesson_slug, "lesson072")
        self.assertEqual(last.source_lessons, (143, 144))
        self.assertEqual(last.pdf_pages, (293, 294, 295, 296))

    def test_rejects_invalid_indices(self):
        with self.assertRaises(ValueError):
            app_lesson_slice(0)
        with self.assertRaises(ValueError):
            format_lesson_slug(73)
        with self.assertRaises(ValueError):
            pdf_pages_for_source_lesson(145)


if __name__ == "__main__":
    unittest.main()
