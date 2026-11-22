from __future__ import annotations

import re
from pathlib import Path

try:
    from content_builder.ja.minna_no_nihongo.book_profiles import format_lesson_slug
except ImportError:
    from content_builder.ja.minna_no_nihongo.book_profiles import format_lesson_slug


def find_lesson_pdf(raw_materials_dir: Path, lesson_id: int, book_number: int = 1) -> Path | None:
    """Find a pre-split lesson PDF, preferring book1/lesson001.pdf."""

    lesson_slug = format_lesson_slug(lesson_id)
    candidates = [
        raw_materials_dir / f"{lesson_slug}.pdf",
        raw_materials_dir / f"lesson{lesson_id}.pdf",
        raw_materials_dir / f"L{lesson_id}.pdf",
        raw_materials_dir / f"{lesson_id}.pdf",
        raw_materials_dir / f"book{book_number}" / f"{lesson_slug}.pdf",
        raw_materials_dir / f"book{book_number}" / f"lesson{lesson_id}.pdf",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    for pdf in sorted(raw_materials_dir.rglob("*.pdf")):
        numbers = [int(value) for value in re.findall(r"\d+", pdf.stem)]
        if numbers and numbers[-1] == lesson_id:
            return pdf
    return None


def find_book_pdf(raw_materials_dir: Path, book_number: int = 1) -> Path:
    """Find the full textbook PDF when no pre-split lesson PDF exists."""

    if not raw_materials_dir.exists():
        raise FileNotFoundError(f"Raw materials dir does not exist: {raw_materials_dir}")

    preferred = [
        raw_materials_dir / f"book{book_number}.pdf",
        raw_materials_dir / f"minna_no_nihongo_{book_number}.pdf",
        raw_materials_dir / f"minna_no_nihongo_book{book_number}.pdf",
        raw_materials_dir / f"大家的日本语{book_number}.pdf",
    ]
    for candidate in preferred:
        if candidate.exists():
            return candidate

    pdfs = [
        pdf for pdf in sorted(raw_materials_dir.glob("*.pdf"))
        if not pdf.stem.lower().startswith("lesson")
    ]
    if len(pdfs) == 1:
        return pdfs[0]
    if not pdfs:
        raise FileNotFoundError(
            f"No full Book {book_number} PDF found in {raw_materials_dir}. "
            "Place the textbook PDF there, or place pre-split lesson PDFs under book1/."
        )
    names = ", ".join(pdf.name for pdf in pdfs[:8])
    raise ValueError(f"Multiple possible Book {book_number} PDFs found: {names}")


def export_book1_lesson_pdf(source_pdf: Path, output_pdf: Path, lesson_id: int) -> Path:
    """Future hook for page slicing once the actual PDF edition is inspected."""

    raise NotImplementedError(
        "Minna no Nihongo page slicing is not configured yet. "
        "Place a pre-split lesson PDF such as raw_materials/book1/lesson001.pdf, "
        "or add page ranges to the book profile after inspecting the downloaded PDF."
    )
