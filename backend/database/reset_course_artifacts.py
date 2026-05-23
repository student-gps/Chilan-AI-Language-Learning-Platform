"""
Course-scoped reset tool used by the dev UI and by local maintenance.

Examples:
  python backend/database/reset_course_artifacts.py --pipeline minna_no_nihongo --course-id 303 --lang zh --actions db,r2 --dry-run
  python backend/database/reset_course_artifacts.py --pipeline minna_no_nihongo --course-id 303 --lang zh --actions db --confirm-code RESET-303
  python backend/database/reset_course_artifacts.py --pipeline integrated_chinese --course-id 1 --lang en --actions restore_synced --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

load_dotenv(BACKEND_DIR / ".env")

from services.maintenance.course_reset import build_request, execute_reset


def main() -> None:
    parser = argparse.ArgumentParser(description="Preview or execute course-scoped reset actions.")
    parser.add_argument("--pipeline", default="minna_no_nihongo")
    parser.add_argument("--course-id", type=int, default=303)
    parser.add_argument("--lang", default="zh")
    parser.add_argument("--actions", default="db", help="Comma-separated: db,r2,restore_synced,local_stage2")
    parser.add_argument("--lesson-start", type=int, default=None)
    parser.add_argument("--lesson-end", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true", help="Preview only. Recommended before every execute.")
    parser.add_argument("--confirm-code", default="", help="Required for execution, e.g. RESET-303.")
    args = parser.parse_args()

    req = build_request(
        pipeline=args.pipeline,
        course_id=args.course_id,
        lang=args.lang,
        actions=args.actions,
        lesson_start=args.lesson_start,
        lesson_end=args.lesson_end,
        dry_run=args.dry_run,
        confirm=bool(args.confirm_code),
        confirm_code=args.confirm_code,
    )
    report = execute_reset(req)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
