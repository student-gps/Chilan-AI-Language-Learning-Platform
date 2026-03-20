import sys
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
import edge_tts
import psycopg2
from psycopg2.extras import RealDictCursor

# 🌟 动态引入后端组件
sys.path.append(str(Path(__file__).resolve().parent.parent))
from database.connection import get_connection  # ✅ 正确引入数据库
from core.evaluator import Evaluator            # ✅ 引入判卷大脑
from core.scheduler import FSRSScheduler        # ✅ 引入记忆算法

router = APIRouter(tags=["Study Flow"])

# 初始化核心业务引擎
evaluator = Evaluator(api_key=os.getenv("GEMINI_API_KEY"))
scheduler = FSRSScheduler()

# ==========================================
# 1. 数据模型定义
# ==========================================
class EvaluateRequest(BaseModel):
    user_id: str
    lesson_id: int
    question_id: int
    question_type: str
    original_text: str
    standard_answers: List[str]
    user_answer: str


# ==========================================
# 2. 核心路由接口
# ==========================================

@router.get("/study/init")
async def init_study_flow(user_id: str, course_id: int = 1):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # ---------------------------------------------------------
        # 步骤一：【复习检测】查询是否有到期需复习的题目 (FSRS 逻辑)
        # ---------------------------------------------------------
        cur.execute("""
            SELECT q.id, q.question_id, q.question_type, q.original_text, q.standard_answers, p.next_review
            FROM language_items q
            JOIN user_progress_of_language_items p ON q.question_id = p.question_id
            WHERE p.user_id::text = %s 
              AND p.next_review <= CURRENT_TIMESTAMP
            ORDER BY p.next_review ASC
            LIMIT 20; -- 每次复习上限，防止题目太多吓跑用户
        """, (user_id,))
        
        due_questions = cur.fetchall()

        if due_questions:
            # 如果有到期题目，强制进入复习模式
            return {
                "mode": "review", 
                "message": f"欢迎回来！你有 {len(due_questions)} 道题需要巩固。",
                "data": {
                    "pending_items": due_questions
                }
            }

        # ---------------------------------------------------------
        # 步骤二：【新课分发】如果没有到期题目，拉取下一课内容
        # ---------------------------------------------------------
        # 1. 查进度：用户上一次学到哪了？
        cur.execute("""
            SELECT last_completed_lesson_id 
            FROM user_progress_of_lessons 
            WHERE user_id = %s AND course_id = %s
        """, (user_id, course_id))
        
        progress = cur.fetchone()
        # 如果没记录，从第 101 课开始（根据你之前的习惯）
        last_lesson = progress['last_completed_lesson_id'] if progress else 100
        next_lesson = last_lesson + 1

        # 2. 查新课内容
        cur.execute("""
            SELECT lesson_id, title, structured_content 
            FROM lessons 
            WHERE course_id = %s AND lesson_id = %s
        """, (course_id, next_lesson))
        
        lesson_row = cur.fetchone()

        if not lesson_row:
            return {
                "mode": "completed",
                "message": "太棒了！你已经完成了本项目的所有课程！"
            }

        # 3. 查新课配套的练习题
        cur.execute("""
            SELECT id, question_id, question_type, original_text, standard_answers
            FROM language_items
            WHERE course_id = %s AND lesson_id = %s
            ORDER BY question_id ASC
        """, (course_id, next_lesson))
        new_questions = cur.fetchall()

        return {
            "mode": "teaching", # 进入教学模式
            "data": {
                "lesson_content": {
                    "lesson_metadata": {"course_id": course_id, "lesson_id": next_lesson, "title": lesson_row['title']},
                    "course_content": lesson_row['structured_content']
                },
                "pending_items": new_questions
            }
        }

    except Exception as e:
        print(f"❌ Init Flow Error: {e}")
        raise HTTPException(status_code=500, detail="加载学习流失败")
    finally:
        if conn: conn.close()


@router.get("/study/tts")
async def generate_tts(text: str):
    """
    调用 Edge TTS 实时生成超自然语音
    """
    if not text:
        return {"error": "文本不能为空"}

    voice = "zh-CN-XiaoxiaoNeural"
    communicate = edge_tts.Communicate(text, voice, rate="+0%") 

    async def audio_stream():
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                yield chunk["data"]

    return StreamingResponse(audio_stream(), media_type="audio/mpeg")


@router.post("/study/evaluate")
async def evaluate_answer(req: EvaluateRequest):
    """
    智能判卷与记忆引擎：三级瀑布流判题 + FSRS 记忆曲线调度
    """
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # ==========================================
        # 🛡️ Tier 1: 正则/字符清洗精确匹配 (0 消耗)
        # ==========================================
        if evaluator.is_exact_match(req.user_answer, req.standard_answers):
            res = evaluator.get_exact_match_result()
            
            # 查出历史复习数据，为后续更新 FSRS 做准备
            cur.execute("""
                SELECT stability, difficulty, recent_history 
                FROM user_progress_of_language_items 
                WHERE user_id::text = %s AND question_id = %s
            """, (req.user_id, req.question_id))
            row = cur.fetchone()
            stability, difficulty, history = row if row else (0.5, 5.0, [])
            
        else:
            # ==========================================
            # 🚄 Tier 2 & 3: 向量检索 + LLM 深度判卷
            # ==========================================
            # 1. 生成用户答案的向量
            user_vec = evaluator.get_embedding(req.user_answer)
            
            # 2. 查询数据库，拿相似度和历史 FSRS 进度
            query = """
                SELECT 
                    p.stability, 
                    p.difficulty, 
                    p.recent_history, 
                    1 - (q.primary_embedding <=> %s::vector) AS score 
                FROM language_items q 
                LEFT JOIN user_progress_of_language_items p 
                       ON q.question_id = p.question_id AND p.user_id::text = %s 
                WHERE q.question_id = %s;
            """
            cur.execute(query, (user_vec, req.user_id, req.question_id))
            row = cur.fetchone()
            stability, difficulty, history, sim_score = row if row else (0.5, 5.0, [], 0.0)
            
            # 3. 丢给大模型决策器 (>0.95 返回极速结果，否则调用 API)
            res = await evaluator.judge(
                q_type=req.question_type, 
                user_input=req.user_answer, 
                orig_text=req.original_text, 
                std_answers=req.standard_answers, 
                score=sim_score
            )
            
        # ==========================================
        # 🧠 FSRS 记忆算法状态更新
        # ==========================================
        fsrs_rating = 5 - res["level"] # 将 1-4 级评价转为 FSRS 需要的打分
        new_s, new_d, next_r = scheduler.calc_next_review(stability or 0.5, difficulty or 5.0, fsrs_rating)
        new_hist = ((history or []) + [fsrs_rating])[-5:]
        
        # 1. 插入复习日志
        cur.execute("""
            INSERT INTO review_logs (user_id, question_id, rating, state, stability, difficulty) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (req.user_id, req.question_id, fsrs_rating, 2 if stability else 0, new_s, new_d))
        
        # 2. Upsert 用户进度表
        cur.execute("""
            INSERT INTO user_progress_of_language_items 
                (user_id, question_id, stability, difficulty, recent_history, is_mastered, last_review, next_review) 
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s) 
            ON CONFLICT (user_id, question_id) 
            DO UPDATE SET 
                stability = EXCLUDED.stability, 
                difficulty = EXCLUDED.difficulty, 
                recent_history = EXCLUDED.recent_history, 
                is_mastered = EXCLUDED.is_mastered, 
                last_review = CURRENT_TIMESTAMP, 
                next_review = EXCLUDED.next_review;
        """, (req.user_id, req.question_id, new_s, new_d, new_hist, scheduler.check_mastery(new_hist), next_r))
        
        conn.commit()
        return {"status": "success", "data": res}
        
    except Exception as e:
        if conn: conn.rollback()
        print(f"Evaluate Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()