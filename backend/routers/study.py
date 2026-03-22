import os
import sys
import time  # 🌟 引入 time 用于手动记录 Tier 1 耗时
from pathlib import Path
from typing import List
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import edge_tts
from psycopg2.extras import RealDictCursor

# 🌟 动态引入路径
sys.path.append(str(Path(__file__).resolve().parent.parent))
from database.connection import get_connection

# 🌟 引入监控工具和原有服务
from services.utils.monitor import PerformanceMonitor
from services.llm.base_engine import LLMEngine
from services.llm.tools import LanguageTools
from services.study.scheduler import FSRSScheduler
from services.study.evaluator_service import StudyEvaluator

router = APIRouter(tags=["Study Flow"])

# --- ⚙️ 初始化全局单例 ---
API_KEY = os.getenv("GEMINI_API_KEY")
engine = LLMEngine(api_key=API_KEY)
llm_tools = LanguageTools(engine=engine)
scheduler = FSRSScheduler()
evaluator_service = StudyEvaluator(tools=llm_tools)

# --- 📦 数据模型 ---
class EvaluateRequest(BaseModel):
    user_id: str
    lesson_id: int
    question_id: int
    question_type: str
    original_text: str
    standard_answers: List[str]
    user_answer: str

class ContentViewedRequest(BaseModel):
    user_id: str
    course_id: int = 1
    lesson_id: int

class CompleteLessonRequest(BaseModel):
    user_id: str
    course_id: int
    lesson_id: int

# ==========================================
# 接口 1: 初始化学习流
# ==========================================
@router.get("/study/init")
async def init_study_flow(user_id: str, course_id: int = 1):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # 1. 复习流查询
        cur.execute("""
            SELECT q.item_id, q.question_id, q.question_type, q.original_text, q.standard_answers
            FROM language_items q
            JOIN user_progress_of_language_items p ON q.item_id = p.item_id
            WHERE p.user_id::text = %s AND p.next_review <= CURRENT_TIMESTAMP
            ORDER BY p.next_review ASC LIMIT 20;
        """, (user_id,))
        
        due_questions = cur.fetchall()

        if due_questions:
            return {"mode": "review", "data": {"pending_items": due_questions}}

        # 2. 查出进度和书签
        cur.execute("""
            SELECT last_completed_lesson_id, viewed_lesson_id 
            FROM user_progress_of_lessons 
            WHERE user_id::text = %s AND course_id = %s
        """, (user_id, course_id))
        
        progress = cur.fetchone()
        
        # 🌟 核心修改：如果是新用户，进度从 0 开始算
        if progress:
            last_lesson = progress.get('last_completed_lesson_id') or 0
            viewed_lesson = progress.get('viewed_lesson_id') or 0
        else:
            last_lesson = 0
            viewed_lesson = 0
            
        # 🌟 核心修改：让数据库直接找排在后面的第一节课 (完美支持 102 跳到 201)
        cur.execute("""
            SELECT lesson_id, title, structured_content 
            FROM lessons 
            WHERE course_id = %s AND lesson_id > %s 
            ORDER BY lesson_id ASC 
            LIMIT 1
        """, (course_id, last_lesson))
        
        lesson_row = cur.fetchone()

        if not lesson_row:
            return {"mode": "completed", "message": "所有课程已完成！"}

        # 真实获取到的下一节课的 ID
        next_lesson = lesson_row['lesson_id']

        # 查询新课题目
        cur.execute("""
            SELECT item_id, question_id, question_type, original_text, standard_answers, %s as lesson_id
            FROM language_items WHERE course_id = %s AND lesson_id = %s
        """, (next_lesson, course_id, next_lesson))
        new_questions = cur.fetchall()

        # 判断这节课的书签是否已经被打过了
        skip_content = (viewed_lesson == next_lesson)

        return {
            "mode": "teaching",
            "data": {
                "lesson_content": {
                    "lesson_metadata": {"course_id": course_id, "lesson_id": next_lesson, "title": lesson_row['title']},
                    "course_content": lesson_row['structured_content'],
                    "aigc_visual_prompt": "A cinematic scene in Paris..." 
                },
                "pending_items": new_questions,
                "skip_content": skip_content  
            }
        }
    except Exception as e:
        print(f"❌ Init Flow Error: {e}")
        raise HTTPException(status_code=500, detail="加载学习流失败")
    finally:
        if conn: conn.close()
        
# ==========================================
# 接口 2: 智能判卷与记忆更新
# ==========================================
@router.post("/study/evaluate")
async def evaluate_answer(req: EvaluateRequest):
    pm = PerformanceMonitor()
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. 统一查询：获取题目的自增主键 (item_id) 和用户进度
        cur.execute("""
            SELECT q.item_id as item_pk, p.stability, p.difficulty, p.recent_history, p.state
            FROM language_items q 
            LEFT JOIN user_progress_of_language_items p 
                   ON q.question_id = p.question_id AND p.user_id::text = %s 
            WHERE q.question_id = %s;
        """, (req.user_id, req.question_id))
        
        base_info = cur.fetchone()
        if not base_info:
            raise HTTPException(status_code=404, detail="题目不存在")

        item_pk = base_info['item_pk']
        stability = base_info['stability']
        difficulty = base_info['difficulty']
        history = base_info['recent_history']
        
        # 定义状态：如果没有历史记录说明是新题(0)，有记录说明在复习(1)
        current_state = 0 if not history else 1

        # 🛡️ Tier 1: 极速正则匹配
        t1_start = time.perf_counter()
        is_exact = evaluator_service.check_exact(req.user_answer, req.standard_answers)
        pm.record("Tier 1 (Regex)", time.perf_counter() - t1_start)

        if is_exact:
            res = {
                "level": 4, 
                "isCorrect": True, 
                "message": "Perfect match! Your expression is very natural.", "judgedBy": "Regex"
            }
            pm.report(vector_score=1.0)
        else:
            # 🚄 Tier 2 & 3: 向量 + LLM
            user_vec = await llm_tools.get_embedding(req.user_answer, pm=pm)
            
            cur.execute("SELECT 1 - (primary_embedding <=> %s::vector) AS sim_score FROM language_items WHERE item_id = %s", (user_vec, item_pk))
            sim_row = cur.fetchone()
            sim_score = sim_row['sim_score'] if sim_row else 0.0
            
            res = await evaluator_service.process_judge(
                q_type=req.question_type, user_ans=req.user_answer, origin=req.original_text,
                std_answers=req.standard_answers, vector_score=sim_score, pm=pm
            )

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
                (user_id, question_id, item_id, rating, state, review_time, stability, difficulty)
            VALUES (%s::uuid, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s)
        """, (
            req.user_id, req.question_id, item_pk, 
            res["level"], current_state, new_s, new_d
        ))
        
        conn.commit()
        return {"status": "success", "data": res}
        
    except Exception as e:
        if conn: conn.rollback()
        print(f"❌ Evaluate Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

# ==========================================
# 接口 3: 标记讲义已看
# ==========================================
@router.post("/study/content_viewed")
async def mark_lesson_content_viewed(req: ContentViewedRequest):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO user_progress_of_lessons (user_id, course_id, viewed_lesson_id)
            VALUES (%s::uuid, %s, %s)
            ON CONFLICT (user_id, course_id)
            DO UPDATE SET viewed_lesson_id = EXCLUDED.viewed_lesson_id;
        """, (req.user_id, req.course_id, req.lesson_id))
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        if conn: conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()

# ==========================================
# 接口 4: TTS 接口
# ==========================================
@router.get("/study/tts")
async def generate_tts(text: str):
    voice = "zh-CN-XiaoxiaoNeural"
    communicate = edge_tts.Communicate(text, voice) 
    async def audio_stream():
        async for chunk in communicate.stream():
            if chunk["type"] == "audio": yield chunk["data"]
    return StreamingResponse(audio_stream(), media_type="audio/mpeg")

# ==========================================
# 接口 5: 完成课程，推进总体进度
# ==========================================
@router.post("/study/complete_lesson")
async def complete_lesson(req: CompleteLessonRequest):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO user_progress_of_lessons (user_id, course_id, last_completed_lesson_id)
            VALUES (%s::uuid, %s, %s)
            ON CONFLICT (user_id, course_id)
            DO UPDATE SET 
                last_completed_lesson_id = GREATEST(user_progress_of_lessons.last_completed_lesson_id, EXCLUDED.last_completed_lesson_id);
        """, (req.user_id, req.course_id, req.lesson_id))
        
        conn.commit()
        return {"status": "success", "message": f"Lesson {req.lesson_id} marked as completed."}
        
    except Exception as e:
        if conn: conn.rollback()
        print(f"❌ Complete Lesson Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn: conn.close()