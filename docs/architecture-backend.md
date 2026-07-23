---
title: 架构文档 — 后端（backend）
generated: 2026-06-17
part: backend
---

# 架构文档 — 后端

## 技术栈

| 类别 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 框架 | FastAPI | latest | async/sync 混用，uvicorn 部署 |
| 运行时 | Python | 3.13 | 用内置泛型（`list[str]`，`dict\|None`） |
| 数据库驱动 | psycopg2-binary | v2 | **非** psycopg3 |
| 连接池 | ThreadedConnectionPool | — | 环境变量控制（DB_POOL_*） |
| 数据库 | PostgreSQL（Neon Cloud）| — | pgvector 扩展用于 embedding 检索 |
| LLM | Gemini 2.0 Flash（google-genai SDK）| — | 支持 Vertex AI 模式 |
| Embedding | VoyageAI / Doubao / Gemini | — | 工厂模式，环境变量切换 |
| 媒体存储 | Cloudflare R2（boto3 S3 兼容）| — | 签名 URL 或公开 URL |
| TTS | Edge TTS | latest | 多语言，声音/语速可配置 |
| ASR | Whisper（OpenAI SDK）| — | 带噪声过滤 |
| JWT | PyJWT（内部）+ python-jose（OAuth）| — | 两库职责不同，不要混用 |
| 邮件 | SMTP 或 Resend API | — | MAIL_PROVIDER 环境变量切换 |

## 架构模式

**分层 REST API：路由层 → 服务层 → 数据层**

```
FastAPI app (main.py)
  │
  ├── routers/auth.py          # /auth/* 所有认证逻辑
  ├── routers/study.py         # /study/* 学习核心
  └── main.py 直接处理          # /courses/*, /classroom/*, /my-courses/*, /daily_tasks/*, /overview/*
```

## 三层答案评估（核心业务）

```
POST /study/evaluate
  │
  ▼ routers/study.py: evaluate_answer()
  │
  ├─ Tier 1: StudyEvaluator.check_exact()
  │   └── 正则清洗后精确匹配 standard_answers
  │   └── 命中 → level=4, judgedBy="Regex", 直接返回
  │
  ├─ Tier 2: LLMEngine + pgvector 余弦相似度
  │   └── 用户答案 → embedding → SELECT 1-(primary_embedding <=> $vec) FROM answer_embeddings
  │   └── sim_score > 0.95 → level=4, judgedBy="Vector Engine"
  │
  └─ Tier 3: LanguageTools.judge_with_ai()
      └── prompts.get_eval_prompt(q_type) → LLMEngine.generate_json()
      └── 返回 {level, is_correct, explanation}
      └── StudyEvaluator._normalize_ai_result() 规范化
```

### 题型到 Prompt 的映射（`services/llm/prompts.py`）

| 题型 | 说明 |
|------|------|
| `CN_TO_EN` | 中译英 |
| `EN_TO_CN` | 英译中 |
| `PATTERN_DRILL` | 英文句型练习 |
| `CN_TO_JA` | 中译日 |
| `JA_TO_CN` | 日译中 |
| `JA_LISTEN_WRITE` | 日语听写 |
| `JA_SPEAK` | 日语口语（ASR 评估） |
| `TARGET_LISTEN_WRITE` | 英语听写 |
| `TARGET_SPEAK` | 英语口语（ASR 评估） |
| `CN_TO_XX` | 动态生成（XX 为任意语言代码） |

## FSRS 间隔复习调度（`services/study/scheduler.py`）

```python
# 关键参数
stability: float   # 记忆稳定性（越高越难遗忘）
difficulty: float  # 1.0-10.0
rating: int        # 1=Again, 2=Hard, 3=Good, 4=Easy

# 下次复习时间 = now() + interval（天），interval = round(stability)
# 掌握条件：最近 5 次中，≥4 次 rating=4，且无 rating≤2
```

## 路由清单

### `routers/auth.py`（prefix: `/auth`）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/signup` | 邮件注册（发验证码） |
| POST | `/auth/verify` | 验证激活码 |
| POST | `/auth/login` | 邮件密码登录 |
| POST | `/auth/forgot-password` | 发重置码 |
| POST | `/auth/reset-password` | 重置密码 |
| POST | `/auth/google` | Google OAuth |
| POST | `/auth/apple` | Apple OAuth |
| GET | `/auth/profile/:user_id` | 获取用户资料 |
| PUT | `/auth/profile/:user_id` | 更新用户名 |
| PUT | `/auth/change-password/:user_id` | 修改密码 |
| DELETE | `/auth/account/:user_id` | 注销账号 |
| GET | `/auth/login-history/:user_id` | 登录历史 |

### `routers/study.py`（无 prefix）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/study/init` | 初始化学习流（返回 teaching/practice/review 模式） |
| GET | `/study/practice_items` | 获取练习题列表 |
| POST | `/study/evaluate` | **三层答案评估**（核心接口） |
| POST | `/study/speech/transcribe` | Whisper ASR 语音转文字 |
| GET | `/study/tts` | Edge TTS 文字转语音 |
| POST | `/study/content_viewed` | 标记讲义已看 |
| POST | `/study/practice_progress` | 保存练习断点进度 |
| POST | `/study/complete_lesson` | 完成课时，更新进度 |
| GET | `/study/knowledge` | 获取词语知识详情 |
| GET | `/study/lesson_preview` | 获取课程渲染计划（dev） |

### `main.py`（直接注册）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/courses` | 所有课程列表 |
| GET | `/courses/:id` | 单课详情 |
| GET | `/my-courses/:user_id` | 用户已报名课程 |
| POST | `/courses/enroll` | 报名课程 |
| DELETE | `/courses/enroll` | 退课/暂停/清空进度 |
| GET | `/courses/:id/lessons` | 课时列表 |
| GET | `/classroom/stats/:user_id` | 教室统计数据 |
| GET | `/daily_tasks/:user_id` | 待复习题目列表 |
| GET | `/overview/stats/:user_id` | 学习概览统计 |
| GET | `/media/pinyin/:filename` | 拼音音频（本地→R2 fallback）|
| GET | `/media/intro/:filename` | 课程介绍音频 |
| GET | `/media/teaching-slide/:pipeline/:lang/:lesson/:file` | 静态幻灯片图片 |
| GET | `/media/teaching-audio/:pipeline/:lang/:lesson/:file` | 教学旁白音频 |

### 开发者接口（`/dev/*`）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/dev/lesson-artifact-preview` | 预览未同步的 lesson JSON |
| POST | `/dev/content-builder/preview` | 内容构建预览 |
| POST | `/dev/content-builder/run-stream` | 内容构建执行（NDJSON 流） |
| POST | `/dev/course-reset/preview` | 课程重置预览 |
| POST | `/dev/course-reset/execute` | 课程重置执行 |
| POST | `/dev/course-sync/preview` | 课程同步预览 |
| POST | `/dev/course-sync/execute` | 课程同步执行 |
| POST | `/dev/course-sync/execute-stream` | 课程同步执行（NDJSON 流） |

## LLM 引擎（`services/llm/base_engine.py`）

```python
# 单例，在 routers/study.py 模块加载时初始化
engine = LLMEngine.from_env()

# 环境变量控制
LLM_JUDGE_PROVIDER=gemini         # 当前仅支持 gemini
LLM_JUDGE_GEMINI_API_KEY=...
LLM_JUDGE_GEMINI_MODEL_ID=gemini-2.5-flash
LLM_JUDGE_GEMINI_USE_VERTEX=false  # true 则切换到 Vertex AI
```

## 媒体存储（`services/storage/`）

```python
# 工厂函数
storage = get_media_storage(optional=True)   # 返回 R2Storage | None

# R2Storage 核心方法
storage.upload_file(local_path, object_key)  # 上传到 R2
storage.resolve_url(object_key)              # 生成签名 URL 或公开 URL

# R2 key 约定
"zh/audio/{lesson_folder}/sentences/{file}"   # 逐句音频
"zh/video/{learner_lang}/{file}"              # 讲解视频
"{lang}/audio/narration/{lang}/{lesson}/{file}" # 教学旁白音频
```

## 数据库连接（`database/connection.py`）

- 连接池：psycopg2 `ThreadedConnectionPool`
- `DB_MODE=cloud`（默认）读 `APP_DATABASE_URL`
- `DB_MODE=local` 读 `APP_DATABASE_URL_LOCAL`
- `get_connection()` 返回池化连接代理（`close()` 归还而非断开）

## 内容构建流水线（`content_builder/`）

三阶段离线流水线，**不是 API**：

```
Stage 1: generate.py
  PDF → LLM 提取 → Lesson JSON + 对话音频 → output_json/

Stage 2: render_narration.py
  Lesson JSON → TTS 旁白 → [可选] Remotion+ffmpeg 视频 → output_audio/ + output_video/

Stage 3 (Publish): sync_to_db.py
  本地音频+视频 → R2 上传 → object_key 写回 JSON → PostgreSQL 同步
  → 移动 JSON 到 synced_json/
```

多 Pipeline 支持：
- `integrated_chinese`：综合中文（英/法/日/韩/越等版）
- `new_concept_english`：新概念英语
- `minna_no_nihongo`：大家的日本语

## 认证设计

- 邮件注册：bcrypt 密码哈希，验证码 6 位数字，10 分钟有效
- Google OAuth：调用 Google userinfo API 验证 access_token
- Apple OAuth：用 `python-jose` 解码 JWT，用 PyJWK 验证签名
- 内部 JWT：`PyJWT` 生成（`database/utils.py: create_access_token()`）
- 邮件服务：`MAIL_PROVIDER=smtp`（默认）或 `resend`

## CORS 配置

```python
# main.py：自动包含以下来源
production_origins = ["https://www.chilanlearning.com", "https://chilanlearning.com"]
local_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
# 额外来源通过 APP_CORS_ORIGINS 环境变量（逗号分隔）配置
```
