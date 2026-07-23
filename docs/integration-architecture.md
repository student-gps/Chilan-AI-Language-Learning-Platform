---
title: 集成架构 — 前后端
generated: 2026-06-17
---

# 集成架构（Frontend ↔ Backend）

## 整体请求流

```
React SPA (Vite, port 5173)
  │
  │  HTTP REST（Axios via apiClient.js）
  ▼
FastAPI (uvicorn, port 8000)
  │
  ├── PostgreSQL (Neon Cloud)     ← 课程/用户/进度数据
  ├── Cloudflare R2               ← 音频/视频/幻灯片媒体文件
  ├── Gemini API (Google)         ← LLM 答案评估 + embedding
  ├── Whisper ASR API             ← 语音转文字
  └── Edge TTS                   ← 文字转语音
```

## 前端 API 客户端

文件：[`frontend/src/api/apiClient.js`](../frontend/src/api/apiClient.js)

```js
// base URL：开发环境 = http://localhost:8000，生产 = 生产域名
// 从 VITE_APP_API_BASE_URL 读取（注意：VITE_APP_ 前缀）
const apiClient = axios.create({ baseURL: import.meta.env.VITE_APP_API_BASE_URL });

// 拦截器：401 → 清除 token → 跳转 /auth
```

## 主要集成点

### 1. 学习流初始化

```
GET /study/init?user_id=&course_id=&lesson_id=&browse=&defer_practice=
  ← 返回：{ mode: "teaching"|"practice"|"review"|"completed", data: {...} }
```

`data` 包含：
- `lesson_content`：完整课时数据（词汇、对话、视频渲染计划、音频资产）
- `pending_items`：练习题列表（若 defer_practice=1 则为空）
- `practice_resume_index`：断点续练索引
- `course_info`：课程元信息

### 2. 答案评估（核心）

```
POST /study/evaluate
Body: {
  user_id, item_id, course_id, lesson_id, question_id,
  question_type, original_text, standard_answers,
  user_answer,          // 文字模式
  input_mode,           // "text" | "speech"
  asr_text,             // 语音模式（ASR 转写结果）
  audio_meta: { confidence, duration_ms },
  forfeit: bool
}

Response: { status: "success", data: {
  level: 1-4,           // 1=Again 2=Hard 3=Good 4=Easy
  isCorrect: bool,
  message: string,
  judgedBy: "Regex"|"Vector Engine"|"LLM Mentor"|"ASR Guard"|"Forfeit",
  inputMode: string,
  recognizedText: string|null,
  vectorScore: float|null
}}
```

### 3. 媒体资源 URL 解析

媒体文件的 URL 由后端在响应时动态生成（R2 签名 URL 或公开 URL），前端直接使用，不做任何构造：

| 资源类型 | 来源 |
|----------|------|
| 拼音音频 | `GET /media/pinyin/:filename` |
| 课程介绍音频 | `GET /media/intro/:filename` |
| 幻灯片图片 | `GET /media/teaching-slide/:pipeline/:lang/:lesson/:file` |
| 教学旁白音频 | `GET /media/teaching-audio/:pipeline/:lang/:lesson/:file` |
| 对话/句子音频 | `lesson_audio_assets.items[].audio_url`（R2 签名 URL，study/init 返回）|
| 讲解视频 | `explanation_video.media_url`（R2 签名 URL，study/init 返回）|
| TTS 即时合成 | `GET /study/tts?text=&language=` |

### 4. 语音录制到评估流程

```
用户录音（MediaRecorder API）
  ↓
POST /study/speech/transcribe
  multipart: { audio: blob, language: "zh"|"ja"|"en", prompt: string }
  ← { status: "success", data: { text, confidence, segments, duration_ms } }
  ↓
POST /study/evaluate（input_mode="speech", asr_text=...)
```

### 5. 课程管理

| 操作 | 接口 |
|------|------|
| 获取所有课程 | `GET /courses` |
| 获取用户课程 | `GET /my-courses/:user_id` |
| 报名课程 | `POST /courses/enroll` |
| 退课/暂停 | `DELETE /courses/enroll` |
| 课时列表 | `GET /courses/:id/lessons` |
| 教室统计 | `GET /classroom/stats/:user_id` |
| 今日任务 | `GET /daily_tasks/:user_id` |
| 学习概览 | `GET /overview/stats/:user_id` |

## 认证集成

```
前端：                             后端：
POST /auth/login
  ← { access_token: JWT, user_id, username, email }
  
JWT 存入 localStorage
  
后续请求 Header: Authorization: Bearer <JWT>
  → auth.py 中间件验证（PyJWT）
  → 401 → 前端跳转 /auth
```

**注意：** 当前后端 API 多处直接在 query params 中传 `user_id`（非 JWT 中间件），这是历史设计。新功能建议从 JWT 提取 user_id。

## CORS 配置

```python
# 生产：chilanlearning.com
# 开发：localhost:5173
# 额外：APP_CORS_ORIGINS 环境变量
```

## 前端环境变量

```bash
# .env.development
VITE_APP_API_BASE_URL=http://localhost:8000

# .env.production
VITE_APP_API_BASE_URL=https://api.chilanlearning.com  # 生产 URL
```

## TanStack Query 缓存键（`src/api/queries.js`）

```js
queryKeys = {
  courses: ()        → ['courses']
  myCourses: (uid)   → ['my-courses', uid]
  classroomStats:(uid)→ ['classroom-stats', uid]
  // ...其他
}
```

前端通过 `useQueryClient().invalidateQueries({ queryKey: queryKeys.myCourses(userId) })` 在报名/退课后使缓存失效。
