#!/usr/bin/env python3
"""
Run the full localized publishing pipeline for one learner language.

This is the safe one-command path for Integrated Chinese localization:

    python content_builder/run_language_pipeline.py --lang th

It runs:
1. localize.py
2. render_narration.py with forced narration and slide regeneration
3. pre-sync asset validation
4. database/sync_to_db.py
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

CONTENT_BUILDER_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CONTENT_BUILDER_DIR.parent
if str(CONTENT_BUILDER_DIR) not in sys.path:
    sys.path.insert(0, str(CONTENT_BUILDER_DIR))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from core.paths import default_paths
from core.pipeline import get_pipeline
from config.env import get_env
from localize import LANG_META


DEFAULT_AZURE_EXPLANATION_VOICES = {
    "ar": "ar-SA-HamedNeural",
    "de": "de-DE-ConradNeural",
    "es": "es-ES-AlvaroNeural",
    "fr": "fr-FR-ClaudeNeural",
    "id": "id-ID-ArdiNeural",
    "it": "it-IT-DiegoNeural",
    "ja": "ja-JP-KeitaNeural",
    "ko": "ko-KR-BongJinNeural",
    "ms": "ms-MY-OsmanNeural",
    "pt": "pt-BR-AntonioNeural",
    "ru": "ru-RU-DmitryNeural",
    "th": "th-TH-NiwatNeural",
    "vi": "vi-VN-NamMinhNeural",
}


def _run_step(label: str, command: list[str], dry_run: bool = False) -> None:
    print(f"\n{'=' * 72}")
    print(f"▶ {label}")
    print("  " + " ".join(command))
    if dry_run:
        return
    result = subprocess.run(command, cwd=BACKEND_DIR)
    if result.returncode != 0:
        raise SystemExit(f"❌ {label} failed with exit code {result.returncode}")


def _lesson_id_from_path(path: Path) -> int:
    digits = "".join(ch for ch in path.stem if ch.isdigit())
    return int(digits) if digits else 0


def _expected_outputs(args: argparse.Namespace) -> list[Path]:
    paths = default_paths()
    pipeline = get_pipeline(args.pipeline)
    out_dir = pipeline.output_json_dir(paths, args.lang)
    synced_dir = pipeline.synced_json_dir(paths, args.lang)

    def resolve_existing(filename: str) -> Path:
        output_candidate = out_dir / filename
        synced_candidate = synced_dir / filename
        if output_candidate.exists():
            return output_candidate
        if args.reuse_localized_json and synced_candidate.exists():
            return synced_candidate
        return output_candidate

    if args.lesson:
        return [resolve_existing(f"lesson{args.lesson}_data_{args.lang}.json")]

    if args.files:
        outputs = []
        for raw in args.files:
            source = Path(raw)
            if source.exists() and source.name.endswith(".json"):
                outputs.append(source)
                continue
            stem = source.stem
            if stem.endswith(f"_{args.lang}"):
                outputs.append(resolve_existing(f"{stem}.json"))
            else:
                outputs.append(resolve_existing(f"{stem}_{args.lang}.json"))
        return outputs

    by_name = {path.name: path for path in sorted(synced_dir.glob(f"lesson*_data_{args.lang}.json"), key=_lesson_id_from_path)}
    by_name.update({path.name: path for path in sorted(out_dir.glob(f"lesson*_data_{args.lang}.json"), key=_lesson_id_from_path)})
    return sorted(by_name.values(), key=_lesson_id_from_path)


def _local_path_exists(value: str) -> bool:
    if not value:
        return False
    path = Path(value)
    return path.exists()


def _deck_from(data: dict) -> dict:
    if isinstance(data.get("teaching_slide_deck"), dict):
        return data["teaching_slide_deck"]
    plan = data.get("video_render_plan")
    if isinstance(plan, dict) and isinstance(plan.get("teaching_slide_deck"), dict):
        return plan["teaching_slide_deck"]
    explanation = plan.get("explanation") if isinstance(plan, dict) else None
    if isinstance(explanation, dict) and isinstance(explanation.get("teaching_slide_deck"), dict):
        return explanation["teaching_slide_deck"]
    return {}


def _validate_file(path: Path, lang: str) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"{path.name}: localized JSON does not exist"]

    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    if data.get("explanation_video_urls"):
        errors.append(f"{path.name}: still has legacy explanation_video_urls")

    narration = data.get("explanation_narration_audio")
    if not isinstance(narration, dict) or narration.get("status") != "ok":
        errors.append(f"{path.name}: explanation_narration_audio.status is not ok")
    elif not _local_path_exists(narration.get("audio_file", "")):
        errors.append(f"{path.name}: narration audio file is missing")

    segments = (
        data.get("video_render_plan", {})
        .get("explanation", {})
        .get("segments", [])
    )
    if not isinstance(segments, list) or not segments:
        errors.append(f"{path.name}: has no explanation segments")
    else:
        for index, segment in enumerate(segments, start=1):
            if not isinstance(segment, dict):
                errors.append(f"{path.name}: segment {index} is not an object")
                continue
            if not segment.get("sentence_texts"):
                errors.append(f"{path.name}: segment {index} has no sentence_texts")
            if not segment.get("sentence_timings_seconds"):
                errors.append(f"{path.name}: segment {index} has no sentence_timings_seconds")

    deck = _deck_from(data)
    if not deck:
        errors.append(f"{path.name}: teaching_slide_deck is missing")
        return errors
    if deck.get("lang") != lang:
        errors.append(f"{path.name}: teaching_slide_deck.lang is {deck.get('lang')!r}, expected {lang!r}")

    slides = deck.get("slides")
    if not isinstance(slides, list) or not slides:
        errors.append(f"{path.name}: teaching_slide_deck has no slides")
        return errors

    if deck.get("slide_count") != len(slides):
        errors.append(f"{path.name}: slide_count does not match slides length")

    for index, slide in enumerate(slides, start=1):
        if not isinstance(slide, dict):
            errors.append(f"{path.name}: slide {index} is not an object")
            continue
        image = slide.get("image") if isinstance(slide.get("image"), dict) else {}
        audio = slide.get("audio") if isinstance(slide.get("audio"), dict) else {}
        if not _local_path_exists(image.get("local_path", "")):
            errors.append(f"{path.name}: slide {index} image is missing")
        if not _local_path_exists(audio.get("local_path", "")):
            errors.append(f"{path.name}: slide {index} audio is missing")

    return errors


def _validate_outputs(json_files: list[Path], lang: str) -> None:
    print(f"\n{'=' * 72}")
    print("▶ Pre-sync validation")
    if not json_files:
        raise SystemExit("❌ No localized JSON files found to validate.")

    errors: list[str] = []
    for path in json_files:
        errors.extend(_validate_file(path, lang))

    if errors:
        print("❌ Validation failed:")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(1)

    print(f"✅ Validation passed for {len(json_files)} lesson file(s).")


def _ensure_tts_env(args: argparse.Namespace) -> None:
    lang_up = args.lang.upper()
    provider_key = f"TTS_EXPLANATION_PROVIDER_{lang_up}"
    voice_key = f"TTS_EXPLANATION_VOICE_{lang_up}"
    provider = (get_env(provider_key) or get_env("TTS_EXPLANATION_PROVIDER") or "").strip().lower()
    voice = (get_env(voice_key) or get_env("TTS_EXPLANATION_VOICE") or "").strip()

    if provider == "ali" and args.lang != "zh":
        default_voice = DEFAULT_AZURE_EXPLANATION_VOICES.get(args.lang)
        if default_voice:
            print(f"ℹ️ {provider_key} 未配置，当前会回落到 ali/{voice or 'default'}，不适合 {args.lang} 旁白。")
            print(f"   本次自动使用 Azure: {voice_key}={default_voice}")
            if not args.dry_run:
                import os
                os.environ[provider_key] = "azure"
                os.environ[voice_key] = default_voice
            provider = "azure"
            voice = default_voice

    if provider == "azure":
        if not get_env("TTS_AZURE_KEY"):
            raise SystemExit("❌ TTS_AZURE_KEY is required for Azure narration rendering.")
        if not voice:
            raise SystemExit(f"❌ {voice_key} is required for Azure narration rendering.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Translate, render, validate, and sync a localized Integrated Chinese language."
    )
    parser.add_argument("--lang", required=True, help=f"Target language code: {', '.join(sorted(LANG_META))}")
    parser.add_argument("--pipeline", default="integrated_chinese", help="Pipeline ID.")
    parser.add_argument("--lesson", help="Only process one lesson ID, for example 101.")
    parser.add_argument("files", nargs="*", help="Optional English source JSON filenames or paths.")
    parser.add_argument(
        "--reuse-localized-json",
        action="store_true",
        help="Do not overwrite existing localized JSON files. Default overwrites for safety.",
    )
    parser.add_argument(
        "--reuse-narration",
        action="store_true",
        help="Reuse existing narration audio if present. Default regenerates for safety.",
    )
    parser.add_argument(
        "--reuse-slides",
        action="store_true",
        help="Reuse existing slide deck assets if present. Default regenerates for safety.",
    )
    parser.add_argument("--skip-vocab", action="store_true", help="Forward --skip-vocab to localize.py.")
    parser.add_argument("--skip-sync", action="store_true", help="Stop after validation without writing to DB.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    args = parser.parse_args()

    if args.lang not in LANG_META:
        raise SystemExit(f"❌ Unknown language '{args.lang}'. Supported: {', '.join(sorted(LANG_META))}")

    _ensure_tts_env(args)

    localize_cmd = [
        sys.executable,
        "content_builder/localize.py",
        "--pipeline",
        args.pipeline,
        "--lang",
        args.lang,
    ]
    if args.lesson:
        localize_cmd.extend(["--lesson", args.lesson])
    if not args.reuse_localized_json:
        localize_cmd.append("--force")
    if args.skip_vocab:
        localize_cmd.append("--skip-vocab")
    localize_cmd.extend(args.files)

    if args.reuse_localized_json:
        print("\n========================================================================")
        print("▶ Stage 1: reuse localized lesson JSON")
        print("  Skipping localize.py; using existing output_json/synced_json files.")
    else:
        _run_step("Stage 1: localize lesson JSON", localize_cmd, dry_run=args.dry_run)

    targets = _expected_outputs(args)
    if args.dry_run:
        print("\nExpected localized outputs:")
        for target in targets:
            print(f"  - {target}")
        return
    if not targets:
        raise SystemExit(f"❌ No output JSON files found for lang={args.lang}.")

    render_cmd = [
        sys.executable,
        "content_builder/render_narration.py",
        "--pipeline",
        args.pipeline,
        "--lang",
        args.lang,
    ]
    if not args.reuse_narration:
        render_cmd.append("--force-narration")
    if not args.reuse_slides:
        render_cmd.append("--force-slides")
    render_cmd.extend(str(path) for path in targets)
    _run_step("Stage 2: render narration and slide deck", render_cmd)

    _validate_outputs(targets, args.lang)

    if args.skip_sync:
        print("\n✅ Stopped before DB sync because --skip-sync was set.")
        return

    sync_cmd = [
        sys.executable,
        "database/sync_to_db.py",
        "--pipeline",
        args.pipeline,
        "--lang",
        args.lang,
    ]
    sync_cmd.extend(str(path) for path in targets)
    _run_step("Stage 3: upload assets and sync to database", sync_cmd)

    print("\n✨ Full language pipeline finished.")


if __name__ == "__main__":
    main()
