from pathlib import Path

try:
    from content_builder.pipelines.new_concept_english.book_profiles import book1
except ImportError:
    from pipelines.new_concept_english.book_profiles import book1


def find_book_pdf(raw_materials_dir: Path, book_number: int) -> Path:
    book_dir = raw_materials_dir / f"book{book_number}"
    if not book_dir.exists():
        raise FileNotFoundError(f"Missing raw material directory: {book_dir}")

    pdfs = sorted(
        path for path in book_dir.glob("*.pdf")
        if not path.stem.lower().startswith("lesson")
    )
    if not pdfs:
        raise FileNotFoundError(f"No source PDF found in {book_dir}")
    if len(pdfs) > 1:
        names = ", ".join(path.name for path in pdfs)
        raise ValueError(f"Expected one Book {book_number} source PDF, found: {names}")
    return pdfs[0]


def export_book1_app_lesson_pdf(
    source_pdf: Path,
    output_pdf: Path,
    app_lesson_index: int,
) -> Path:
    lesson_slice = book1.app_lesson_slice(app_lesson_index)
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    import fitz

    source_doc = fitz.open(source_pdf)
    try:
        output_doc = fitz.open()
        try:
            for page_index in lesson_slice.pdf_page_indices:
                if page_index < 0 or page_index >= source_doc.page_count:
                    raise ValueError(
                        f"Page index {page_index} is outside {source_pdf.name} "
                        f"({source_doc.page_count} pages)"
                    )
                output_doc.insert_pdf(source_doc, from_page=page_index, to_page=page_index)
            output_doc.save(output_pdf)
        finally:
            output_doc.close()
    finally:
        source_doc.close()

    return output_pdf


def export_book1_all_app_lesson_pdfs(source_pdf: Path, output_dir: Path) -> list[Path]:
    output_paths = []
    for lesson_slice in book1.iter_app_lesson_slices():
        output_paths.append(
            export_book1_app_lesson_pdf(
                source_pdf=source_pdf,
                output_pdf=output_dir / f"{lesson_slice.lesson_slug}.pdf",
                app_lesson_index=lesson_slice.app_lesson_index,
            )
        )
    return output_paths
