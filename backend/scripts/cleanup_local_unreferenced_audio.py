"""Clean local audio files that are not referenced by current JSON/DB object_keys.

By default this is a dry run. It treats every local_path attached to an
object_key in local JSONs or the database as protected. That keeps dialogue
audio, full dialogue audio, slide narration audio, and any other R2-bound media.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from database.connection import get_connection


ARTIFACTS_DIR = BACKEND_DIR / "content_builder" / "artifacts"
AUDIO_ROOT = ARTIFACTS_DIR / "integrated_chinese" / "output_audio"


def human_size(value: int) -> str:
    size = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.2f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.2f} TB"


def resolve_local_path(value: str) -> Path | None:
    if not value:
        return None
    raw = Path(value)
    candidates = [raw]
    parts = raw.parts
    try:
        index = next(i for i, part in enumerate(parts) if part.lower() == "artifacts")
    except StopIteration:
        index = -1
    if index >= 0:
        tail = Path(*parts[index + 1 :])
        candidates.append(ARTIFACTS_DIR / tail)
        if tail.parts and tail.parts[0] in {"integrated_chinese", "new_concept_english"}:
            candidates.append(ARTIFACTS_DIR / Path(*tail.parts[1:]))
    for candidate in candidates:
        try:
            return candidate.resolve()
        except OSError:
            continue
    return None


def extract_protected_local_audio(value) -> set[Path]:
    protected: set[Path] = set()
    if isinstance(value, dict):
        object_key = value.get("object_key")
        local_path = value.get("local_path") or value.get("local_audio_file") or value.get("audio_file")
        if isinstance(object_key, str) and object_key.strip() and isinstance(local_path, str):
            resolved = resolve_local_path(local_path)
            if resolved and AUDIO_ROOT.resolve() in resolved.parents:
                protected.add(resolved)
        for child in value.values():
            protected.update(extract_protected_local_audio(child))
    elif isinstance(value, list):
        for child in value:
            protected.update(extract_protected_local_audio(child))
    return protected


def collect_local_json_protected() -> set[Path]:
    protected: set[Path] = set()
    for path in ARTIFACTS_DIR.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        protected.update(extract_protected_local_audio(data))
    return protected


def collect_db_protected() -> set[Path]:
    protected: set[Path] = set()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT lesson_metadata, course_content, teaching_materials, video_plan,
               video_render_plan, lesson_audio_assets, explanation_video_urls
        FROM lessons;
        """
    )
    for row in cur.fetchall():
        for value in row:
            protected.update(extract_protected_local_audio(value))
    cur.close()
    conn.close()
    return protected


def classify(path: Path) -> str:
    name = path.name.lower()
    folder = path.parent.name.lower()
    if name.startswith("lesson") and "_slide_" in name:
        return "slide_audio_unreferenced"
    if name.startswith("lesson") and "_narration" in name:
        return "full_narration_unreferenced"
    if name.startswith("raw_"):
        return "raw_tmp"
    if name.startswith("padded_"):
        return "padded_tmp"
    if folder.startswith("_tmp"):
        return "tmp_folder"
    return "other_unreferenced"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--delete", action="store_true", help="Actually delete candidates.")
    parser.add_argument("--top", type=int, default=40)
    args = parser.parse_args()

    if not AUDIO_ROOT.exists():
        raise SystemExit(f"Audio root not found: {AUDIO_ROOT}")

    print("Collecting protected audio local_paths from JSON and DB...")
    protected = collect_local_json_protected() | collect_db_protected()
    all_audio = [path.resolve() for path in AUDIO_ROOT.rglob("*.mp3")]
    candidates = [path for path in all_audio if path not in protected]

    total = sum(path.stat().st_size for path in all_audio if path.exists())
    protected_size = sum(path.stat().st_size for path in protected if path.exists())
    candidate_size = sum(path.stat().st_size for path in candidates if path.exists())

    print(f"audio_root={AUDIO_ROOT}")
    print(f"all_audio: count={len(all_audio)} size={human_size(total)}")
    print(f"protected: count={len(protected)} existing={sum(1 for p in protected if p.exists())} size={human_size(protected_size)}")
    print(f"delete_candidates: count={len(candidates)} size={human_size(candidate_size)}")

    by_type: dict[str, list[Path]] = defaultdict(list)
    for path in candidates:
        by_type[classify(path)].append(path)

    print("\nCandidate groups:")
    for label, paths in sorted(by_type.items(), key=lambda item: sum(p.stat().st_size for p in item[1] if p.exists()), reverse=True):
        size = sum(path.stat().st_size for path in paths if path.exists())
        print(f"  {label:32} count={len(paths):6} size={human_size(size):>10}")

    print("\nLargest candidates:")
    for path in sorted(candidates, key=lambda p: p.stat().st_size if p.exists() else 0, reverse=True)[: args.top]:
        print(f"  {human_size(path.stat().st_size):>10}  {path}")

    if not args.delete:
        print("\nDry run only. Re-run with --delete to remove candidates.")
        return

    deleted = 0
    failed = 0
    for path in candidates:
        try:
            path.unlink()
            deleted += 1
        except Exception as exc:
            print(f"  failed: {path} | {exc}")
            failed += 1
    print(f"\nDeleted files: {deleted}, failed: {failed}, freed up to {human_size(candidate_size)}")


if __name__ == "__main__":
    main()
