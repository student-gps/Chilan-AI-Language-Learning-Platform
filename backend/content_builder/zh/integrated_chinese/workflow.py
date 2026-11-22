"""Fixed Integrated Chinese workflow. Run with `python -m ...workflow --help`."""
from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from content_builder.core.artifacts import (apply_narration_timings, atomic_write_json, code_digest,
                                           file_digest, fingerprint, narration_fingerprint, resolve_artifact_path)
from content_builder.core.checkpoints import CheckpointStore, build_lock
from content_builder.core.paths import default_paths
from content_builder.zh.integrated_chinese.quality import audit_lesson, require_quality

STAGES = ("content", "lesson_audio", "localize", "narration", "slides", "verify", "publish")
PIPELINE_DIR = Path(__file__).resolve().parent
ROOT = PIPELINE_DIR / "artifacts"


def preflight(stages) -> None:
    if any(stage in stages for stage in ("lesson_audio", "narration", "slides", "verify", "publish")):
        missing = [name for name in ("ffmpeg", "ffprobe") if not shutil.which(name)]
        if missing:
            raise RuntimeError(f"Missing media tools: {', '.join(missing)}")
    if "slides" in stages:
        if not shutil.which("node"):
            raise RuntimeError("Node.js is required for static slide rendering")
        from PIL import features
        if not features.check("webp"):
            raise RuntimeError("Pillow must include WebP support")
        frontend = default_paths().project_root / "frontend"
        if not (frontend / "node_modules/@remotion/bundler/package.json").is_file():
            raise RuntimeError("Install the frontend dependencies before rendering slides: npm ci")


def lesson_json(root: Path, lesson: int, lang: str) -> Path:
    name = f"lesson{lesson}_data{'_' + lang if lang != 'en' else ''}.json"
    for folder in ("output_json", "synced_json"):
        path = root / folder / lang / name
        if path.is_file():
            return path
    return root / "output_json" / lang / name


def source_pdf(root: Path, lesson: int, explicit: Path | None) -> Path:
    if explicit:
        if not explicit.is_file() or explicit.suffix.lower() != ".pdf":
            raise FileNotFoundError(f"Source PDF not found: {explicit}")
        return explicit.resolve()
    candidates = [root / folder / f"lesson{lesson}.pdf" for folder in ("raw_materials", "archive_pdfs")]
    found = next((path for path in candidates if path.is_file()), None)
    if found is None:
        raise FileNotFoundError(f"Provide a pre-split PDF with --source; tried {candidates}")
    return found.resolve()


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _files(data: dict, root: Path, *, slides=False, narration=False, lesson_audio=False) -> list[Path]:
    values = []
    if narration:
        values.append((data.get("explanation_narration_audio") or {}).get("audio_file", ""))
    if lesson_audio:
        assets = data.get("lesson_audio_assets") or {}
        values += [item.get("local_audio_file", "") for item in assets.get("items", [])]
        values.append((assets.get("full_audio") or {}).get("local_audio_file", ""))
    if slides:
        values += [slide.get(kind, {}).get("local_path", "") for slide in (data.get("teaching_slide_deck") or {}).get("slides", []) for kind in ("image", "audio")]
    return [resolve_artifact_path(value, root) for value in values if value]


def _settings(prefix: str) -> str:
    return fingerprint({key: value for key, value in os.environ.items() if key.startswith(prefix) and not any(secret in key for secret in ("KEY", "TOKEN", "SECRET", "PASSWORD"))})


def _history(root: Path, lesson: int) -> dict:
    memory_file = root / "vocab_memory/global_vocab_memory.json"
    memory = _read(memory_file) if memory_file.is_file() else {}
    result = {}
    for word, entries in memory.items():
        prior = [entry for entry in entries if int(entry.get("lesson_id") or 0) < lesson] if isinstance(entries, list) else []
        if prior:
            result[word] = prior
    return result


def run(args, root: Path = ROOT) -> dict:
    if STAGES.index(args.from_stage) > STAGES.index(args.through):
        raise ValueError("--from-stage must precede --through")
    if args.images_only and (args.from_stage != "slides" or args.through not in {"slides", "verify", "publish"}):
        raise ValueError("--images-only requires --from-stage slides")
    working = root / "output_json" / args.lang / lesson_json(root, args.lesson, args.lang).name
    written = working
    shared = CheckpointStore(root / "workflow" / f"lesson{args.lesson}" / "shared")
    localized = CheckpointStore(root / "workflow" / f"lesson{args.lesson}" / args.lang)
    stages = STAGES[STAGES.index(args.from_stage): STAGES.index(args.through) + 1]
    preflight(stages)
    content_files = ["content_extractor.py", "notes_extractor.py", "quiz_generator.py", "_explanation_writer.py", "video_director.py", "render_planner.py"]
    code = code_digest([PIPELINE_DIR / "quality.py", PIPELINE_DIR / "agent.py", *[PIPELINE_DIR / "tasks" / name for name in content_files]])
    provider = None

    def llm():
        nonlocal provider
        if provider is None:
            from content_builder.core.llm_providers import LLMFactory
            provider = LLMFactory.create_provider()
        return provider

    def check(data, *, media=False):
        report = audit_lesson(data, artifact_root=root, lang=args.lang if media else (data.get("localization") or {}).get("target_lang", "en"), media=media, deep=media)
        report_file = root / "reports" / args.lang / f"lesson{args.lesson}_{'media' if media else 'content'}.json"
        atomic_write_json(report_file, report)
        require_quality(report)
        return report

    with build_lock(root / "workflow" / f"lesson{args.lesson}.lock"):
        data = None
        if args.from_stage != "content":
            input_lang = "en" if args.from_stage in {"lesson_audio", "localize"} else args.lang
            data = _read(args.input_json or lesson_json(root, args.lesson, input_lang))
            if data.get("lesson_metadata", {}).get("lesson_id") != args.lesson:
                raise ValueError("Input JSON lesson_id does not match --lesson")
            check(data)
        for stage in stages:
            if stage == "content":
                source = None if args.input_json else source_pdf(root, args.lesson, args.source)
                def content():
                    if args.input_json:
                        result = _read(args.input_json)
                    else:
                        from content_builder.zh.integrated_chinese.agent import ContentCreatorAgent
                        result = ContentCreatorAgent(llm(), root).generate_content(str(source), args.lesson, args.course_id,
                            checkpoint_dir=shared.root / "tasks", render_lesson_audio=False, update_memory=False, force="content" in args.force, raise_on_error=True)
                    if not isinstance(result, dict) or result.get("lesson_metadata", {}).get("lesson_id") != args.lesson:
                        raise ValueError("Content generation failed or lesson_id mismatched")
                    if (result.get("localization") or {}).get("target_lang", "en") != "en":
                        raise ValueError("The shared content stage requires the English source lesson")
                    report = audit_lesson(result, artifact_root=root, lang="en")
                    atomic_write_json(root / "reports/en" / f"lesson{args.lesson}_content.json", report)
                    require_quality(report)
                    return result
                data = shared.run("content", {"source": file_digest(args.input_json or source), "course": args.course_id,
                    "code": code, "model": _settings("LLM_"), "task_settings": _settings("CONTENT_TASK"),
                    "practice_settings": _settings("PRACTICE_"), "history": _history(root, args.lesson)}, content, force="content" in args.force)
                # Commit vocabulary only after the complete content gate passes.
                from content_builder.zh.integrated_chinese.tasks.quiz_generator import Task2QuizGenerator
                Task2QuizGenerator(None, root).save_memory(data["course_content"]["vocabulary"], args.lesson)
                atomic_write_json(root / "output_json/en" / f"lesson{args.lesson}_data.json", data)
            elif stage == "lesson_audio":
                def target_audio():
                    from content_builder.zh.integrated_chinese.tasks.dialogue_audio import Task4BLessonAudioRenderer
                    result = copy.deepcopy(data)
                    renderer = Task4BLessonAudioRenderer()
                    result["lesson_audio_assets"] = renderer.render_sentence_audio_assets(result, root / "output_audio" / f"lesson{args.lesson}")["lesson_audio_assets"]
                    if not result["lesson_audio_assets"].get("items") or any(item.get("status") != "ready" for item in result["lesson_audio_assets"]["items"]):
                        raise ValueError("Textbook sentence audio is incomplete")
                    return result
                data = shared.run(stage, {"data": data, "tts": _settings("TTS_TENCENT"), "code": file_digest(PIPELINE_DIR / "tasks/dialogue_audio.py")}, target_audio,
                    force=stage in args.force, outputs=lambda value: _files(value, root, lesson_audio=True))
            elif stage == "localize" and args.lang != "en":
                source = root / "output_json/en" / f"lesson{args.lesson}_data.json"
                atomic_write_json(source, data)
                def localize():
                    from content_builder.zh.integrated_chinese.scripts.localize import translate_lesson
                    result = translate_lesson(source, args.lang, llm())
                    require_quality(audit_lesson(result, artifact_root=root, lang=args.lang))
                    return result
                localize_code = file_digest(PIPELINE_DIR / "scripts/localize.py")
                source_audio = data.get("lesson_audio_assets")
                localization_input = {key: value for key, value in data.items() if key not in {"lesson_audio_assets", "explanation_narration_audio", "teaching_slide_deck", "llm_usage"}}
                data = localized.run(stage, {"data": localization_input, "lang": args.lang, "code": localize_code, "llm": _settings("LLM_")}, localize, force=stage in args.force)
                if source_audio is not None:
                    data["lesson_audio_assets"] = source_audio
            elif stage == "narration":
                signature = narration_fingerprint(data, args.lang)
                def narrate():
                    from content_builder.zh.integrated_chinese.tasks.narration_audio import Task4DExplanationNarrator
                    result = copy.deepcopy(data)
                    narrator = Task4DExplanationNarrator()
                    narrator.duration_mode = "actual"
                    narrator.duration_buffer_seconds = 0.5
                    audio = narrator.run(result["video_render_plan"]["explanation"], root / "output_audio" / args.lang / f"lesson{args.lesson}_narration", args.lang)
                    apply_narration_timings(result, audio)
                    audio["input_fingerprint"] = signature
                    return audio
                audio = localized.run(stage, {"signature": signature}, narrate, force=stage in args.force,
                    outputs=lambda value: [resolve_artifact_path(value["audio_file"], root)])
                apply_narration_timings(data, audio)
                data["explanation_narration_audio"] = audio
            elif stage == "slides":
                # build_deck has its own content/template fingerprint; do not put
                # a second cache in front of it that could hide template changes.
                from content_builder.zh.integrated_chinese.scripts.build_teaching_slide_deck import build_deck
                atomic_write_json(working, data)
                build_deck(working, "integrated_chinese", args.lang, force=stage in args.force, images_only=args.images_only)
                data = _read(working)
            elif stage == "verify":
                check(data, media=True)
            elif stage == "publish":
                # Recheck on every publish; external state cannot be checkpointed.
                check(data, media=True)
                atomic_write_json(working, data)
                command = [sys.executable, str(default_paths().backend_dir / "database/sync_to_db.py"), "--pipeline", "integrated_chinese", "--lang", args.lang, "--strict", str(working.resolve())]
                subprocess.run(command, cwd=default_paths().backend_dir, check=True)
                return {"status": "published", "json": str(lesson_json(root, args.lesson, args.lang))}
            if data is not None:
                written = working if stage not in {"content", "lesson_audio"} or args.lang == "en" else root / "output_json/en" / f"lesson{args.lesson}_data.json"
                atomic_write_json(written, data)
        receipt = {"status": "verified" if "verify" in stages else "draft", "lesson_id": args.lesson,
                   "lang": args.lang, "completed_stages": list(stages), "json": str(written.resolve())}
        atomic_write_json(root / "workflow" / f"lesson{args.lesson}" / args.lang / "latest.json", receipt)
        return receipt


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Integrated Chinese: PDF → content/practice → TTS → caption-free WebP slides → validation → optional publishing")
    parser.add_argument("command", choices=("plan", "run", "check"))
    parser.add_argument("--lesson", type=int)
    parser.add_argument("--all", action="store_true", help="Check all existing lesson JSONs")
    parser.add_argument("--lang", default="en")
    parser.add_argument("--course-id", type=int, default=1)
    parser.add_argument("--source", type=Path, help="A pre-split lesson PDF")
    parser.add_argument("--input-json", type=Path, help="Explicitly adopt existing content, or start at a downstream stage")
    parser.add_argument("--from-stage", choices=STAGES, default="content")
    parser.add_argument("--through", choices=STAGES, default="verify")
    parser.add_argument("--force", nargs="*", choices=STAGES, default=[])
    parser.add_argument("--images-only", action="store_true", help="Keep existing narration/captions during a visual refresh")
    parser.add_argument("--media", action="store_true", help="Check delivery assets as well as lesson content")
    parser.add_argument("--deep", action="store_true", help="Decode images and probe every audio file during check")
    args = parser.parse_args(argv)
    from dotenv import load_dotenv
    load_dotenv(default_paths().backend_dir / ".env")
    if args.lang not in {"en", "fr", "de", "es", "ja", "ko", "vi", "ar", "th", "pt", "ru", "id", "ms", "it"}:
        parser.error("Unsupported learner language")
    if args.lesson is None and not (args.command == "check" and (args.all or args.input_json)):
        parser.error("--lesson is required")
    if args.lesson is not None and args.lesson <= 0:
        parser.error("--lesson must be positive")
    try:
        if args.command == "plan":
            print(json.dumps({"lesson": args.lesson, "lang": args.lang, "stages": STAGES[STAGES.index(args.from_stage):STAGES.index(args.through)+1],
                "source": str(args.source or ROOT / 'raw_materials' / f'lesson{args.lesson}.pdf'),
                "input_json": str(args.input_json or ""), "publish": args.through == "publish"}, ensure_ascii=False, indent=2))
            return 0
        if args.command == "run":
            print(json.dumps(run(args), ensure_ascii=False, indent=2))
            return 0
        if args.input_json:
            files = [args.input_json]
        elif args.all:
            by_name = {path.name: path for path in (ROOT / "synced_json" / args.lang).glob("*_data*.json")}
            by_name.update({path.name: path for path in (ROOT / "output_json" / args.lang).glob("*_data*.json")})
            files = sorted(by_name.values())
        else:
            files = [lesson_json(ROOT, args.lesson, args.lang)]
        reports = []
        for path in files:
            try:
                report = audit_lesson(_read(path), artifact_root=ROOT, lang=args.lang, media=args.media, deep=args.deep)
            except (OSError, ValueError, TypeError, AttributeError, KeyError) as exc:
                report = {"ok": False, "issues": [{"severity": "error", "code": "input", "message": str(exc)}]}
            reports.append({"file": str(path), **report})
        output = ROOT / "reports" / args.lang / f"audit_{'media' if args.media else 'content'}.json"
        atomic_write_json(output, {"lessons": reports})
        passed = sum(report["ok"] for report in reports)
        print(f"Passed {passed}/{len(reports)} lesson(s). Report: {output}")
        return 0 if reports and passed == len(reports) else 1
    except Exception as exc:
        print(f"Workflow failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
