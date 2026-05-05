"""
Batch-compress all slide PNGs in output_slides/ to WebP (quality=85).
Replaces .png with .webp in place and patches lesson JSON files to match.

Usage:
    python compress_slides_to_webp.py               # all pipelines
    python compress_slides_to_webp.py --dry-run     # preview only, no changes
    python compress_slides_to_webp.py --pipeline integrated_chinese
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: pip install Pillow")

ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"
WEBP_QUALITY = 85
_SLIDE_PNG_RE = re.compile(r"(slide_\d+)\.png")


_SKIP_DIR_SUFFIXES = ("_backup", "_test", "_bak")


def _is_standard_slide_dir(png_path: Path) -> bool:
    """Only process dirs named lessonNNN (not backup/test dirs)."""
    return not any(png_path.parent.name.endswith(s) for s in _SKIP_DIR_SUFFIXES)


def convert_png(png_path: Path, dry_run: bool) -> tuple[int, int]:
    """Convert one PNG to WebP q85; delete original. Returns (old_bytes, new_bytes)."""
    if not png_path.exists():
        return 0, 0
    old_bytes = png_path.stat().st_size
    webp_path = png_path.with_suffix(".webp")
    if dry_run:
        return old_bytes, 0
    img = Image.open(png_path)
    img.save(webp_path, "WEBP", quality=WEBP_QUALITY, method=6)
    new_bytes = webp_path.stat().st_size
    png_path.unlink()
    return old_bytes, new_bytes


def patch_json(json_path: Path, dry_run: bool) -> int:
    """Replace slide_NNN.png → slide_NNN.webp in a JSON file. Returns hit count."""
    text = json_path.read_text(encoding="utf-8")
    if not _SLIDE_PNG_RE.search(text):
        return 0
    new_text = _SLIDE_PNG_RE.sub(r"\1.webp", text)
    count = len(_SLIDE_PNG_RE.findall(text))
    if not dry_run:
        json_path.write_text(new_text, encoding="utf-8")
    return count


def run(pipeline_filter: str | None, dry_run: bool) -> None:
    tag = "[DRY-RUN] " if dry_run else ""

    # ── 1. Convert PNGs ──────────────────────────────────────────────────────
    total_old = total_new = png_count = 0
    slides_root = ARTIFACTS_DIR
    for png_path in sorted(slides_root.rglob("output_slides/**/*.png")):
        if pipeline_filter and pipeline_filter not in str(png_path):
            continue
        if not _is_standard_slide_dir(png_path):
            continue
        old, new = convert_png(png_path, dry_run)
        total_old += old
        total_new += new
        png_count += 1
        rel = png_path.relative_to(ARTIFACTS_DIR)
        if dry_run:
            print(f"  {tag}{rel}  {old // 1024}KB → WebP q{WEBP_QUALITY}")
        else:
            pct = new / old * 100 if old else 0
            print(f"  {rel}  {old // 1024}KB → {new // 1024}KB ({pct:.0f}%)")

    if png_count == 0:
        print("No PNG slides found (already converted or wrong path).")
    else:
        saved = total_old - total_new
        print(
            f"\n{'[DRY-RUN] ' if dry_run else ''}Images: {png_count} files, "
            f"{total_old / 1_048_576:.1f} MB → {total_new / 1_048_576:.1f} MB "
            f"(saved {saved / 1_048_576:.1f} MB)"
            if not dry_run
            else f"\n[DRY-RUN] Would convert {png_count} PNG files."
        )

    # ── 2. Patch JSON references ─────────────────────────────────────────────
    json_dirs = ["output_json", "synced_json"]
    json_hits = json_count = 0
    for pipeline_dir in ARTIFACTS_DIR.iterdir():
        if not pipeline_dir.is_dir():
            continue
        if pipeline_filter and pipeline_filter not in pipeline_dir.name:
            continue
        for sub in json_dirs:
            for json_path in (pipeline_dir / sub).rglob("*.json"):
                hits = patch_json(json_path, dry_run)
                if hits:
                    json_count += 1
                    json_hits += hits
                    print(f"  {tag}patched {json_path.relative_to(ARTIFACTS_DIR)}  ({hits} refs)")

    if json_hits:
        print(f"\n{tag}JSON: {json_count} files, {json_hits} references updated.")
    else:
        print(f"\n{tag}No JSON slide references needed patching.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compress slide PNGs to WebP q85 in place.")
    parser.add_argument("--pipeline", help="Limit to one pipeline dir (e.g. integrated_chinese)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    args = parser.parse_args()
    run(args.pipeline, args.dry_run)


if __name__ == "__main__":
    main()
