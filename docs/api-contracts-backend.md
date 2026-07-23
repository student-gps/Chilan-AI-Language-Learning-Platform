---
title: API 契约 — 后端
generated: 2026-06-17
part: backend
---

# API 契约（后端完整接口文档）

> 所有接口均以 `http://localhost:8000`（开发）或生产域名为 base URL。
> 成功响应结构：`{ "status": "success", "data": {...} }` 或直接返回对象（部分旧接口）。
> 错误响应：`{ "status": "error", "message": "..." }` + HTTP 4xx/5xx。

---

## 健康检查

### `GET /health`
- 功能：服务健康检查
- 响应：`{ "status": "ok" }`

---

## 认证模块（`/auth/*`）

### `POST /auth/signup`
- 功能：邮件注册（发送 6 位验证码）
- Body: `{ "email": string, "password": string, "username": string }`
- 响应: `{ "status": "success", "message": "验证码已发送" }`
- 注意：密码 bcrypt 哈希存储；验证码 10 分钟有效

### `POST /auth/verify`
- 功能：验证邮件激活码，激活账户
- Body: `{ "email": string, "code": string, "username": string, "password": string }`
- 响应: `{ "status": "success", "data": { "access_token": string, "user_id": string, "username": string, "email": string } }`

### `POST /auth/login`
- 功能：邮件密码登录
- Body: `{ "email": string, "password": string }`
- 响应: `{ "status": "success", "data": { "access_token": string, "user_id": string, "username": string, "email": string } }`
- 注意：写入 `login_logs` 表（ip_address, user_agent, device_info）

### `POST /auth/forgot-password`
- 功能：发送密码重置验证码
- Body: `{ "email": string }`
- 响应: `{ "status": "success" }`

### `POST /auth/reset-password`
- 功能：使用验证码重置密码
- Body: `{ "email": string, "code": string, "new_password": string }`
- 响应: `{ "status": "success" }`

### `POST /auth/google`
- 功能：Google OAuth 登录/注册
- Body: `{ "access_token": string }`（Google OAuth access_token）
- 响应: 同 `/auth/login` 响应结构

### `POST /auth/apple`
- 功能：Apple OAuth 登录/注册
- Body: `{ "identity_token": string, "user_identifier": string, "full_name": { "givenName": string, "familyName": string } }`
- 响应: 同 `/auth/login` 响应结构

### `GET /auth/profile/:user_id`
- 功能：获取用户资料
- 响应: `{ "user_id": string, "username": string, "email": string, "is_active": bool, "created_at": string }`

### `PUT /auth/profile/:user_id`
- 功能：更新用户名
- Body: `{ "username": string }`
- 响应: `{ "status": "success" }`

### `PUT /auth/change-password/:user_id`
- 功能：修改密码（需旧密码）
- Body: `{ "current_password": string, "new_password": string }`
- 响应: `{ "status": "success" }`

### `DELETE /auth/account/:user_id`
- 功能：注销账户（软删除或物理删除）
- 响应: `{ "status": "success" }`

### `GET /auth/login-history/:user_id`
- 功能：获取登录历史记录
- 响应: `{ "status": "success", "data": [ { "login_time": string, "login_provider": string, "ip_address": string, "device_info": string } ] }`

---

## 课程模块（`/courses/*`, `/my-courses/*`）

### `GET /courses`
- 功能：获取所有课程列表
- 响应: `[ { "course_id": int, "name": string, "category": string, "target_language": string, "source_language": string } ]`

### `GET /courses/:id`
- 功能：获取单课详情
- Path: `id` = course_id (int)
- 响应: 同上，单个对象

### `GET /my-courses/:user_id`
- 功能：获取用户报名的课程列表（含进度）
- 响应: `[ { "course_id": int, "name": string, "status": "active"|"paused"|"completed", "last_completed_lesson_id": int|null, ... } ]`

### `POST /courses/enroll`
- 功能：报名课程
- Body: `{ "user_id": string, "course_id": int }`
- 限制：`MAX_ACTIVE_COURSES = 2`（同时最多 2 门 active）
- 响应: `{ "status": "success" }`

### `DELETE /courses/enroll`
- 功能：退课 / 暂停 / 清空进度
- Body: `{ "user_id": string, "course_id": int, "action": "drop"|"pause"|"clear_progress" }`
- 响应: `{ "status": "success" }`

### `GET /courses/:id/lessons`
- 功能：获取课时列表
- 响应: `[ { "lesson_id": int, "title": string, "lesson_metadata": { ... } } ]`

---

## 教室与统计模块

### `GET /classroom/stats/:user_id`
- 功能：教室页面统计数据
- 响应: `{ "active_courses": [ {...} ], "total_mastered": int, "total_reviewed_today": int, "streak_days": int }`

### `GET /daily_tasks/:user_id`
- 功能：今日待复习题目列表
- 响应: `{ "items": [ { "item_id": int, "question_id": int, "course_id": int, "lesson_id": int, "question_type": string, "original_text": string, "next_review": string } ], "total": int }`

### `GET /overview/stats/:user_id`
- 功能：学习概览统计
- 响应: `{ "total_days": int, "total_items_learned": int, "mastery_by_course": [ {...} ], "review_history": [ { "date": string, "count": int } ] }`

---

## 学习核心模块（`/study/*`）

### `GET /study/init`
- 功能：初始化学习流
- Query: `user_id`, `course_id`, `lesson_id`, `browse` (bool), `defer_practice` (0/1)
- 响应:
```json
{
  "mode": "teaching" | "practice" | "review" | "completed",
  "data": {
    "lesson_content": { ... },
    "pending_items": [ { "item_id", "question_id", "question_type", "original_text", "standard_answers", "metadata" } ],
    "practice_resume_index": int,
    "course_info": { ... }
  }
}
```

### `GET /study/practice_items`
- 功能：获取练习题列表（用于延迟加载）
- Query: `user_id`, `course_id`, `lesson_id`
- 响应: `{ "items": [ ... ] }` （同 pending_items 结构）

### `POST /study/evaluate`
- 功能：**三层答案评估（核心接口）**
- Body:
```json
{
  "user_id": "UUID",
  "item_id": int,
  "course_id": int,
  "lesson_id": int,
  "question_id": int,
  "question_type": "CN_TO_EN" | "EN_TO_CN" | "JA_SPEAK" | ... ,
  "original_text": "string",
  "standard_answers": ["string", ...],
  "user_answer": "string",
  "input_mode": "text" | "speech",
  "asr_text": "string | null",
  "audio_meta": { "confidence": float, "duration_ms": int },
  "forfeit": false
}
```
- 响应:
```json
{
  "status": "success",
  "data": {
    "level": 1 | 2 | 3 | 4,
    "isCorrect": bool,
    "message": "string",
    "judgedBy": "Regex" | "Vector Engine" | "LLM Mentor" | "ASR Guard" | "Forfeit",
    "inputMode": "text" | "speech",
    "recognizedText": "string | null",
    "vectorScore": float | null
  }
}
```
- FSRS 调度在此接口内自动更新（写入 `user_progress_of_language_items` + `review_logs`）

### `POST /study/speech/transcribe`
- 功能：Whisper ASR 语音识别
- Body: multipart/form-data
  - `audio`: audio file (webm/wav/mp3)
  - `language`: "zh" | "ja" | "en" | ...
  - `prompt`: 提示文本（提升识别精度）
- 响应: `{ "status": "success", "data": { "text": string, "confidence": float, "segments": [...], "duration_ms": int } }`

### `GET /study/tts`
- 功能：Edge TTS 即时合成语音
- Query: `text` (string), `language` ("zh"/"en"/"ja"/...)
- 响应: audio/mpeg 二进制流

### `POST /study/content_viewed`
- 功能：标记用户已查看讲义
- Body: `{ "user_id": string, "course_id": int, "lesson_id": int }`
- 响应: `{ "status": "success" }`

### `POST /study/practice_progress`
- 功能：保存练习断点（账号级续练）
- Body: `{ "user_id": string, "course_id": int, "lesson_id": int, "index": int }`
- 响应: `{ "status": "success" }`

### `POST /study/complete_lesson`
- 功能：完成课时，更新课时进度
- Body: `{ "user_id": string, "course_id": int, "lesson_id": int }`
- 响应: `{ "status": "success", "data": { "next_lesson_id": int | null } }`

### `GET /study/knowledge`
- 功能：获取词语知识详情（释义/例句）
- Query: `course_id`, `lesson_id`, `word`
- 响应: `{ "word": string, "pinyin": string, "part_of_speech": string, "definition": string, "example": {...} }`

### `GET /study/lesson_preview`
- 功能：获取课时的 video_render_plan（开发用）
- Query: `course_id`, `lesson_id`
- 响应: `{ "video_render_plan": {...} }`

---

## 媒体代理（`/media/*`）

### `GET /media/pinyin/:filename`
- 响应: 拼音音频文件（audio/mpeg）；先查本地，再 fallback R2

### `GET /media/intro/:filename`
- 响应: 课程介绍音频文件

### `GET /media/teaching-slide/:pipeline/:lang/:lesson/:file`
- Path params: pipeline（如 `integrated_chinese`）, lang（学习者语言）, lesson, file
- 响应: 静态幻灯片图片

### `GET /media/teaching-audio/:pipeline/:lang/:lesson/:file`
- 响应: 教学旁白音频文件

---

## 开发者接口（`/dev/*`）

### `GET /dev/lesson-artifact-preview`
- Query: `pipeline`, `lesson_id`
- 响应: 未同步的 lesson JSON 内容

### `POST /dev/content-builder/preview`
- Body: `{ "pipeline": string, "lesson_id": int }`
- 响应: 构建预览

### `POST /dev/content-builder/run-stream`
- Body: `{ "pipeline": string, "lesson_id": int }`
- 响应: NDJSON 流（逐行输出构建进度）

### `POST /dev/course-reset/preview`
- Body: `{ "course_id": int }`
- 响应: 重置影响预览

### `POST /dev/course-reset/execute`
- Body: `{ "course_id": int }`
- 响应: `{ "status": "success" }`

### `POST /dev/course-sync/preview`
- Body: `{ "pipeline": string, "lesson_ids": [int] }`
- 响应: 同步预览

### `POST /dev/course-sync/execute`
- Body: 同上
- 响应: `{ "status": "success", "synced": int }`

### `POST /dev/course-sync/execute-stream`
- Body: 同上
- 响应: NDJSON 流

---

## 通用约定

| 约定 | 说明 |
|------|------|
| 认证 | `Authorization: Bearer <JWT>` header（部分旧接口通过 query param 传 user_id） |
| 错误格式 | `{ "detail": "message" }`（FastAPI 默认）或 `{ "status": "error", "message": "..." }` |
| 时间格式 | ISO 8601 UTC（`2026-06-17T08:00:00Z`） |
| user_id 类型 | UUID 字符串（非整数）|
| course_id / lesson_id | 整数 |
