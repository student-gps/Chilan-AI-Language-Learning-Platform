import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from routers import auth, study
from database.connection import get_connection
from core.evaluator import Evaluator
from core.scheduler import FSRSScheduler

app = FastAPI(title="Chilan LRS - Core Service")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载认证模块
app.include_router(auth.router)

# 挂载学习模块
app.include_router(study.router)

# 初始化业务组件
evaluator = Evaluator(api_key=os.getenv("GEMINI_API_KEY"))
scheduler = FSRSScheduler()

# --- 业务模型 ---
class EnrollReq(BaseModel):
    user_id: str
    course_id: int

# 🌟 新的判题请求模型，严格对齐前端传来的 JSON
class EvaluateRequest(BaseModel):
    user_id: str
    lesson_id: int
    question_id: int
    question_type: str
    original_text: str
    standard_answers: List[str]
    user_answer: str

def get_db():
    conn = get_connection()
    try: yield conn
    finally: conn.close()

# --- 课程系统 (已补全) ---
@app.get("/courses")
async def list_all_courses(db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT course_id, name, category, cover_color FROM courses")
    return [{"id": r[0], "name": r[1], "category": r[2], "color": r[3]} for r in cur.fetchall()]

@app.get("/my-courses/{user_id}")
async def get_my_courses(user_id: str, db=Depends(get_db)):
    cur = db.cursor()
    query = """
        SELECT c.course_id, c.name, c.category, c.cover_color, 
               COUNT(p.progress_id) FILTER (WHERE p.is_mastered = TRUE) as mastered_count
        FROM courses c
        JOIN user_courses uc ON c.course_id = uc.course_id
        LEFT JOIN language_items li ON c.course_id = li.course_id
        LEFT JOIN user_progress_of_language_items p ON li.question_id = p.question_id AND p.user_id::text = %s
        WHERE uc.user_id::text = %s
        GROUP BY c.course_id;
    """
    cur.execute(query, (user_id, user_id))
    return [{"id": r[0], "name": r[1], "category": r[2], "color": r[3], "mastered": r[4]} for r in cur.fetchall()]

@app.post("/courses/enroll")
async def enroll_course(req: EnrollReq, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("INSERT INTO user_courses (user_id, course_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (req.user_id, req.course_id))
        db.commit(); return {"status": "success"}
    except Exception as e: db.rollback(); raise HTTPException(status_code=500, detail=str(e))

# --- 统计与任务 (已补全) ---
@app.get("/classroom/stats/{user_id}")
async def get_classroom_stats(user_id: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM user_progress_of_language_items WHERE user_id::text = %s AND next_review <= CURRENT_TIMESTAMP", (user_id,))
        rem = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT question_id) FROM review_logs WHERE user_id::text = %s AND review_time >= CURRENT_DATE", (user_id,))
        rev = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM review_logs WHERE user_id::text = %s AND state = 0 AND review_time >= CURRENT_DATE", (user_id,))
        new_l = cur.fetchone()[0]
        return {"totalRemaining": rem, "totalReviewed": rev, "totalNewLearned": new_l}
    finally: cur.close()

@app.get("/daily_tasks/{user_id}")
async def get_daily_tasks(user_id: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        query = """
            SELECT q.question_id, q.question_type, q.original_text FROM language_items q
            JOIN user_progress_of_language_items p ON q.question_id = p.question_id
            WHERE p.user_id::text = %s AND p.next_review <= CURRENT_TIMESTAMP ORDER BY p.next_review ASC LIMIT 20;
        """
        cur.execute(query, (user_id,))
        return [{"id": r[0], "type": r[1], "text": r[2]} for r in cur.fetchall()]
    finally: cur.close()

# --- 判题与 FSRS 记忆更新系统 ---
@app.post("/study/evaluate")
async def evaluate_answer(req: EvaluateRequest, db=Depends(get_db)):
    cur = db.cursor()
    try:
        # 1. 将用户的回答转换为向量
        user_vec = evaluator.get_embedding(req.user_answer)
        
        # 2. 查询数据库，获取该题目的历史进度，并利用 pgvector 极速计算余弦相似度
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
        
        # 容错：如果题目由于某种原因在数据库中丢失，给出默认分数
        stability, difficulty, history, sim_score = row if row else (0.5, 5.0, [], 0.0)
        
        # 3. 调用 AI 判卷大脑 (传入计算好的相似度)
        res = await evaluator.judge(
            q_type=req.question_type, 
            user_input=req.user_answer, 
            orig_text=req.original_text, 
            std_answers=req.standard_answers, 
            score=sim_score
        )
        
        # --------- 以下为 FSRS 记忆算法更新逻辑 ---------
        # 根据 AI 的评分 (1-4级)，反转为 FSRS 评分 (4为掌握，1为遗忘)
        fsrs_rating = 5 - res["level"]
        
        # 计算下一次复习的时间和新的稳定性/难度
        new_s, new_d, next_r = scheduler.calc_next_review(stability or 0.5, difficulty or 5.0, fsrs_rating)
        new_hist = ((history or []) + [fsrs_rating])[-5:]
        
        # 记录用户的本次复习日志
        log_query = """
            INSERT INTO review_logs (user_id, question_id, rating, state, stability, difficulty) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cur.execute(log_query, (req.user_id, req.question_id, fsrs_rating, 2 if stability else 0, new_s, new_d))
        
        # 更新该题目的总体掌握进度和下一次复习时间 (Upsert 逻辑)
        upsert_query = """
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
        """
        cur.execute(upsert_query, (req.user_id, req.question_id, new_s, new_d, new_hist, scheduler.check_mastery(new_hist), next_r))
        
        db.commit()
        
        # 4. 返回前端期待的统一格式
        return {
            "status": "success", 
            "data": res
        }
        
    except Exception as e:
        db.rollback()
        print(f"Evaluate Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)