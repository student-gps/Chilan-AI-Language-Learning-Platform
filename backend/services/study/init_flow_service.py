from typing import Any, Dict

from psycopg2.extras import RealDictCursor

from database.connection import get_connection
from services.study.lesson_progress_service import ensure_lesson_progress_columns


def _normalize_video_render_plan(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {"explanation": {}}

    explanation = payload.get("explanation")
    if not isinstance(explanation, dict):
        explanation = {}

    return {"explanation": explanation}


def _normalize_teaching_video(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {"global_config": {}, "scenes": []}

    global_config = payload.get("global_config")
    scenes = payload.get("scenes")

    if not isinstance(global_config, dict):
        global_config = {}
    if not isinstance(scenes, list):
        scenes = []

    return {
        "global_config": global_config,
        "scenes": [scene for scene in scenes if isinstance(scene, dict)],
    }


def _normalize_explanation_video_urls(payload: Any) -> Dict[str, Any]:
    empty = {"media_url": "", "object_key": "", "local_path": "", "youtube_url": "", "bilibili_url": ""}
    if not isinstance(payload, dict):
        return empty
    return {
        "media_url":  (payload.get("media_url") or "").strip(),
        "object_key": (payload.get("object_key") or "").strip(),
        "local_path": (payload.get("local_path") or "").strip(),
        "youtube_url":  (payload.get("youtube_url") or "").strip(),
        "bilibili_url": (payload.get("bilibili_url") or "").strip(),
    }


def _hydrate_explanation_video_urls(payload: Any, cos_media_storage=None) -> Dict[str, Any]:
    urls = _normalize_explanation_video_urls(payload)
    if not cos_media_storage:
        return urls

    object_key = urls.get("object_key", "").strip()
    if object_key:
        try:
            urls["media_url"] = cos_media_storage.resolve_url(object_key)
        except Exception as e:
            print(f"⚠️ R2 video 签名 URL 生成失败: {e}")
    return urls


def _normalize_lesson_audio_assets(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "provider": "",
            "mode": "sentence_audio",
            "default_voice_type": None,
            "role_voice_map": {},
            "codec": "mp3",
            "sample_rate": 16000,
            "include_speakers": False,
            "storage_backend": "local",
            "sentence_gap_ms": 300,
            "full_audio": {
                "status": "missing",
                "audio_url": "",
                "object_key": "",
                "local_audio_file": "",
                "codec": "mp3",
            },
            "items": [],
        }

    items = payload.get("items", [])
    if not isinstance(items, list):
        items = []

    return {
        "provider": payload.get("provider", ""),
        "mode": payload.get("mode", "sentence_audio"),
        "default_voice_type": payload.get("default_voice_type"),
        "role_voice_map": payload.get("role_voice_map", {}) if isinstance(payload.get("role_voice_map"), dict) else {},
        "codec": payload.get("codec", "mp3"),
        "sample_rate": payload.get("sample_rate", 16000),
        "include_speakers": bool(payload.get("include_speakers", False)),
        "storage_backend": payload.get("storage_backend", "local"),
        "sentence_gap_ms": payload.get("sentence_gap_ms", 300),
        "full_audio": payload.get("full_audio", {}) if isinstance(payload.get("full_audio"), dict) else {
            "status": "missing",
            "audio_url": "",
            "object_key": "",
            "local_audio_file": "",
            "codec": payload.get("codec", "mp3"),
        },
        "items": [item for item in items if isinstance(item, dict)],
    }


def _hydrate_lesson_audio_urls(payload: Any, cos_media_storage=None) -> Dict[str, Any]:
    assets = _normalize_lesson_audio_assets(payload)
    if not cos_media_storage:
        return assets

    full_audio = assets.get("full_audio", {})
    if isinstance(full_audio, dict):
        object_key = (full_audio.get("object_key") or "").strip()
        if object_key:
            try:
                full_audio["audio_url"] = cos_media_storage.resolve_url(object_key)
            except Exception as e:
                print(f"⚠️ COS full audio 签名 URL 生成失败: {e}")

    for item in assets.get("items", []):
        object_key = (item.get("object_key") or "").strip()
        if not object_key:
            continue
        try:
            item["audio_url"] = cos_media_storage.resolve_url(object_key)
        except Exception as e:
            print(f"⚠️ COS sentence audio 签名 URL 生成失败: line_ref={item.get('line_ref')} | {e}")

    return assets


def init_study_flow(user_id: str, course_id: int = 1, cos_media_storage=None, lesson_id: int = None):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        ensure_lesson_progress_columns(cur)
        conn.commit()

        # 指定 lesson_id 时跳过 FSRS 复习队列，直接加载该课
        if lesson_id is None:
            cur.execute(
                """
                SELECT
                    q.item_id,
                    q.question_id,
                    q.question_type,
                    q.original_text,
                    q.original_pinyin,
                    q.standard_answers,
                    q.metadata
                FROM language_items q
                JOIN user_progress_of_language_items p ON q.item_id = p.item_id
                WHERE p.user_id::text = %s AND p.next_review <= CURRENT_TIMESTAMP
                ORDER BY p.next_review ASC
                LIMIT 20;
                """,
                (user_id,),
            )
            due_questions = cur.fetchall()
            if due_questions:
                return {"mode": "review", "data": {"pending_items": due_questions}}

        cur.execute(
            """
            SELECT last_completed_lesson_id, viewed_lesson_id, practice_question_index
            FROM user_progress_of_lessons
            WHERE user_id::text = %s AND course_id = %s
            """,
            (user_id, course_id),
        )
        progress = cur.fetchone()

        if progress:
            last_lesson = progress.get("last_completed_lesson_id") or 0
            viewed_lesson = progress.get("viewed_lesson_id") or 0
            practice_question_index = progress.get("practice_question_index") or 0
        else:
            last_lesson = 0
            viewed_lesson = 0
            practice_question_index = 0

        if lesson_id is not None:
            cur.execute(
                """
                SELECT lesson_id, title,
                       lesson_metadata, course_content, teaching_materials,
                       video_plan, video_render_plan, lesson_audio_assets,
                       explanation_video_urls, llm_usage
                FROM lessons
                WHERE course_id = %s AND lesson_id = %s
                """,
                (course_id, lesson_id),
            )
        else:
            cur.execute(
                """
                SELECT lesson_id, title,
                       lesson_metadata, course_content, teaching_materials,
                       video_plan, video_render_plan, lesson_audio_assets,
                       explanation_video_urls, llm_usage
                FROM lessons
                WHERE course_id = %s AND lesson_id > %s
                ORDER BY lesson_id ASC
                LIMIT 1
                """,
                (course_id, last_lesson),
            )
        lesson_row = cur.fetchone()
        if not lesson_row:
            return {"mode": "completed", "message": "恭喜！你已完成本课程的所有内容。"}

        next_lesson_id = lesson_row["lesson_id"]
        lesson_metadata = lesson_row.get("lesson_metadata") or {}
        course_content = lesson_row.get("course_content") or {}
        video_plan = lesson_row.get("video_plan") or {}
        video_render_plan = _normalize_video_render_plan(lesson_row.get("video_render_plan"))
        lesson_audio_assets = _hydrate_lesson_audio_urls(lesson_row.get("lesson_audio_assets"), cos_media_storage)
        explanation_video_urls = _hydrate_explanation_video_urls(lesson_row.get("explanation_video_urls"), cos_media_storage)
        teaching_video = _normalize_teaching_video(
            video_plan.get("dramatization") if isinstance(video_plan.get("dramatization"), dict) else {}
        )

        lesson_metadata = {
            "course_id": course_id,
            "lesson_id": next_lesson_id,
            "title": lesson_metadata.get("title") or lesson_row["title"],
            "content_type": lesson_metadata.get("content_type", "dialogue"),
            **{k: v for k, v in lesson_metadata.items() if k not in {"course_id", "lesson_id", "title", "content_type"}},
        }

        cur.execute(
            """
            SELECT
                item_id,
                question_id,
                question_type,
                original_text,
                original_pinyin,
                standard_answers,
                metadata,
                %s as lesson_id
            FROM language_items
            WHERE course_id = %s AND lesson_id = %s
            ORDER BY question_id ASC
            """,
            (next_lesson_id, course_id, next_lesson_id),
        )
        new_questions = cur.fetchall()
        skip_content = viewed_lesson == next_lesson_id

        return {
            "mode": "teaching",
            "data": {
                "lesson_content": {
                    "lesson_metadata": lesson_metadata,
                    "course_content": course_content,
                    "teaching_video": teaching_video,
                    "video_render_plan": video_render_plan,
                    "lesson_audio_assets": lesson_audio_assets,
                    "explanation_video_urls": explanation_video_urls,
                    "aigc_visual_prompt": "A thematic visual for the current lesson...",
                },
                "pending_items": new_questions,
                "skip_content": skip_content,
                "practice_resume_index": max(0, min(practice_question_index, max(len(new_questions) - 1, 0))),
            },
        }
    finally:
        if conn:
            conn.close()
