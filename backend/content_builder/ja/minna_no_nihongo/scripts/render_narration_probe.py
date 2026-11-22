from __future__ import annotations

import argparse
import json
import re
import sys
from copy import deepcopy
from pathlib import Path

from dotenv import load_dotenv

sys.stdout.reconfigure(line_buffering=True)

BACKEND_DIR = Path(__file__).resolve().parents[4]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from content_builder.core.paths import default_paths
from content_builder.zh.integrated_chinese.tasks.narration_audio import (
    Task4DExplanationNarrator,
    _split_sentences,
)


PATHS = default_paths()
BASE_DIR = PATHS.backend_dir
ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"

load_dotenv(dotenv_path=BASE_DIR / ".env")


def _extract_lesson_id(json_path: Path) -> int | None:
    numbers = re.findall(r"\d+", json_path.stem)
    return int(numbers[0]) if numbers else None


def _narration_text(segment: dict, lang: str) -> str:
    track = segment.get("narration_track") if isinstance(segment.get("narration_track"), dict) else {}
    return (
        track.get(f"subtitle_{lang}")
        or track.get("script")
        or track.get("subtitle_zh")
        or track.get("subtitle_en")
        or ""
    ).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a tiny narration probe without touching lesson JSON.")
    parser.add_argument("json_file", help="Lesson JSON path.")
    parser.add_argument("--lang", default="zh", help="Learner language code.")
    parser.add_argument("--segment", type=int, default=1, help="1-based segment index to render.")
    parser.add_argument("--sentence", type=int, default=0, help="1-based sentence index inside the segment. 0 renders the full segment.")
    args = parser.parse_args()

    json_path = Path(args.json_file)
    lesson_id = _extract_lesson_id(json_path) or 0
    data = json.loads(json_path.read_text(encoding="utf-8"))
    plan = (data.get("video_render_plan") or {}).get("explanation") or {}
    segments = plan.get("segments") if isinstance(plan, dict) else []
    if not isinstance(segments, list) or not segments:
        raise SystemExit("No explanation segments found.")
    if not (1 <= args.segment <= len(segments)):
        raise SystemExit(f"--segment must be between 1 and {len(segments)}")

    source_segment = deepcopy(segments[args.segment - 1])
    text = _narration_text(source_segment, args.lang)
    if args.sentence:
        sentences = _split_sentences(text) or [text]
        if not (1 <= args.sentence <= len(sentences)):
            raise SystemExit(f"--sentence must be between 1 and {len(sentences)}")
        text = sentences[args.sentence - 1]
        track = source_segment.setdefault("narration_track", {})
        track["script"] = text
        track[f"subtitle_{args.lang}"] = text
        track["subtitle_zh"] = text
        source_segment["duration_seconds"] = max(4.0, float(len(text)) / 5.0)

    source_segment["segment_id"] = 1
    source_segment["segment_order"] = 1
    probe_plan = {
        "lesson_id": f"{lesson_id:03d}_probe_s{args.segment:03d}" + (f"_sent{args.sentence:02d}" if args.sentence else ""),
        "segments": [source_segment],
    }

    narrator = Task4DExplanationNarrator()
    narrator.duration_mode = "actual"
    narrator.duration_buffer_seconds = 0.2
    output_dir = ARTIFACTS_DIR / "output_audio" / "narration_probes"
    result = narrator.run(probe_plan, output_dir=output_dir, lang=args.lang)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("status") == "ok":
        print(f"🎧 Probe audio: {result.get('audio_file')}")


if __name__ == "__main__":
    main()
