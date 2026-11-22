from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[3]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

try:
    from content_builder.core.llm_providers import LLMFactory
    from content_builder.core.paths import default_paths
    from content_builder.core.pipeline import get_pipeline
    from content_builder.ja.minna_no_nihongo.agent import MinnaNoNihongoAgent
    from content_builder.ja.minna_no_nihongo.book_profiles import book1, lesson_profile
    from content_builder.ja.minna_no_nihongo.tasks.source_pdf import find_book_pdf, find_lesson_pdf
except ImportError:
    from content_builder.core.llm_providers import LLMFactory
    from content_builder.core.paths import default_paths
    from content_builder.core.pipeline import get_pipeline
    from content_builder.ja.minna_no_nihongo.agent import MinnaNoNihongoAgent
    from content_builder.ja.minna_no_nihongo.book_profiles import book1, lesson_profile
    from content_builder.ja.minna_no_nihongo.tasks.source_pdf import find_book_pdf, find_lesson_pdf


def _parse_lesson(value: str) -> int:
    normalized = value.strip().lower()
    if normalized.startswith("lesson"):
        normalized = normalized.removeprefix("lesson")
    numbers = "".join(char for char in normalized if char.isdigit())
    if not numbers:
        raise ValueError(f"Cannot parse lesson id from {value!r}")
    return int(numbers)


def _write_json(output_file: Path, payload: dict) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _lesson_indices(args) -> list[int]:
    if args.all:
        start = args.start or 1
        end = args.end or book1.LESSON_COUNT
        return list(range(start, end + 1))
    return [_parse_lesson(args.lesson)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Minna no Nihongo lesson JSON.")
    parser.add_argument("--book", type=int, default=1)
    parser.add_argument("--lesson", default="lesson001", help="Lesson slug or number, e.g. lesson001.")
    parser.add_argument("--all", action="store_true", help="Build every Book 1 lesson.")
    parser.add_argument("--start", type=int, default=None, help="First lesson id when using --all.")
    parser.add_argument("--end", type=int, default=None, help="Last lesson id when using --all.")
    parser.add_argument("--support-lang", default="zh")
    parser.add_argument("--course-id", default=book1.COURSE_ID, help="Database course_id for Book 1.")
    parser.add_argument("--split-only", action="store_true", help="Reserve flag for future whole-book PDF splitting.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing JSON files.")
    parser.add_argument("--dry-run-placeholder", action="store_true", help="Build deterministic placeholder JSON without an LLM.")
    parser.add_argument(
        "--lesson-audio-metadata-only",
        action="store_true",
        help="Skip real Japanese lesson audio rendering and write metadata only.",
    )
    args = parser.parse_args()

    if args.book != 1:
        print("⚠️ --book is a legacy PDF hint; the lesson profile is selected from --lesson/--start/--end.")

    paths = default_paths()
    load_dotenv(dotenv_path=paths.backend_dir / ".env")
    artifact_root = get_pipeline("minna_no_nihongo").artifact_root(paths)
    raw_materials_dir = artifact_root / "raw_materials"
    output_dir = artifact_root / "output_json" / args.support_lang
    output_dir.mkdir(parents=True, exist_ok=True)

    lesson_indices = _lesson_indices(args)
    for index in lesson_indices:
        lesson_profile(index)

    if args.split_only:
        print("⚠️ Minna no Nihongo whole-book page slicing is not configured yet.")
        print(f"Place pre-split PDFs under: {raw_materials_dir / 'book1'}")
        print("Expected names: lesson001.pdf, lesson002.pdf, ...")
        return

    provider = None if args.dry_run_placeholder else LLMFactory.create_provider()
    if provider is not None:
        model_id = getattr(provider, "model_id", "") or getattr(provider, "endpoint_id", "")
        model_label = f" | model={model_id}" if model_id else ""
        print(f"🔧 LLM provider: {type(provider).__name__}{model_label}")
    agent = MinnaNoNihongoAgent(
        provider=provider,
        memory_dir=artifact_root,
        render_lesson_audio=not args.lesson_audio_metadata_only,
    )

    built = []
    for lesson_id in lesson_indices:
        profile = lesson_profile(lesson_id)
        output_file = output_dir / f"{profile.lesson_slug}_data.json"
        if output_file.exists() and not args.force:
            print(f"⏭️  {profile.lesson_slug}: JSON already exists, skipping.")
            built.append(output_file)
            continue

        lesson_pdf = None if args.dry_run_placeholder else find_lesson_pdf(
            raw_materials_dir,
            lesson_id=lesson_id,
            book_number=profile.book,
        )
        if args.dry_run_placeholder and lesson_pdf is None:
            lesson_pdf = raw_materials_dir / f"{profile.lesson_slug}.pdf"
        if lesson_pdf is None:
            try:
                source_pdf = find_book_pdf(raw_materials_dir, book_number=profile.book)
            except Exception as exc:
                raise FileNotFoundError(
                    f"{profile.lesson_slug} PDF not found. Put it at "
                    f"{raw_materials_dir / 'book1' / (profile.lesson_slug + '.pdf')}."
                ) from exc
            raise FileNotFoundError(
                f"{profile.lesson_slug} PDF not found. Found full book PDF {source_pdf}, "
                "but page slicing is not configured yet. Please place a pre-split lesson PDF first."
            )

        lesson_data = agent.generate_content(
            file_path=str(lesson_pdf),
            lesson_id=lesson_id,
            course_id=args.course_id,
            support_language=args.support_lang,
        )
        if lesson_data is None:
            raise RuntimeError(f"{profile.lesson_slug} generation failed.")

        _write_json(output_file, lesson_data)
        vocab_count = len(((lesson_data.get("course_content") or {}).get("vocabulary")) or [])
        grammar_count = len(((lesson_data.get("course_content") or {}).get("grammar_sections")) or [])
        print(f"✅ {profile.lesson_slug}: vocab={vocab_count}, grammar={grammar_count}")
        built.append(output_file)

    print(f"✅ Built {len(built)} lesson JSON file(s).")
    print(f"Output dir: {output_dir}")


if __name__ == "__main__":
    main()
