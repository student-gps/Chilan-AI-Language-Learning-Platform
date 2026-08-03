MAX_ACTIVE_COURSES = 2
ACTIVE_COURSE_STATUS = "active"
PAUSED_COURSE_STATUS = "paused"
COMPLETED_COURSE_STATUS = "completed"
VALID_COURSE_STATUSES = (
    ACTIVE_COURSE_STATUS,
    PAUSED_COURSE_STATUS,
    COMPLETED_COURSE_STATUS,
)

_USER_COURSES_STATUS_SCHEMA_READY = False


def ensure_course_query_indexes(cur):
    """Create indexes used by course, enrollment, and Classroom aggregate queries."""
    cur.execute("""
        CREATE INDEX IF NOT EXISTS progress_items_user_text_item_idx
        ON user_progress_of_language_items ((user_id::text), item_id)
        INCLUDE (is_mastered);
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS review_logs_user_text_time_course_idx
        ON review_logs ((user_id::text), review_time, course_id)
        INCLUDE (item_id, state);
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS review_logs_user_text_new_time_course_idx
        ON review_logs ((user_id::text), review_time, course_id)
        WHERE state = 0;
    """)


def ensure_user_courses_status(cur):
    global _USER_COURSES_STATUS_SCHEMA_READY
    if _USER_COURSES_STATUS_SCHEMA_READY:
        return

    cur.execute("""
        ALTER TABLE user_courses
        ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active';
    """)
    cur.execute("""
        UPDATE user_courses
        SET status = 'active'
        WHERE status IS NULL OR status = '';
    """)
    cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'user_courses_status_check'
            ) THEN
                ALTER TABLE user_courses
                ADD CONSTRAINT user_courses_status_check
                CHECK (status IN ('active', 'paused', 'completed'));
            END IF;
        END $$;
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS user_courses_user_status_idx
        ON user_courses (user_id, status);
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS user_courses_user_text_status_course_idx
        ON user_courses ((user_id::text), status, course_id);
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS language_items_course_item_idx
        ON language_items (course_id, item_id);
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS progress_items_user_text_review_item_idx
        ON user_progress_of_language_items ((user_id::text), next_review, item_id);
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS review_logs_user_text_course_time_idx
        ON review_logs ((user_id::text), course_id, review_time);
    """)
    ensure_course_query_indexes(cur)
    _USER_COURSES_STATUS_SCHEMA_READY = True
