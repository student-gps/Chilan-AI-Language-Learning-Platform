import copy
import json
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict

from psycopg2.extras import RealDictCursor

from database.connection import get_connection
from services.course_enrollment_service import ACTIVE_COURSE_STATUS
from services.study.access_service import assert_active_course_enrollment, assert_lesson_belongs_to_course


PRACTICE_METADATA_FIELDS = {
    "answer_mode",
    "answer_language",
    "answerLanguage",
    "audio_id",
    "audio_language",
    "line_ref",
    "prompt_language",
    "show_knowledge_card",
    "source_language",
    "source_ref",
    "source_section",
    "speech_eval_config",
    "speech_language",
    "support_language",
    "supportLanguage",
    "target_language",
    "targetLanguage",
    "tts_language",
}
PRACTICE_CONTEXT_FIELDS = {
    "audio_id",
    "audio_language",
    "line_ref",
    "pattern",
    "slot",
    "source_ref",
    "source_section",
    "support_language",
    "target_language",
}


def _practice_metadata(metadata: Any) -> Dict[str, Any]:
    if not isinstance(metadata, dict):
        return {}

    safe_metadata = {
        key: value
        for key, value in metadata.items()
        if key in PRACTICE_METADATA_FIELDS
    }
    context = metadata.get("context")
    if isinstance(context, dict):
        safe_context = {
            key: value
            for key, value in context.items()
            if key in PRACTICE_CONTEXT_FIELDS
        }
        if safe_context:
            safe_metadata["context"] = safe_context
    return safe_metadata


def serialize_practice_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Return only UI fields needed before an answer is evaluated."""
    return {
        "item_id": item.get("item_id"),
        "course_id": item.get("course_id"),
        "lesson_id": item.get("lesson_id"),
        "question_id": item.get("question_id"),
        "question_type": item.get("question_type"),
        "original_text": item.get("original_text"),
        "original_pinyin": item.get("original_pinyin") or "",
        "metadata": _practice_metadata(item.get("metadata")),
    }


def _study_capabilities(is_course_enrolled: bool) -> Dict[str, bool]:
    return {
        "can_view_lesson": True,
        "can_practice": bool(is_course_enrolled),
        "can_write_progress": bool(is_course_enrolled),
        "can_renew_lesson_media": bool(is_course_enrolled),
    }


BACKEND_DIR = Path(__file__).resolve().parents[2]
_LESSON_ROW_CACHE_MAX = 256
_LESSON_ROW_CACHE_TTL_SECONDS = 15 * 60
_LESSON_ROW_CACHE: OrderedDict[tuple[int, int], tuple[float, Dict[str, Any]]] = OrderedDict()


def _needs_teaching_materials(course_id: int) -> bool:
    # New Concept English renders grammar notes from teaching_materials.
    return int(course_id or 0) == 101


def _get_cached_lesson_row(course_id: int, lesson_id: int | None) -> Dict[str, Any] | None:
    if lesson_id is None:
        return None
    cache_key = (int(course_id), int(lesson_id))
    cached = _LESSON_ROW_CACHE.get(cache_key)
    if not cached:
        return None
    cached_at, lesson_row = cached
    if time.monotonic() - cached_at >= _LESSON_ROW_CACHE_TTL_SECONDS:
        _LESSON_ROW_CACHE.pop(cache_key, None)
        return None
    _LESSON_ROW_CACHE.move_to_end(cache_key)
    return copy.deepcopy(lesson_row)


def _put_cached_lesson_row(course_id: int, lesson_id: int | None, lesson_row: Dict[str, Any]) -> None:
    if lesson_id is None:
        return
    cache_key = (int(course_id), int(lesson_id))
    _LESSON_ROW_CACHE[cache_key] = (time.monotonic(), copy.deepcopy(lesson_row))
    _LESSON_ROW_CACHE.move_to_end(cache_key)
    while len(_LESSON_ROW_CACHE) > _LESSON_ROW_CACHE_MAX:
        _LESSON_ROW_CACHE.popitem(last=False)


def clear_lesson_row_cache(course_id: int | None = None, lesson_id: int | None = None) -> None:
    """Clear one lesson cache entry or all cached lessons after publishing."""
    if course_id is None or lesson_id is None:
        _LESSON_ROW_CACHE.clear()
        return
    _LESSON_ROW_CACHE.pop((int(course_id), int(lesson_id)), None)


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
    full_audio = assets.get("full_audio", {})
    if cos_media_storage and isinstance(full_audio, dict):
        object_key = (full_audio.get("object_key") or "").strip()
        if object_key:
            try:
                full_audio["audio_url"] = cos_media_storage.resolve_url(object_key)
            except Exception as e:
                print(f"⚠️ COS full audio 签名 URL 生成失败: {e}")

    for item in assets.get("items", []):
        object_key = (item.get("object_key") or "").strip()
        if not object_key or not cos_media_storage:
            continue
        try:
            item["audio_url"] = cos_media_storage.resolve_url(object_key)
        except Exception as e:
            print(f"⚠️ COS sentence audio 签名 URL 生成失败: line_ref={item.get('line_ref')} | {e}")

    for asset in [assets.get("full_audio"), *assets.get("items", [])]:
        if isinstance(asset, dict):
            asset.pop("object_key", None)
            asset.pop("local_audio_file", None)

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
    course_info: Dict[str, Any] | None = None,
    is_course_enrolled: bool = False,
    viewed_lesson: int = 0,
    practice_question_index: int = 0,
    can_practice: bool = False,
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
    if not can_practice:
        lesson_audio_assets = {
            **lesson_audio_assets,
            "full_audio": {},
            "items": [],
        }
    explanation_video_urls = _hydrate_explanation_video_urls(lesson_row.get("explanation_video_urls"), cos_media_storage)
    teaching_video = _normalize_teaching_video(
        video_plan.get("dramatization") if isinstance(video_plan.get("dramatization"), dict) else {}
    )
    questions = [serialize_practice_item(question) for question in (new_questions or [])]

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
            "course_info": course_info,
            "is_course_enrolled": is_course_enrolled,
            "capabilities": _study_capabilities(can_practice),
            "lesson_content": {
                "pipeline_id": lesson_metadata.get("pipeline_id") or lesson_metadata.get("course_slug"),
                "target_language": lesson_metadata.get("target_language") or (course_info or {}).get("target_language"),
                "source_language": lesson_metadata.get("source_language") or lesson_metadata.get("support_language"),
                "lesson_metadata": lesson_metadata,
                "course_content": course_content,
                "teaching_video": teaching_video,
                "teaching_materials": lesson_row.get("teaching_materials") or {},
                "video_render_plan": video_render_plan,
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
        assert_lesson_belongs_to_course(cur, course_id=course_id, lesson_id=lesson_id)
        assert_active_course_enrollment(cur, user_id=user_id, course_id=course_id)
        cur.execute(
            """
            WITH progress AS (
                SELECT COALESCE(practice_question_index, 0) AS practice_question_index
                FROM user_progress_of_lessons
                WHERE user_id::text = %s
                  AND course_id = %s
                LIMIT 1
            )
            SELECT
                COALESCE((SELECT practice_question_index FROM progress), 0) AS practice_question_index,
                item.item_id,
                item.course_id,
                item.question_id,
                item.question_type,
                item.original_text,
                item.original_pinyin,
                item.standard_answers,
                item.metadata,
                %s AS lesson_id
            FROM language_items item
            WHERE item.course_id = %s
              AND item.lesson_id = %s
            ORDER BY item.question_id ASC, item.item_id ASC
            """,
            (user_id, course_id, lesson_id, course_id, lesson_id),
        )
        rows = cur.fetchall()
        practice_question_index = (rows[0].get("practice_question_index") or 0) if rows else 0
        questions = [serialize_practice_item({
            key: value
            for key, value in row.items()
            if key != "practice_question_index"
        }) for row in rows]
        return {
            "pending_items": questions,
            "practice_resume_index": max(0, min(practice_question_index, max(len(questions) - 1, 0))),
        }
    finally:
        if conn:
            conn.close()


def _select_lesson_row(cur, *, course_id: int, lesson_id: int | None, last_lesson: int = 0):
    if lesson_id is None:
        cur.execute(
            """
            SELECT lesson_id
            FROM lessons
            WHERE course_id = %s
              AND lesson_id > %s
            ORDER BY lesson_id ASC
            LIMIT 1
            """,
            (course_id, last_lesson),
        )
        next_lesson = cur.fetchone()
        if not next_lesson:
            return None
        lesson_id = next_lesson["lesson_id"]

    cached = _get_cached_lesson_row(course_id, lesson_id)
    if cached:
        return cached

    teaching_materials_column = "teaching_materials" if _needs_teaching_materials(course_id) else "'{}'::jsonb AS teaching_materials"
    selected_columns = f"""lesson_id, title,
        lesson_metadata,
        course_content,
        {teaching_materials_column},
        '{{}}'::jsonb AS video_plan,
        jsonb_build_object('teaching_slide_deck', video_render_plan->'teaching_slide_deck') AS video_render_plan,
        lesson_audio_assets,
        '{{}}'::jsonb AS explanation_video_urls,
        '{{}}'::jsonb AS llm_usage
    """
    cur.execute(
        f"""
        SELECT {selected_columns}
        FROM lessons
        WHERE course_id = %s
          AND lesson_id = %s
        """,
        (course_id, lesson_id),
    )
    row = cur.fetchone()
    if row:
        _put_cached_lesson_row(course_id, row["lesson_id"], row)
    return row


def _load_study_context(
    cur,
    *,
    user_id: str,
    course_id: int,
) -> tuple[Dict[str, Any] | None, bool, Dict[str, Any]]:
    """Load static course data, active enrollment, and course-level progress together."""
    cur.execute(
        """
        SELECT
            c.course_id,
            c.name,
            c.category,
            c.target_language,
            c.source_language,
            EXISTS (
                SELECT 1
                FROM user_courses uc
                WHERE uc.user_id::text = %s
                  AND uc.course_id = c.course_id
                  AND uc.status = %s
            ) AS is_course_enrolled,
            COALESCE(lp.last_completed_lesson_id, 0) AS last_completed_lesson_id,
            COALESCE(lp.viewed_lesson_id, 0) AS viewed_lesson_id,
            COALESCE(lp.practice_question_index, 0) AS practice_question_index
        FROM courses c
        LEFT JOIN user_progress_of_lessons lp
          ON lp.course_id = c.course_id
         AND lp.user_id::text = %s
        WHERE c.course_id = %s
        """,
        (user_id, ACTIVE_COURSE_STATUS, user_id, course_id),
    )
    row = cur.fetchone()
    if not row:
        return None, False, {
            "last_completed_lesson_id": 0,
            "viewed_lesson_id": 0,
            "practice_question_index": 0,
        }

    return {
        "id": row.get("course_id"),
        "name": row.get("name"),
        "category": row.get("category"),
        "target_language": row.get("target_language"),
        "source_language": row.get("source_language"),
    }, bool(row.get("is_course_enrolled")), {
        "last_completed_lesson_id": row.get("last_completed_lesson_id") or 0,
        "viewed_lesson_id": row.get("viewed_lesson_id") or 0,
        "practice_question_index": row.get("practice_question_index") or 0,
    }


def init_study_flow(
    user_id: str,
    course_id: int = 1,
    cos_media_storage=None,
    lesson_id: int = None,
    prefer_local_content: bool = False,
    defer_practice_items: bool = False,
):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        course_info, is_course_enrolled, progress = _load_study_context(
            cur,
            user_id=user_id,
            course_id=course_id,
        )
        can_practice = is_course_enrolled
        if lesson_id is not None:
            assert_lesson_belongs_to_course(cur, course_id=course_id, lesson_id=lesson_id)
        if not is_course_enrolled and (lesson_id is None or not prefer_local_content):
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
                ORDER BY p.next_review ASC, q.item_id ASC
                LIMIT 20;
                """,
                (user_id, course_id),
            )
            due_questions = cur.fetchall()
            if due_questions:
                return {
                    "mode": "review",
                    "data": {
                        "pending_items": [serialize_practice_item(question) for question in due_questions],
                        "capabilities": _study_capabilities(True),
                    },
                }

        last_lesson = progress.get("last_completed_lesson_id") or 0
        viewed_lesson = progress.get("viewed_lesson_id") or 0
        practice_question_index = progress.get("practice_question_index") or 0

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

        practice_deferred = bool(defer_practice_items or prefer_local_content or not can_practice)
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
                ORDER BY question_id ASC, item_id ASC
                """,
                (next_lesson_id, course_id, next_lesson_id),
            )
            new_questions = cur.fetchall()
        skip_content = viewed_lesson == next_lesson_id
    finally:
        if conn:
            conn.close()

    return _build_teaching_response(
        lesson_row,
        course_id=course_id,
        course_info=course_info,
        is_course_enrolled=is_course_enrolled,
        viewed_lesson=viewed_lesson,
        practice_question_index=practice_question_index,
        can_practice=can_practice,
        new_questions=new_questions,
        practice_deferred=practice_deferred,
        cos_media_storage=cos_media_storage,
    )
