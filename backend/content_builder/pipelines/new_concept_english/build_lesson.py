import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv


CONTENT_BUILDER_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = CONTENT_BUILDER_DIR.parent
if str(CONTENT_BUILDER_DIR) not in sys.path:
    sys.path.append(str(CONTENT_BUILDER_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

try:
    from content_builder.core.paths import default_paths
    from content_builder.core.llm_providers import LLMFactory
    from content_builder.pipelines.new_concept_english.agent import NewConceptEnglishAgent
    from content_builder.pipelines.new_concept_english.book_profiles import book1
    from content_builder.pipelines.new_concept_english.tasks.source_pdf import (
        export_book1_app_lesson_pdf,
        export_book1_all_app_lesson_pdfs,
        find_book_pdf,
    )
except ImportError:
    from core.paths import default_paths
    from core.llm_providers import LLMFactory
    from pipelines.new_concept_english.agent import NewConceptEnglishAgent
    from pipelines.new_concept_english.book_profiles import book1
    from pipelines.new_concept_english.tasks.source_pdf import (
        export_book1_all_app_lesson_pdfs,
        export_book1_app_lesson_pdf,
        find_book_pdf,
    )


def _parse_lesson(value: str) -> int:
    normalized = value.strip().lower()
    if normalized.startswith("lesson"):
        normalized = normalized.removeprefix("lesson")
    return int(normalized)


def _write_json(output_file: Path, payload: dict) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _build_one_lesson(
    *,
    app_lesson_index: int,
    course_id: int | str,
    source_pdf: Path,
    raw_materials_dir: Path,
    output_dir: Path,
    support_language: str,
    agent: NewConceptEnglishAgent,
    force: bool,
) -> tuple[Path, Path]:
    lesson_slice = book1.app_lesson_slice(app_lesson_index)
    lesson_pdf = raw_materials_dir / "book1" / f"{lesson_slice.lesson_slug}.pdf"
    export_book1_app_lesson_pdf(source_pdf, lesson_pdf, app_lesson_index=app_lesson_index)

    output_file = output_dir / f"{lesson_slice.lesson_slug}_data.json"
    if output_file.exists() and not force:
        print(f"⏭️  {lesson_slice.lesson_slug}: JSON already exists, skipping.")
        return lesson_pdf, output_file

    lesson_data = agent.generate_content(
        file_path=str(lesson_pdf),
        lesson_id=app_lesson_index,
        course_id=course_id,
        support_language=support_language,
    )
    if lesson_data is None:
        raise RuntimeError(f"{lesson_slice.lesson_slug} generation failed.")

    _write_json(output_file, lesson_data)
    anchor_lines = len(
        (((lesson_data.get("course_content") or {}).get("anchor") or {}).get("lines") or [])
    )
    vocab_count = len(((lesson_data.get("course_content") or {}).get("vocabulary") or []))
    render_segment_count = len(
        ((((lesson_data.get("video_render_plan") or {}).get("explanation") or {}).get("segments")) or [])
    )
    print(
        f"✅ {lesson_slice.lesson_slug}: lines={anchor_lines}, vocab={vocab_count}, "
        f"render_segments={render_segment_count}, pdf_pages={lesson_slice.pdf_pages}"
    )
    return lesson_pdf, output_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Build New Concept English lesson JSON.")
    parser.add_argument("--book", type=int, default=1)
    parser.add_argument("--lesson", default="lesson001", help="App lesson slug or number, e.g. lesson001.")
    parser.add_argument("--all", action="store_true", help="Build every Book 1 app lesson.")
    parser.add_argument("--start", type=int, default=None, help="First app lesson index when using --all.")
    parser.add_argument("--end", type=int, default=None, help="Last app lesson index when using --all.")
    parser.add_argument("--support-lang", default="zh")
    parser.add_argument("--course-id", default=book1.COURSE_ID, help="Database course_id for Book 1.")
    parser.add_argument("--split-only", action="store_true", help="Only export lessonXXX PDFs; do not build JSON.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing JSON files.")
    args = parser.parse_args()

    if args.book != 1:
        raise ValueError("Only Book 1 is supported by the current builder.")

    paths = default_paths()
    load_dotenv(dotenv_path=paths.backend_dir / ".env")
    artifact_root = paths.artifacts_dir / "new_concept_english"
    raw_materials_dir = artifact_root / "raw_materials"
    source_pdf = find_book_pdf(raw_materials_dir, book_number=args.book)
    output_dir = artifact_root / "output_json" / args.support_lang
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.all:
        start = args.start or 1
        end = args.end or book1.APP_LESSON_COUNT
        lesson_indices = list(range(start, end + 1))
    else:
        lesson_indices = [_parse_lesson(args.lesson)]

    if args.split_only:
        if args.all and (args.start is None and args.end is None):
            exported = export_book1_all_app_lesson_pdfs(source_pdf, raw_materials_dir / "book1")
        else:
            exported = [
                export_book1_app_lesson_pdf(
                    source_pdf=source_pdf,
                    output_pdf=raw_materials_dir / "book1" / f"{book1.format_lesson_slug(idx)}.pdf",
                    app_lesson_index=idx,
                )
                for idx in lesson_indices
            ]
        print(f"✅ Exported {len(exported)} lesson PDFs.")
        print(f"Output dir: {raw_materials_dir / 'book1'}")
        return

    provider = None
    if any(index != 1 for index in lesson_indices):
        provider = LLMFactory.create_provider()
        print(f"🔧 LLM provider: {type(provider).__name__}")
    agent = NewConceptEnglishAgent(provider=provider, memory_dir=artifact_root)

    built = []
    for index in lesson_indices:
        _, output_file = _build_one_lesson(
            app_lesson_index=index,
            course_id=args.course_id,
            source_pdf=source_pdf,
            raw_materials_dir=raw_materials_dir,
            output_dir=output_dir,
            support_language=args.support_lang,
            agent=agent,
            force=args.force,
        )
        built.append(output_file)

    print(f"✅ Built {len(built)} lesson JSON file(s).")
    print(f"Output dir: {output_dir}")


if __name__ == "__main__":
    main()
