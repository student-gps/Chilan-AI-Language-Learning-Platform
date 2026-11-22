from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[4]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

try:
    from content_builder.core.llm_providers import LLMFactory
    from content_builder.core.paths import default_paths
    from content_builder.core.pipeline import get_pipeline
    from content_builder.ja.minna_no_nihongo.book_profiles import book1, lesson_profile
    from content_builder.ja.minna_no_nihongo.tasks.lesson_audio import MinnaNoNihongoLessonAudioRenderer
    from content_builder.ja.minna_no_nihongo.tasks.lesson_normalizer import MinnaNoNihongoLessonNormalizer
    from content_builder.ja.minna_no_nihongo.tasks.schema_validator import MinnaNoNihongoSchemaValidator
    from content_builder.ja.minna_no_nihongo.tasks.speaker_resolver import MinnaNoNihongoSpeakerResolver
except ImportError:
    from content_builder.core.llm_providers import LLMFactory
    from content_builder.core.paths import default_paths
    from content_builder.core.pipeline import get_pipeline
    from content_builder.ja.minna_no_nihongo.book_profiles import book1, lesson_profile
    from content_builder.ja.minna_no_nihongo.tasks.lesson_audio import MinnaNoNihongoLessonAudioRenderer
    from content_builder.ja.minna_no_nihongo.tasks.lesson_normalizer import MinnaNoNihongoLessonNormalizer
    from content_builder.ja.minna_no_nihongo.tasks.schema_validator import MinnaNoNihongoSchemaValidator
    from content_builder.ja.minna_no_nihongo.tasks.speaker_resolver import MinnaNoNihongoSpeakerResolver


def parse_lesson(value: str) -> int:
    normalized = value.strip().lower()
    if normalized.startswith("lesson"):
        normalized = normalized.removeprefix("lesson")
    digits = "".join(char for char in normalized if char.isdigit())
    if not digits:
        raise ValueError(f"Cannot parse lesson id from {value!r}")
    return int(digits)


def parse_only(values: list[str] | None) -> set[str]:
    selected = set()
    for value in values or []:
        for item in value.split(","):
            item = item.strip()
            if item:
                selected.add(item)
    return selected


def lesson_json_path(artifact_root: Path, lesson_id: int, support_lang: str) -> Path:
    profile = lesson_profile(lesson_id)
    output_path = artifact_root / "output_json" / support_lang / f"{profile.lesson_slug}_data.json"
    if output_path.exists():
        return output_path
    return artifact_root / "synced_json" / support_lang / f"{profile.lesson_slug}_data.json"


def normalize_for_audio(data: dict, lesson_id: int, json_path: Path) -> dict:
    metadata = data.get("lesson_metadata") if isinstance(data.get("lesson_metadata"), dict) else {}
    source = metadata.get("source") if isinstance(metadata.get("source"), dict) else {}
    lesson_pdf = Path(
        source.get("lesson_pdf")
        or json_path.parents[2] / "raw_materials" / f"lesson{lesson_id:03d}.pdf"
    )
    source_pdf = Path(source.get("source_pdf") or lesson_pdf)
    normalized = MinnaNoNihongoLessonNormalizer().run(
        data,
        lesson_id=lesson_id,
        source_pdf=source_pdf,
        lesson_pdf=lesson_pdf,
        support_language=data.get("support_language") or "zh",
        course_id=metadata.get("course_id") or book1.COURSE_ID,
    )
    if isinstance(data.get("pipeline_diagnostics"), dict):
        normalized["pipeline_diagnostics"] = data["pipeline_diagnostics"]
    return normalized


def summarize_assets(assets: dict) -> None:
    items = assets.get("items") if isinstance(assets.get("items"), list) else []
    sections = {}
    voices = {}
    statuses = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        sections[item.get("source_section", "")] = sections.get(item.get("source_section", ""), 0) + 1
        voices[item.get("voice", "")] = voices.get(item.get("voice", ""), 0) + 1
        statuses[item.get("status", "")] = statuses.get(item.get("status", ""), 0) + 1

    print(f"Audio items: {len(items)}")
    print(f"Sections: {sections}")
    print(f"Voices: {voices}")
    print(f"Statuses: {statuses}")
    full_audio = assets.get("full_audio") if isinstance(assets.get("full_audio"), dict) else {}
    print(
        "Full audio: "
        f"{full_audio.get('status')} | duration={full_audio.get('duration_seconds')} | "
        f"{full_audio.get('local_audio_file')}"
    )


def print_selected_items(assets: dict, selected_audio_ids: set[str]) -> None:
    if not selected_audio_ids:
        return
    print("Selected items:")
    for item in assets.get("items") or []:
        if not isinstance(item, dict) or item.get("audio_id") not in selected_audio_ids:
            continue
        print(
            "  "
            f"{item.get('audio_id')} | {item.get('source_section')} | "
            f"speaker={item.get('speaker') or '-'} | voice={item.get('voice')} | "
            f"status={item.get('status')} | text={item.get('source_text')}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Render Minna no Nihongo lesson sentence audio.")
    parser.add_argument("--lesson", default="lesson001", help="Lesson number or slug, e.g. 001 or lesson001.")
    parser.add_argument("--support-lang", default="zh")
    parser.add_argument("--only", action="append", help="Render only specific audio_id(s), comma-separated allowed.")
    parser.add_argument("--render", action="store_true", help="Call Azure TTS and write rendered audio metadata.")
    parser.add_argument("--dry-run", action="store_true", help="Preview metadata only. This is the default.")
    parser.add_argument("--force", action="store_true", help="Re-render existing ready files.")
    parser.add_argument("--write-json", action="store_true", help="Write JSON even in dry-run mode.")
    parser.add_argument("--no-write-json", action="store_true", help="Do not write JSON after rendering.")
    parser.add_argument("--speaker-audit-llm", action="store_true", help="Run the optional LLM speaker audit before rendering.")
    args = parser.parse_args()

    lesson_id = parse_lesson(args.lesson)
    lesson_profile(lesson_id)
    only_audio_ids = parse_only(args.only)
    dry_run = not args.render

    paths = default_paths()
    load_dotenv(dotenv_path=paths.backend_dir / ".env")
    artifact_root = get_pipeline("minna_no_nihongo").artifact_root(paths)
    json_path = lesson_json_path(artifact_root, lesson_id=lesson_id, support_lang=args.support_lang)
    if not json_path.exists():
        raise FileNotFoundError(f"Lesson JSON not found: {json_path}")

    data = json.loads(json_path.read_text(encoding="utf-8-sig"))
    existing_assets = data.get("lesson_audio_assets") if isinstance(data.get("lesson_audio_assets"), dict) else {}

    speaker_provider = LLMFactory.create_provider() if args.speaker_audit_llm else None
    repaired = MinnaNoNihongoSpeakerResolver().run(
        data,
        llm_provider=speaker_provider,
        lesson_id=lesson_id,
    )
    normalized = normalize_for_audio(repaired, lesson_id=lesson_id, json_path=json_path)
    if isinstance(repaired.get("pipeline_diagnostics"), dict):
        normalized["pipeline_diagnostics"] = repaired["pipeline_diagnostics"]

    renderer = MinnaNoNihongoLessonAudioRenderer()
    available_audio_ids = {item["audio_id"] for item in renderer.extract_sentence_items(normalized)}
    unknown = sorted(only_audio_ids - available_audio_ids)
    if unknown:
        raise ValueError(f"Unknown --only audio_id(s): {', '.join(unknown)}")

    audio_output_dir = artifact_root / "output_audio" / f"lesson{lesson_id:03d}"
    lesson_audio_assets = renderer.render_sentence_audio_assets(
        lesson_data=normalized,
        output_dir=audio_output_dir,
        dry_run=dry_run,
        only_audio_ids=only_audio_ids,
        existing_assets=existing_assets,
        reuse_existing=True,
        force=args.force or bool(only_audio_ids),
    ).get("lesson_audio_assets", {})
    normalized["lesson_audio_assets"] = lesson_audio_assets

    MinnaNoNihongoSchemaValidator().validate(normalized)
    summarize_assets(lesson_audio_assets)
    print_selected_items(lesson_audio_assets, only_audio_ids)

    write_json = (args.render and not args.no_write_json) or args.write_json
    if write_json:
        json_path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ Wrote {json_path}")
    else:
        print("ℹ️ JSON not written. Use --render or --write-json to persist changes.")


if __name__ == "__main__":
    main()
