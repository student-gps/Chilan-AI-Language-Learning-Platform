import os
import sys
import time  # 🌟 引入 time 用于手动记录 Tier 1 耗时
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import edge_tts
from psycopg2.extras import RealDictCursor

# 🌟 动态引入路径
sys.path.append(str(Path(__file__).resolve().parent.parent))
from database.connection import get_connection

# 🌟 引入监控工具和原有服务
from services.utils.monitor import PerformanceMonitor
from services.llm.base_engine import LLMEngine
from services.llm.tools import LanguageTools
from services.speech import ASRService
from services.study.scheduler import FSRSScheduler
from services.study.evaluator_service import StudyEvaluator
from services.study.lesson_progress_service import (
    complete_lesson as complete_lesson_service,
    mark_lesson_content_viewed as mark_lesson_content_viewed_service,
    save_practice_progress as save_practice_progress_service,
)
from services.study.init_flow_service import init_study_flow as init_study_flow_service
from services.storage.media_storage import get_media_storage
from config.env import get_env

router = APIRouter(tags=["Study Flow"])

# --- ⚙️ 初始化全局单例 ---
API_KEY = get_env("LLM_GEMINI_API_KEY")
engine = LLMEngine(api_key=API_KEY)
llm_tools = LanguageTools(engine=engine)
scheduler = FSRSScheduler()
evaluator_service = StudyEvaluator(tools=llm_tools)
asr_service = ASRService()
cos_media_storage = get_media_storage(optional=True)

# --- 📦 数据模型 ---
class EvaluateRequest(BaseModel):
    user_id: str
    lesson_id: int
    question_id: int
    question_type: str
    original_text: str
    original_pinyin: str = ""
    standard_answers: List[str]
    user_answer: str = ""
    input_mode: str = "text"
    asr_text: str = ""
    audio_meta: Dict[str, Any] = Field(default_factory=dict)
    forfeit: bool = False

class ContentViewedRequest(BaseModel):
    user_id: str
    course_id: int = 1
    lesson_id: int

class CompleteLessonRequest(BaseModel):
    user_id: str
    course_id: int
    lesson_id: int

class PracticeProgressRequest(BaseModel):
    user_id: str
    course_id: int
    lesson_id: int
    current_index: int


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
        "scenes": [scene for scene in scenes if isinstance(scene, dict)]
    }


def _normalize_video_render_plan(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {"explanation": {}}

    explanation = payload.get("explanation")
    if not isinstance(explanation, dict):
        explanation = {}

    return {"explanation": explanation}


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


def _hydrate_explanation_video_urls(payload: Any) -> Dict[str, Any]:
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
            "items": []
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
        "items": [item for item in items if isinstance(item, dict)]
    }


def _hydrate_lesson_audio_urls(payload: Dict[str, Any]) -> Dict[str, Any]:
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
                print(f"⚠️ R2 full audio 签名 URL 生成失败: {e}")

    for item in assets.get("items", []):
        object_key = (item.get("object_key") or "").strip()
        if not object_key:
            continue
        try:
            item["audio_url"] = cos_media_storage.resolve_url(object_key)
        except Exception as e:
            print(f"⚠️ R2 sentence audio 签名 URL 生成失败: line_ref={item.get('line_ref')} | {e}")

    return assets


def _to_optional_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_optional_int(value: Any) -> Optional[int]:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def ensure_lesson_progress_columns(cur):
    cur.execute("""
        ALTER TABLE user_progress_of_lessons
        ADD COLUMN IF NOT EXISTS practice_question_index INTEGER DEFAULT 0;
    """)
    cur.execute("""
        ALTER TABLE user_progress_of_lessons
        ADD COLUMN IF NOT EXISTS practice_question_updated_at TIMESTAMP;
    """)


def ensure_vocabulary_knowledge_table(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vocabulary_knowledge (
            course_id INTEGER NOT NULL,
            lesson_id INTEGER NOT NULL,
            word TEXT NOT NULL,
            pinyin TEXT,
            part_of_speech TEXT,
            definition TEXT NOT NULL,
            example JSONB DEFAULT '{}'::jsonb,
            PRIMARY KEY (course_id, lesson_id, word, definition)
        );
    """)

# ==========================================
# 接口 1: 初始化学习流
# ==========================================
# ==========================================
# 接口 1: 初始化学习流 (完整版)
# ==========================================
@router.get("/study/init")
async def init_study_flow(user_id: str, course_id: int = 1, lesson_id: int = None):
    try:
        return init_study_flow_service(
            user_id=user_id,
            course_id=course_id,
            cos_media_storage=cos_media_storage,
            lesson_id=lesson_id,
        )
    except Exception as e:
        print(f"❌ Init Flow Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="加载学习流失败，请检查后端日志")
        
# ==========================================
# 接口 2: 智能判卷与记忆更新
# ==========================================
@router.post("/study/speech/transcribe")
async def transcribe_speech(
    audio: UploadFile = File(...),
    language: str = Form("zh"),
    prompt: str = Form(""),
):
    try:
        if not audio:
            raise HTTPException(status_code=400, detail="Audio file is required.")

        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Audio file is empty.")

        if len(audio_bytes) > asr_service.max_audio_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Audio file too large. Max {asr_service.max_audio_bytes} bytes.",
            )

        result = asr_service.transcribe(
            audio_bytes=audio_bytes,
            filename=audio.filename or "speech.webm",
            content_type=audio.content_type or "",
            language=(language or "").strip() or None,
            prompt=(prompt or "").strip() or None,
        )
        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        print(f"ASR Error: {e}")
        raise HTTPException(status_code=500, detail="ASR service failed.")


@router.post("/study/evaluate")
async def evaluate_answer(req: EvaluateRequest):
    pm = PerformanceMonitor()
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        input_mode = (req.input_mode or "text").strip().lower()
        if input_mode not in {"text", "speech"}:
            raise HTTPException(status_code=400, detail="Invalid input_mode. Use 'text' or 'speech'.")

        normalized_answers = [str(ans).strip() for ans in (req.standard_answers or []) if str(ans).strip()]
        if not normalized_answers:
            raise HTTPException(status_code=400, detail="standard_answers is empty.")

        if req.forfeit:
            effective_answer = ""
        elif input_mode == "speech":
            effective_answer = (req.asr_text or "").strip()
            if not effective_answer:
                raise HTTPException(status_code=400, detail="asr_text is required when input_mode is 'speech'.")
        else:
            effective_answer = (req.user_answer or "").strip()
            if not effective_answer:
                raise HTTPException(status_code=400, detail="user_answer is empty.")

        audio_meta = req.audio_meta or {}
        asr_text_for_log = effective_answer if input_mode == "speech" else None
        asr_confidence = _to_optional_float(audio_meta.get("confidence")) if input_mode == "speech" else None
        audio_duration_ms = _to_optional_int(audio_meta.get("duration_ms")) if input_mode == "speech" else None
        vector_score = None

        cur.execute("""
            SELECT q.item_id as item_pk, q.metadata as item_metadata, p.stability, p.difficulty, p.recent_history, p.state
            FROM language_items q 
            LEFT JOIN user_progress_of_language_items p 
                   ON q.question_id = p.question_id AND p.user_id::text = %s 
            WHERE q.question_id = %s;
        """, (req.user_id, req.question_id))
        
        base_info = cur.fetchone()
        if not base_info:
            raise HTTPException(status_code=404, detail="题目不存在")

        item_pk = base_info['item_pk']
        item_metadata = base_info.get('item_metadata') if isinstance(base_info.get('item_metadata'), dict) else {}
        stability = base_info['stability']
        difficulty = base_info['difficulty']
        history = base_info['recent_history']
        speech_eval_config = evaluator_service.get_speech_eval_config(item_metadata.get("speech_eval_config"))
        
        # 定义状态：如果没有历史记录说明是新题(0)，有记录说明在复习(1)
        current_state = 0 if not history else 1

        # ⚡ Forfeit: 用户选择不会，跳过评判直接记 level=1
        if req.forfeit:
            res = {"level": 1, "isCorrect": False, "message": "", "judgedBy": "Forfeit", "forfeited": True}
            new_s, new_d, next_r = scheduler.calc_next_review(stability or 0.5, difficulty or 5.0, 1)
            new_hist = ((history or []) + [1])[-5:]
            cur.execute("""
                INSERT INTO user_progress_of_language_items
                    (user_id, question_id, item_id, stability, difficulty, state, recent_history, is_mastered, last_review, next_review)
                VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s)
                ON CONFLICT (user_id, question_id)
                DO UPDATE SET
                    item_id = EXCLUDED.item_id, stability = EXCLUDED.stability,
                    difficulty = EXCLUDED.difficulty, state = EXCLUDED.state,
                    recent_history = EXCLUDED.recent_history, is_mastered = EXCLUDED.is_mastered,
                    last_review = CURRENT_TIMESTAMP, next_review = EXCLUDED.next_review;
            """, (req.user_id, req.question_id, item_pk, new_s, new_d, current_state, new_hist,
                  scheduler.check_mastery(new_hist), next_r))
            cur.execute("""
                INSERT INTO review_logs
                    (user_id, question_id, item_id, rating, state, review_time, stability, difficulty,
                     input_mode, asr_text, asr_confidence, vector_score, audio_duration_ms)
                VALUES (%s::uuid, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s, %s, %s, %s, %s)
            """, (req.user_id, req.question_id, item_pk, 1, current_state, new_s, new_d,
                  "forfeit", None, None, None, None))
            conn.commit()
            return {"status": "success", "data": {**res, "inputMode": "forfeit", "recognizedText": None, "vectorScore": None}}

        if input_mode == "speech":
            retry_res = evaluator_service.check_speech_readiness(
                asr_text=effective_answer,
                asr_confidence=asr_confidence,
                speech_eval_config=speech_eval_config,
            )
            if retry_res:
                response_payload = {
                    **retry_res,
                    "inputMode": input_mode,
                    "recognizedText": asr_text_for_log,
                    "vectorScore": None,
                }
                return {"status": "success", "data": response_payload}

        # 🛡️ Tier 1: 极速正则匹配
        t1_start = time.perf_counter()
        is_exact = evaluator_service.check_exact(effective_answer, normalized_answers)
        pm.record("Tier 1 (Regex)", time.perf_counter() - t1_start)

        if is_exact:
            vector_score = 1.0
            res = {
                "level": 4, 
                "isCorrect": True, 
                "message": "Perfect match! Your expression is very natural.", "judgedBy": "Regex"
            }
            pm.report(vector_score=vector_score)
        else:
            # 🚄 Tier 2 & 3: 向量 + LLM
            try:
                user_vec = await llm_tools.get_embedding(effective_answer, pm=pm)

                cur.execute(
                    "SELECT 1 - (primary_embedding <=> %s::vector) AS sim_score FROM language_items WHERE item_id = %s",
                    (user_vec, item_pk)
                )
                sim_row = cur.fetchone()
                sim_score = sim_row['sim_score'] if sim_row else 0.0
                vector_score = sim_score

                res = await evaluator_service.process_judge(
                    q_type=req.question_type,
                    user_ans=effective_answer,
                    origin=req.original_text,
                    std_answers=normalized_answers,
                    vector_score=sim_score,
                    pm=pm,
                    input_mode=input_mode,
                    asr_confidence=asr_confidence,
                    speech_eval_config=speech_eval_config,
                )
            except Exception as judge_error:
                print(f"⚠️ Evaluate degraded: {judge_error}")
                response_payload = {
                    "level": 1,
                    "isCorrect": False,
                    "message": "Evaluation service is temporarily unavailable. Please retry in a moment.",
                    "judgedBy": "Service Degraded",
                    "shouldRetry": True,
                    "inputMode": input_mode,
                    "recognizedText": asr_text_for_log if input_mode == "speech" else None,
                    "vectorScore": None,
                }
                return {"status": "success", "data": response_payload}

        # 🧠 FSRS 状态更新
        new_s, new_d, next_r = scheduler.calc_next_review(stability or 0.5, difficulty or 5.0, res["level"])
        new_hist = ((history or []) + [res["level"]])[-5:]

        # --- 🌟 数据库更新事务 ---
        
        # 1. 更新进度表 user_progress_of_language_items
        cur.execute("""
            INSERT INTO user_progress_of_language_items 
                (user_id, question_id, item_id, stability, difficulty, state, recent_history, is_mastered, last_review, next_review) 
            VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s) 
            ON CONFLICT (user_id, question_id) 
            DO UPDATE SET 
                item_id = EXCLUDED.item_id,
                stability = EXCLUDED.stability, 
                difficulty = EXCLUDED.difficulty, 
                state = EXCLUDED.state,
                recent_history = EXCLUDED.recent_history, 
                is_mastered = EXCLUDED.is_mastered, 
                last_review = CURRENT_TIMESTAMP, 
                next_review = EXCLUDED.next_review;
        """, (
            req.user_id, req.question_id, item_pk, 
            new_s, new_d, current_state, new_hist, 
            scheduler.check_mastery(new_hist), next_r
        ))

        # 2. 记录流水表 review_logs
        cur.execute("""
            INSERT INTO review_logs 
                (
                    user_id, question_id, item_id, rating, state, review_time, stability, difficulty,
                    input_mode, asr_text, asr_confidence, vector_score, audio_duration_ms
                )
            VALUES (%s::uuid, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s, %s, %s, %s, %s)
        """, (
            req.user_id, req.question_id, item_pk, 
            res["level"], current_state, new_s, new_d,
            input_mode, asr_text_for_log, asr_confidence, vector_score, audio_duration_ms
        ))
        
        conn.commit()
        response_payload = {
            **res,
            "inputMode": input_mode,
            "recognizedText": asr_text_for_log if input_mode == "speech" else None,
            "vectorScore": vector_score,
        }
        return {"status": "success", "data": response_payload}

    except HTTPException:
        raise
    except Exception as e:
        if conn: conn.rollback()
        print(f"❌ Evaluate Error: {e}")
        raise HTTPException(status_code=500, detail="Evaluation failed. Please retry later.")
    finally:
        if conn: conn.close()

# ==========================================
# 接口 3: 标记讲义已看
# ==========================================
@router.post("/study/content_viewed")
async def mark_lesson_content_viewed(req: ContentViewedRequest):
    try:
        return mark_lesson_content_viewed_service(
            user_id=req.user_id,
            course_id=req.course_id,
            lesson_id=req.lesson_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 接口 4: 同步练习进度（账号级断点续练）
# ==========================================
@router.post("/study/practice_progress")
async def save_practice_progress(req: PracticeProgressRequest):
    try:
        return save_practice_progress_service(
            user_id=req.user_id,
            course_id=req.course_id,
            lesson_id=req.lesson_id,
            current_index=req.current_index,
        )
    except Exception as e:
        print(f"❌ Save Practice Progress Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/study/knowledge")
async def get_knowledge_details(item_id: int):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        ensure_vocabulary_knowledge_table(cur)
        conn.commit()

        cur.execute("""
            SELECT item_id, course_id, lesson_id, question_type, original_text, standard_answers, metadata
            FROM language_items
            WHERE item_id = %s
        """, (item_id,))
        item = cur.fetchone()
        if not item:
            raise HTTPException(status_code=404, detail="题目不存在")

        metadata = item.get("metadata") or {}
        knowledge_meta = metadata.get("knowledge") or {}
        question_type = item.get("question_type")
        standard_answers = item.get("standard_answers") or []

        if question_type == "CN_TO_EN":
            word = (item.get("original_text") or "").strip()
        else:
            word = (standard_answers[0] if standard_answers else "").strip()

        if not word:
            return {"status": "success", "data": None}

        current_definition = (knowledge_meta.get("definition") or "").strip()

        cur.execute("""
            SELECT course_id, lesson_id, word, pinyin, part_of_speech, definition, example
            FROM vocabulary_knowledge
            WHERE word = %s
            ORDER BY
                CASE WHEN lesson_id = %s THEN 0 ELSE 1 END,
                lesson_id ASC
        """, (word, item.get("lesson_id")))
        rows = cur.fetchall()
        if not rows:
            return {"status": "success", "data": None}

        current_entry = None
        other_entries = []

        for row in rows:
            row_definition = (row.get("definition") or "").strip()
            candidate = {
                "word": row.get("word"),
                "pinyin": row.get("pinyin"),
                "part_of_speech": row.get("part_of_speech"),
                "definition": row_definition,
                "example_sentence": row.get("example") or {},
                "lesson_id": row.get("lesson_id")
            }

            if current_entry is None and current_definition and row_definition.lower() == current_definition.lower():
                current_entry = candidate
            else:
                other_entries.append(candidate)

        if current_entry is None:
            current_entry = {
                "word": knowledge_meta.get("word") or word,
                "pinyin": knowledge_meta.get("pinyin") or rows[0].get("pinyin"),
                "part_of_speech": knowledge_meta.get("part_of_speech") or rows[0].get("part_of_speech"),
                "definition": knowledge_meta.get("definition") or rows[0].get("definition"),
                "example_sentence": knowledge_meta.get("example_sentence") or rows[0].get("example") or {},
                "lesson_id": item.get("lesson_id")
            }
            other_entries = [
                entry for entry in other_entries
                if (entry.get("definition") or "").strip().lower() != (current_entry.get("definition") or "").strip().lower()
            ]

        return {
            "status": "success",
            "data": {
                "word": current_entry.get("word") or word,
                "pinyin": current_entry.get("pinyin") or knowledge_meta.get("pinyin") or "",
                "current_sense": current_entry,
                "other_senses": other_entries
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Knowledge Detail Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

# ==========================================
# 接口 5: TTS 接口
# ==========================================
@router.get("/study/tts")
async def generate_tts(text: str):
    voice = get_env("TTS_EDGE_VOICE", default="zh-CN-XiaoxiaoNeural")
    rate = get_env("TTS_EDGE_RATE", default="-12%")
    communicate = edge_tts.Communicate(text, voice, rate=rate) 
    async def audio_stream():
        async for chunk in communicate.stream():
            if chunk["type"] == "audio": yield chunk["data"]
    return StreamingResponse(audio_stream(), media_type="audio/mpeg")

# ==========================================
# 接口 6: 完成课程，推进总体进度
# ==========================================
@router.get("/study/lesson_preview")
async def lesson_preview(course_id: int, lesson_id: int):
    """Dev-only: fetch a specific lesson's render plan by lesson_id."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT title, video_render_plan FROM lessons WHERE course_id = %s AND lesson_id = %s",
            (course_id, lesson_id),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Lesson {lesson_id} not found.")
        title = row["title"]
        video_render_plan = _normalize_video_render_plan(row.get("video_render_plan"))
        return {
            "lesson_id": lesson_id,
            "course_id": course_id,
            "title": title,
            "video_render_plan": video_render_plan,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()


@router.post("/study/complete_lesson")
async def complete_lesson(req: CompleteLessonRequest):
    try:
        return complete_lesson_service(
            user_id=req.user_id,
            course_id=req.course_id,
            lesson_id=req.lesson_id,
        )
    except Exception as e:
        print(f"❌ Complete Lesson Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
