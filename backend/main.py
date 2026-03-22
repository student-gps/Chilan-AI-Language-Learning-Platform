import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

# 🌟 1. 挂载路由（所有的 /study/... 和 /auth/... 逻辑都已移入这两个文件）
from routers import auth, study
from database.connection import get_connection

app = FastAPI(title="Chilan LRS - Core Service")

# --- ⚙️ 中间件配置 ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://chilan-ai-language-learning-platform-9apcf1evg.vercel.app/"
    ], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 🚀 挂载路由模块 ---
app.include_router(auth.router)
app.include_router(study.router)

# --- 🧪 数据库依赖 ---
def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

# --- 📦 业务请求模型 ---
class EnrollReq(BaseModel):
    user_id: str
    course_id: int

# ==========================================
# 2. 课程管理系统 (核心业务：保留)
# ==========================================

@app.get("/courses")
async def list_all_courses(db=Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT course_id, name, category, cover_color FROM courses")
    return [{"id": r[0], "name": r[1], "category": r[2], "color": r[3]} for r in cur.fetchall()]

@app.get("/my-courses/{user_id}")
async def get_my_courses(user_id: str, db=Depends(get_db)):
    cur = db.cursor()
    # 🌟 关联查询用户课程及 FSRS 掌握进度
    query = """
        SELECT c.course_id, c.name, c.category, c.cover_color, 
               COUNT(p.question_id) FILTER (WHERE p.is_mastered = TRUE) as mastered_count
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
        # 记录用户选课
        cur.execute("INSERT INTO user_courses (user_id, course_id) VALUES (%s, %s) ON CONFLICT DO NOTHING", (req.user_id, req.course_id))
        
        # 🌟 关键：初始化该课程的“课时进度”记录，从 100 开始（即下一课是 101）
        cur.execute("""
            INSERT INTO user_progress_of_lessons (user_id, course_id, last_completed_lesson_id)
            VALUES (%s, %s, 100) ON CONFLICT DO NOTHING
        """, (req.user_id, req.course_id))
        
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 3. 教室仪表盘与统计 (数据中心：保留)
# ==========================================

@app.get("/classroom/stats/{user_id}")
async def get_classroom_stats(user_id: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        # 1. 查询待复习数 (Based on FSRS next_review)
        cur.execute("SELECT COUNT(*) FROM user_progress_of_language_items WHERE user_id::text = %s AND next_review <= CURRENT_TIMESTAMP", (user_id,))
        rem = cur.fetchone()[0]
        # 2. 查询今日已复习数量
        cur.execute("SELECT COUNT(DISTINCT question_id) FROM review_logs WHERE user_id::text = %s AND review_time >= CURRENT_DATE", (user_id,))
        rev = cur.fetchone()[0]
        # 3. 查询今日新学题目数量
        cur.execute("SELECT COUNT(*) FROM review_logs WHERE user_id::text = %s AND state = 0 AND review_time >= CURRENT_DATE", (user_id,))
        new_l = cur.fetchone()[0]
        return {"totalRemaining": rem, "totalReviewed": rev, "totalNewLearned": new_l}
    finally:
        cur.close()

@app.get("/daily_tasks/{user_id}")
async def get_daily_tasks(user_id: str, db=Depends(get_db)):
    cur = db.cursor()
    try:
        query = """
            SELECT q.question_id, q.question_type, q.original_text FROM language_items q
            JOIN user_progress_of_language_items p ON q.question_id = p.question_id
            WHERE p.user_id::text = %s AND p.next_review <= CURRENT_TIMESTAMP 
            ORDER BY p.next_review ASC LIMIT 20;
        """
        cur.execute(query, (user_id,))
        return [{"id": r[0], "type": r[1], "text": r[2]} for r in cur.fetchall()]
    finally:
        cur.close()
        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)