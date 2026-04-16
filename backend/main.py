import os
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List

# 🌟 1. 挂载路由（所有的 /study/... 和 /auth/... 逻辑都已移入这两个文件）
from routers import auth, study
from database.connection import get_connection
from config.env import get_env

app = FastAPI(title="Chilan LRS - Core Service")

# 1. 从环境变量读取线上地址
cors_origins_str = get_env("APP_CORS_ORIGINS", default="")
# 2. 将字符串转为列表，并去掉多余空格
origins = [o.strip() for o in cors_origins_str.split(",") if o.strip()]

# 线上常用域名兜底，避免部署环境漏配 APP_CORS_ORIGINS 时注册/登录直接被浏览器拦截
production_origins = [
    "https://www.chilanlearning.com",
    "https://chilanlearning.com",
]

# 3. 强行加入本地开发地址（确保本地开发永远可用）
local_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

for origin in production_origins + local_origins:
    if origin not in origins:
        origins.append(origin)

# 🌟 最终的 origins 列表会包含线上所有域名 + 本地 5173
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

audio_static_dir = Path(__file__).resolve().parent / "content_builder" / "output_audio"
audio_static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media/audio", StaticFiles(directory=str(audio_static_dir)), name="media-audio")

video_static_dir = Path(__file__).resolve().parent / "content_builder" / "output_video"
video_static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media/video", StaticFiles(directory=str(video_static_dir)), name="media-video")

# --- 🚀 挂载路由模块 ---
app.include_router(auth.router)
app.include_router(study.router)

# --- 🔊 拼音音频代理（本地文件优先，R2 presigned URL 兜底）---
from fastapi.responses import FileResponse
from services.storage.media_storage import get_media_storage as _get_media_storage
_pinyin_storage = _get_media_storage(optional=True)
_PINYIN_LOCAL_DIR = Path(__file__).resolve().parent / "pinyin_audio"
_INTRO_LOCAL_DIR = Path(__file__).resolve().parent.parent / "frontend" / "public" / "audio" / "intro"

@app.get("/media/pinyin/{filename}")
async def get_pinyin_audio(filename: str):
    """Serve pinyin audio: local file first (dev), then R2 presigned URL (prod)."""
    local_file = _PINYIN_LOCAL_DIR / filename
    if local_file.exists():
        return FileResponse(str(local_file), media_type="audio/wav")
    if not _pinyin_storage:
        raise HTTPException(status_code=404, detail=f"{filename} not found locally and storage not configured")
    object_key = f"zh/audio/pinyin/{filename}"
    try:
        url = _pinyin_storage.resolve_url(object_key)
        return RedirectResponse(url=url, status_code=302)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/media/intro/{filename}")
async def get_intro_audio(filename: str):
    """Serve course-intro narration audio: local file first (dev), then R2 (prod)."""
    local_file = _INTRO_LOCAL_DIR / filename
    if local_file.exists():
        return FileResponse(str(local_file), media_type="audio/mpeg")
    if not _pinyin_storage:
        raise HTTPException(status_code=404, detail=f"{filename} not found locally and storage not configured")
    object_key = f"zh/audio/intro/{filename}"
    try:
        url = _pinyin_storage.resolve_url(object_key)
        return RedirectResponse(url=url, status_code=302)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    cur.execute("SELECT course_id, name, category, target_language, source_language FROM courses")
    return [{
        "id": r[0],
        "name": r[1],
        "category": r[2],
        "target_language": r[3],
        "source_language": r[4],
    } for r in cur.fetchall()]

@app.get("/my-courses/{user_id}")
async def get_my_courses(user_id: str, db=Depends(get_db)):
    cur = db.cursor()
    # 🌟 关联查询用户课程及 FSRS 掌握进度
    query = """
        SELECT c.course_id, c.name, c.category,
               c.target_language, c.source_language,
               COUNT(p.question_id) FILTER (WHERE p.is_mastered = TRUE) as mastered_count
        FROM courses c
        JOIN user_courses uc ON c.course_id = uc.course_id
        LEFT JOIN language_items li ON c.course_id = li.course_id
        LEFT JOIN user_progress_of_language_items p ON li.question_id = p.question_id AND p.user_id::text = %s
        WHERE uc.user_id::text = %s
        GROUP BY c.course_id;
    """
    cur.execute(query, (user_id, user_id))
    return [{
        "id": r[0],
        "name": r[1],
        "category": r[2],
        "target_language": r[3],
        "source_language": r[4],
        "mastered": r[5],
    } for r in cur.fetchall()]

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
