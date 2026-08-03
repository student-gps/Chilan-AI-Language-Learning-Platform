from typing import Any

from fastapi import HTTPException

from services.course_enrollment_service import ACTIVE_COURSE_STATUS


def assert_lesson_belongs_to_course(cur, *, course_id: int, lesson_id: int) -> None:
    cur.execute(
        """
        SELECT 1
        FROM lessons
        WHERE course_id = %s
          AND lesson_id = %s
        """,
        (course_id, lesson_id),
    )
    if cur.fetchone() is None:
        raise HTTPException(status_code=404, detail="Lesson not found in this course")


def is_active_course_enrollment(cur, *, user_id: str, course_id: int) -> bool:
    cur.execute(
        """
        SELECT 1
        FROM user_courses
        WHERE user_id::text = %s
          AND course_id = %s
          AND status = %s
        """,
        (user_id, course_id, ACTIVE_COURSE_STATUS),
    )
    return cur.fetchone() is not None


def assert_active_course_enrollment(cur, *, user_id: str, course_id: int) -> None:
    if not is_active_course_enrollment(cur, user_id=user_id, course_id=course_id):
        raise HTTPException(status_code=403, detail="Active course enrollment required")


def get_item_course_context(cur, *, item_id: int) -> dict[str, Any]:
    cur.execute(
        """
        SELECT item_id, course_id, lesson_id, question_id, question_type,
               original_text, original_pinyin, standard_answers, metadata
        FROM language_items
        WHERE item_id = %s
        """,
        (item_id,),
    )
    item = cur.fetchone()
    if not item:
        raise HTTPException(status_code=404, detail="Practice item not found")
    return item


def get_lesson_audio_asset(
    cur,
    *,
    course_id: int,
    lesson_id: int,
    asset_ref: str,
) -> dict[str, Any]:
    cur.execute(
        """
        SELECT lesson_audio_assets
        FROM lessons
        WHERE course_id = %s
          AND lesson_id = %s
        """,
        (course_id, lesson_id),
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Lesson not found in this course")

    assets = row.get("lesson_audio_assets") if isinstance(row, dict) else row[0]
    assets = assets if isinstance(assets, dict) else {}
    normalized_ref = str(asset_ref or "").strip()
    if normalized_ref == "full":
        asset = assets.get("full_audio") if isinstance(assets.get("full_audio"), dict) else None
    elif normalized_ref.startswith("line:"):
        line_ref = normalized_ref.removeprefix("line:")
        asset = next((
            item for item in assets.get("items", [])
            if isinstance(item, dict) and str(item.get("line_ref")) == line_ref
        ), None)
    elif normalized_ref.startswith("audio:"):
        audio_id = normalized_ref.removeprefix("audio:")
        asset = next((
            item for item in assets.get("items", [])
            if isinstance(item, dict) and str(item.get("audio_id")) == audio_id
        ), None)
    else:
        asset = None

    object_key = (asset or {}).get("object_key") if isinstance(asset, dict) else ""
    if not object_key:
        raise HTTPException(status_code=404, detail="Lesson audio asset not found")
    return {"asset_ref": normalized_ref, "object_key": object_key}
