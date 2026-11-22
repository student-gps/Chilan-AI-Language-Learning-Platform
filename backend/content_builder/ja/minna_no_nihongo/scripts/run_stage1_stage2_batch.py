from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
MNN_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = MNN_DIR.parents[3]
PYTHON = Path(sys.executable)


def _lesson_slug(lesson_id: int) -> str:
    return f"lesson{lesson_id:03d}"


def _default_log_path(start: int, end: int, lang: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return MNN_DIR / "artifacts" / "logs" / f"batch_stage1_stage2_{lang}_{start:03d}_{end:03d}_{stamp}.log"


def _stream_command(command: list[str], *, cwd: Path, log_handle) -> int:
    line = f"\n$ {' '.join(command)}\n"
    print(line, end="")
    log_handle.write(line)
    log_handle.flush()

    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env={**os.environ, "PYTHONUNBUFFERED": "1"},
    )
    assert process.stdout is not None
    for output_line in process.stdout:
        print(output_line, end="")
        log_handle.write(output_line)
    return_code = process.wait()
    footer = f"\n[exit={return_code}] {' '.join(command)}\n"
    print(footer, end="")
    log_handle.write(footer)
    log_handle.flush()
    return return_code


def _stage1_command(args, lesson_id: int) -> list[str]:
    command = [
        str(PYTHON),
        "-u",
        str(MNN_DIR / "build_lesson.py"),
        "--lesson",
        _lesson_slug(lesson_id),
        "--support-lang",
        args.lang,
    ]
    if args.force_stage1:
        command.append("--force")
    return command


def _stage2_command(args, lesson_id: int) -> list[str]:
    json_path = MNN_DIR / "artifacts" / "output_json" / args.lang / f"{_lesson_slug(lesson_id)}_data.json"
    command = [
        str(PYTHON),
        "-u",
        str(SCRIPT_DIR / "render_narration.py"),
        str(json_path),
        "--lang",
        args.lang,
    ]
    if args.force_narration:
        command.append("--force-narration")
    if args.force_slides:
        command.append("--force-slides")
    if args.refresh_render_plan:
        command.append("--refresh-render-plan")
    return command


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MNN Stage 1 + Stage 2 for a lesson range.")
    parser.add_argument("--start", type=int, required=True, help="First lesson number, e.g. 2.")
    parser.add_argument("--end", type=int, required=True, help="Last lesson number, e.g. 7.")
    parser.add_argument("--lang", default="zh", help="Support/native language, default zh.")
    parser.add_argument("--force-stage1", action="store_true", help="Overwrite existing lesson JSON.")
    parser.add_argument("--force-narration", action="store_true", help="Regenerate narration audio.")
    parser.add_argument("--force-slides", action="store_true", help="Regenerate static slide images.")
    parser.add_argument(
        "--refresh-render-plan",
        action="store_true",
        help="Refresh render plan during Stage 2. Normally leave off to preserve Stage 1 output.",
    )
    parser.add_argument("--delay-seconds", type=float, default=8.0, help="Pause between lessons to reduce TTS throttling.")
    parser.add_argument("--stop-on-error", action="store_true", help="Stop immediately on the first failed stage.")
    parser.add_argument("--log-file", type=Path, default=None, help="Optional log file path.")
    args = parser.parse_args()

    if args.end < args.start:
        raise ValueError("--end must be >= --start")

    log_path = args.log_file or _default_log_path(args.start, args.end, args.lang)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"🧪 MNN batch Stage 1+2: lesson{args.start:03d}..lesson{args.end:03d} [lang={args.lang}]")
    print(f"🧾 Log: {log_path}")

    results: list[tuple[int, str, int]] = []
    with log_path.open("w", encoding="utf-8") as log_handle:
        log_handle.write(f"MNN batch Stage 1+2 started at {datetime.now().isoformat(timespec='seconds')}\n")
        for lesson_id in range(args.start, args.end + 1):
            slug = _lesson_slug(lesson_id)
            header = f"\n{'=' * 72}\n🚀 {slug}: Stage 1\n{'=' * 72}\n"
            print(header, end="")
            log_handle.write(header)

            stage1_code = _stream_command(_stage1_command(args, lesson_id), cwd=PROJECT_ROOT, log_handle=log_handle)
            results.append((lesson_id, "stage1", stage1_code))
            if stage1_code != 0:
                print(f"❌ {slug}: Stage 1 failed.")
                if args.stop_on_error:
                    break
                continue

            header = f"\n{'=' * 72}\n🎙️ {slug}: Stage 2\n{'=' * 72}\n"
            print(header, end="")
            log_handle.write(header)
            stage2_code = _stream_command(_stage2_command(args, lesson_id), cwd=PROJECT_ROOT, log_handle=log_handle)
            results.append((lesson_id, "stage2", stage2_code))
            if stage2_code != 0 and args.stop_on_error:
                print(f"❌ {slug}: Stage 2 failed.")
                break

            if lesson_id < args.end and args.delay_seconds > 0:
                print(f"⏳ Waiting {args.delay_seconds:.1f}s before next lesson...")
                time.sleep(args.delay_seconds)

        log_handle.write(f"\nMNN batch finished at {datetime.now().isoformat(timespec='seconds')}\n")

    failed = [(lesson_id, stage, code) for lesson_id, stage, code in results if code != 0]
    print("\n" + "=" * 72)
    if failed:
        print(f"⚠️ Batch finished with {len(failed)} failed stage(s):")
        for lesson_id, stage, code in failed:
            print(f"  - lesson{lesson_id:03d} {stage}: exit={code}")
        print(f"🧾 Full log: {log_path}")
        return 1

    print(f"✅ Batch finished successfully: lesson{args.start:03d}..lesson{args.end:03d}")
    print(f"🧾 Full log: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
