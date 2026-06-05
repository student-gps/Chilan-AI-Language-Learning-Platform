import json
from pathlib import Path
from typing import Any, Dict

from psycopg2.extras import RealDictCursor

from database.connection import get_connection
from services.course_enrollment_service import ACTIVE_COURSE_STATUS


BACKEND_DIR = Path(__file__).resolve().parents[2]
_LESSON_ROW_CACHE: dict[tuple[int, int], Dict[str, Any]] = {}


def _cacheable_course(course_id: int) -> bool:
    return int(course_id or 0) in {303}


def _get_cached_lesson_row(course_id: int, lesson_id: int | None) -> Dict[str, Any] | None:
    if lesson_id is None or not _cacheable_course(course_id):
        return None
    cached = _LESSON_ROW_CACHE.get((int(course_id), int(lesson_id)))
    return dict(cached) if cached else None


def _put_cached_lesson_row(course_id: int, lesson_id: int | None, lesson_row: Dict[str, Any]) -> None:
    if lesson_id is None or not _cacheable_course(course_id):
        return
    _LESSON_ROW_CACHE[(int(course_id), int(lesson_id))] = dict(lesson_row)


def _normalize_video_render_plan(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {"explanation": {}}

    explanation = payload.get("explanation")
    if not isinstance(explanation, dict):
        explanation = {}
    teaching_slide_deck = payload.get("teaching_slide_deck")
    if not isinstance(teaching_slide_deck, dict):
        teaching_slide_deck = None

    normalized = {"explanation": explanation}
    if teaching_slide_deck:
        normalized["teaching_slide_deck"] = teaching_slide_deck
    return normalized


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


def _load_local_mnn_lesson_row(course_id: int, lesson_id: int | None, lang: str = "zh") -> Dict[str, Any] | None:
    """Dev preview fast path for MNN lessons; avoids pulling large JSONB from remote DB."""
    if course_id != 303 or lesson_id is None:
        return None

    lesson_slug = f"lesson{int(lesson_id):03d}"
    artifact_root = BACKEND_DIR / "content_builder" / "ja" / "minna_no_nihongo" / "artifacts"
    candidates = [
        artifact_root / "synced_json" / lang / f"{lesson_slug}_data.json",
        artifact_root / "output_json" / lang / f"{lesson_slug}_data.json",
    ]
    json_path = next((path for path in candidates if path.exists()), None)
    if json_path is None:
        return None

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"⚠️ 本地 MNN 预览 JSON 读取失败: {json_path} | {exc}")
        return None

    metadata = data.get("lesson_metadata") if isinstance(data.get("lesson_metadata"), dict) else {}
    metadata = {
        **metadata,
        "course_id": course_id,
        "lesson_id": int(lesson_id),
        "pipeline_id": data.get("pipeline_id") or metadata.get("pipeline_id"),
    }
    return {
        "lesson_id": int(lesson_id),
        "title": metadata.get("title") or data.get("title") or f"第{int(lesson_id)}課",
        "lesson_metadata": metadata,
        "course_content": data.get("course_content") if isinstance(data.get("course_content"), dict) else {},
        "teaching_materials": data.get("teaching_materials") if isinstance(data.get("teaching_materials"), dict) else {},
        "video_plan": data.get("video_plan") if isinstance(data.get("video_plan"), dict) else {},
        "video_render_plan": data.get("video_render_plan") if isinstance(data.get("video_render_plan"), dict) else {},
        "lesson_audio_assets": data.get("lesson_audio_assets") if isinstance(data.get("lesson_audio_assets"), dict) else {},
        "explanation_video_urls": data.get("explanation_video_urls") if isinstance(data.get("explanation_video_urls"), dict) else {},
        "llm_usage": data.get("llm_usage") if isinstance(data.get("llm_usage"), dict) else {},
    }


def _build_teaching_response(
    lesson_row: Dict[str, Any],
    *,
    course_id: int,
    viewed_lesson: int = 0,
    practice_question_index: int = 0,
    new_questions: list | None = None,
    practice_deferred: bool = False,
    cos_media_storage=None,
) -> Dict[str, Any]:
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
    questions = new_questions or []

    lesson_metadata = {
        "course_id": course_id,
        "lesson_id": next_lesson_id,
        "title": lesson_metadata.get("title") or lesson_row["title"],
        "content_type": lesson_metadata.get("content_type", "dialogue"),
        **{k: v for k, v in lesson_metadata.items() if k not in {"course_id", "lesson_id", "title", "content_type"}},
    }

    return {
        "mode": "teaching",
        "data": {
            "lesson_content": {
                "pipeline_id": lesson_metadata.get("pipeline_id") or lesson_metadata.get("course_slug"),
                "target_language": lesson_metadata.get("target_language"),
                "source_language": lesson_metadata.get("source_language") or lesson_metadata.get("support_language"),
                "lesson_metadata": lesson_metadata,
                "course_content": course_content,
                "teaching_video": teaching_video,
                "video_render_plan": video_render_plan,
                "teaching_slide_deck": video_render_plan.get("teaching_slide_deck"),
                "lesson_audio_assets": lesson_audio_assets,
                "explanation_video_urls": explanation_video_urls,
                "aigc_visual_prompt": "A thematic visual for the current lesson...",
            },
            "pending_items": questions,
            "practice_deferred": practice_deferred,
            "skip_content": viewed_lesson == next_lesson_id,
            "practice_resume_index": max(0, min(practice_question_index, max(len(questions) - 1, 0))),
        },
    }


def load_lesson_practice_items(user_id: str, course_id: int, lesson_id: int) -> Dict[str, Any]:
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT COALESCE(practice_question_index, 0) AS practice_question_index
            FROM user_progress_of_lessons
            WHERE user_id::text = %s AND course_id = %s
            """,
            (user_id, course_id),
        )
        progress = cur.fetchone() or {}
        practice_question_index = progress.get("practice_question_index") or 0

        cur.execute(
            """
            SELECT
                item_id,
                course_id,
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
            (lesson_id, course_id, lesson_id),
        )
        questions = cur.fetchall()
        return {
            "pending_items": questions,
            "practice_resume_index": max(0, min(practice_question_index, max(len(questions) - 1, 0))),
        }
    finally:
        if conn:
            conn.close()


def _select_lesson_row(cur, *, course_id: int, lesson_id: int | None, last_lesson: int = 0):
    if _cacheable_course(course_id):
        selected_columns = """
            lesson_id,
            title,
            lesson_metadata,
            course_content,
            '{}'::jsonb AS teaching_materials,
            '{}'::jsonb AS video_plan,
            jsonb_build_object('teaching_slide_deck', video_render_plan->'teaching_slide_deck') AS video_render_plan,
            lesson_audio_assets,
            explanation_video_urls,
            '{}'::jsonb AS llm_usage
        """
    else:
        selected_columns = """
            lesson_id,
            title,
            lesson_metadata,
            course_content,
            teaching_materials,
            video_plan,
            video_render_plan,
            lesson_audio_assets,
            explanation_video_urls,
            llm_usage
        """

    if lesson_id is not None:
        cur.execute(
            f"""
            SELECT {selected_columns}
            FROM lessons
            WHERE course_id = %s AND lesson_id = %s
            """,
            (course_id, lesson_id),
        )
    else:
        cur.execute(
            f"""
            SELECT {selected_columns}
            FROM lessons
            WHERE course_id = %s AND lesson_id > %s
            ORDER BY lesson_id ASC
            LIMIT 1
            """,
            (course_id, last_lesson),
        )
    row = cur.fetchone()
    if row and _cacheable_course(course_id):
        _put_cached_lesson_row(course_id, row["lesson_id"], row)
    return row


def init_study_flow(
    user_id: str,
    course_id: int = 1,
    cos_media_storage=None,
    lesson_id: int = None,
    prefer_local_content: bool = False,
    defer_practice_items: bool = False,
):
    if prefer_local_content and lesson_id is not None:
        lesson_row = _load_local_mnn_lesson_row(course_id, lesson_id)
        if lesson_row:
            return _build_teaching_response(
                lesson_row,
                course_id=course_id,
                viewed_lesson=0,
                practice_question_index=0,
                new_questions=[],
                practice_deferred=True,
                cos_media_storage=cos_media_storage,
            )

    if lesson_id is not None and defer_practice_items:
        lesson_row = _get_cached_lesson_row(course_id, lesson_id)
        if lesson_row:
            return _build_teaching_response(
                lesson_row,
                course_id=course_id,
                viewed_lesson=0,
                practice_question_index=0,
                new_questions=[],
                practice_deferred=True,
                cos_media_storage=cos_media_storage,
            )

    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        if lesson_id is None:
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
            if not cur.fetchone():
                return {
                    "mode": "not_enrolled",
                    "message": "请先将课程添加到学习列表。",
                }

        # 指定 lesson_id 时跳过 FSRS 复习队列，直接加载该课
        if lesson_id is None:
            cur.execute(
                """
                SELECT
                    q.item_id,
                    q.course_id,
                    q.lesson_id,
                    q.question_id,
                    q.question_type,
                    q.original_text,
                    q.original_pinyin,
                    q.standard_answers,
                    q.metadata
                FROM language_items q
                JOIN user_progress_of_language_items p ON q.item_id = p.item_id
                WHERE p.user_id::text = %s
                  AND q.course_id = %s
                  AND p.next_review <= CURRENT_TIMESTAMP
                ORDER BY p.next_review ASC
                LIMIT 20;
                """,
                (user_id, course_id),
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

        lesson_row = _load_local_mnn_lesson_row(course_id, lesson_id) if prefer_local_content else None

        if lesson_id is not None and lesson_row is None:
            lesson_row = _select_lesson_row(cur, course_id=course_id, lesson_id=lesson_id)
        else:
            lesson_row = lesson_row or _select_lesson_row(
                cur,
                course_id=course_id,
                lesson_id=None,
                last_lesson=last_lesson,
            )
        if not lesson_row:
            return {"mode": "completed", "message": "恭喜！你已完成本课程的所有内容。"}

        next_lesson_id = lesson_row["lesson_id"]

        practice_deferred = bool(defer_practice_items or prefer_local_content)
        if practice_deferred:
            new_questions = []
        else:
            cur.execute(
                """
                SELECT
                    item_id,
                    course_id,
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

        return _build_teaching_response(
            lesson_row,
            course_id=course_id,
            viewed_lesson=viewed_lesson,
            practice_question_index=practice_question_index,
            new_questions=new_questions,
            practice_deferred=practice_deferred,
            cos_media_storage=cos_media_storage,
        )
    finally:
        if conn:
            conn.close()
