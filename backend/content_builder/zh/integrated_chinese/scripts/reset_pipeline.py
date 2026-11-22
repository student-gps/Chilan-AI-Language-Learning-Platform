"""
Deprecated safety wrapper.

The old reset implementation was renamed to dangerous_reset_all_pipeline.py
because it can clear all lessons/practice data and broad R2 media. For routine
maintenance, use the course-scoped reset tools instead:

  Dev UI:
    /dev/course-maintenance

  CLI:
    python backend/database/reset_course_artifacts.py --pipeline integrated_chinese --course-id 1 --lang en --actions db --dry-run
"""

from __future__ import annotations

import sys


MESSAGE = """
This reset_pipeline.py entry point is deprecated and intentionally does nothing.

Use the course-scoped maintenance tools instead:
  - Dev UI: /dev/course-maintenance
  - CLI: backend/database/reset_course_artifacts.py

If you truly need the old all-system destructive reset, run this file directly:
  backend/content_builder/zh/integrated_chinese/scripts/dangerous_reset_all_pipeline.py
"""


def main() -> int:
    print(MESSAGE.strip())
    return 2


if __name__ == "__main__":
    sys.exit(main())
