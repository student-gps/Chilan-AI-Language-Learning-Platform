from database.connection import get_connection


def ensure_lesson_progress_columns(cur):
    cur.execute("""
        ALTER TABLE user_progress_of_lessons
        ADD COLUMN IF NOT EXISTS practice_question_index INTEGER DEFAULT 0;
    """)
    cur.execute("""
        ALTER TABLE user_progress_of_lessons
        ADD COLUMN IF NOT EXISTS practice_question_updated_at TIMESTAMP;
    """)


def mark_lesson_content_viewed(user_id: str, course_id: int, lesson_id: int):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        ensure_lesson_progress_columns(cur)
        cur.execute(
            """
            INSERT INTO user_progress_of_lessons (user_id, course_id, viewed_lesson_id)
            VALUES (%s::uuid, %s, %s)
            ON CONFLICT (user_id, course_id)
            DO UPDATE SET viewed_lesson_id = EXCLUDED.viewed_lesson_id;
            """,
            (user_id, course_id, lesson_id),
        )
        conn.commit()
        return {"status": "success"}
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def save_practice_progress(user_id: str, course_id: int, lesson_id: int, current_index: int):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        ensure_lesson_progress_columns(cur)
        cur.execute(
            """
            INSERT INTO user_progress_of_lessons (user_id, course_id, viewed_lesson_id, practice_question_index, practice_question_updated_at)
            VALUES (%s::uuid, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id, course_id)
            DO UPDATE SET
                viewed_lesson_id = EXCLUDED.viewed_lesson_id,
                practice_question_index = EXCLUDED.practice_question_index,
                practice_question_updated_at = CURRENT_TIMESTAMP;
            """,
            (user_id, course_id, lesson_id, max(current_index, 0)),
        )
        conn.commit()
        return {"status": "success"}
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def complete_lesson(user_id: str, course_id: int, lesson_id: int):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        ensure_lesson_progress_columns(cur)
        cur.execute(
            """
            INSERT INTO user_progress_of_lessons (user_id, course_id, last_completed_lesson_id)
            VALUES (%s::uuid, %s, %s)
            ON CONFLICT (user_id, course_id)
            DO UPDATE SET
                last_completed_lesson_id = GREATEST(user_progress_of_lessons.last_completed_lesson_id, EXCLUDED.last_completed_lesson_id),
                practice_question_index = 0,
                practice_question_updated_at = NULL;
            """,
            (user_id, course_id, lesson_id),
        )
        conn.commit()
        return {"status": "success", "message": f"Lesson {lesson_id} marked as completed."}
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
