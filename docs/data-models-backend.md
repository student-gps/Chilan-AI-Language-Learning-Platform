---
title: 数据模型 — 后端（backend）
generated: 2026-06-17
part: backend
---

# 数据模型（PostgreSQL）

## 数据库扩展

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- UUID 生成
CREATE EXTENSION IF NOT EXISTS vector;       -- pgvector（embedding 向量检索）
```

## 核心表

### `users`

| 列名 | 类型 | 说明 |
|------|------|------|
| `user_id` | UUID (PK) | 用户 ID |
| `username` | TEXT | 用户名（2-24 字符） |
| `email` | TEXT (UNIQUE) | 邮箱 |
| `password_hash` | TEXT | bcrypt 哈希；Google 用户为 `"GOOGLE_USER"`；Apple 为 `"APPLE_USER"` |
| `is_active` | BOOLEAN | 邮件验证后激活 |
| `created_at` | TIMESTAMP | 注册时间 |

### `verification_codes`

| 列名 | 类型 | 说明 |
|------|------|------|
| `email` | TEXT (PK) | 邮箱（唯一冲突时覆盖） |
| `code` | TEXT | 6 位数字验证码 |
| `created_at` | TIMESTAMP | 创建时间（10分钟有效期由应用层控制） |

### `login_logs`（表名：`login_logs`）

| 列名 | 类型 | 说明 |
|------|------|------|
| `log_id` | SERIAL (PK) | |
| `user_id` | UUID | 外键 → users |
| `login_provider` | TEXT | `password` / `google` / `apple` |
| `login_time` | TIMESTAMP | |
| `ip_address` | TEXT | |
| `user_agent` | TEXT | |
| `device_info` | TEXT | 解析后的设备简述 |
| `status` | TEXT | `success` |

### `courses`

| 列名 | 类型 | 说明 |
|------|------|------|
| `course_id` | SERIAL (PK) | |
| `name` | TEXT | 课程名 |
| `category` | TEXT | |
| `target_language` | TEXT | 目标语言（如 `zh`） |
| `source_language` | TEXT | 学习者母语（如 `en`） |

### `lessons`

| 列名 | 类型 | 说明 |
|------|------|------|
| `lesson_id` | INTEGER (PK) | |
| `course_id` | INTEGER | 外键 → courses |
| `title` | TEXT | 课时标题 |
| `lesson_metadata` | JSONB | 包含 `title_localized`、`target_language` 等 |
| `video_render_plan` | JSONB | Remotion 视频渲染计划（scene 列表） |

### `language_items`

语言学习条目（练习题）的核心表。

| 列名 | 类型 | 说明 |
|------|------|------|
| `item_id` | SERIAL (PK) | |
| `question_id` | INTEGER | 课内题目编号 |
| `course_id` | INTEGER | 外键 → courses |
| `lesson_id` | INTEGER | |
| `question_type` | TEXT | 见下方题型枚举 |
| `original_text` | TEXT | 题目原文 |
| `standard_answers` | JSONB / TEXT[] | 标准答案列表 |
| `metadata` | JSONB | 含 `knowledge`（词语释义）、`speech_eval_config` 等 |
| `answer_embedding_id` | INTEGER | 外键 → answer_embeddings |

**question_type 枚举：** `CN_TO_EN`, `EN_TO_CN`, `CN_TO_JA`, `JA_TO_CN`, `JA_LISTEN_WRITE`, `JA_SPEAK`, `PATTERN_DRILL`, `TARGET_LISTEN_WRITE`, `TARGET_SPEAK`, `TARGET_TO_SUPPORT`, `SUPPORT_TO_TARGET`, `CN_LISTEN_WRITE`，以及动态模式 `CN_TO_XX`、`XX_TO_CN`。

### `answer_embeddings`

| 列名 | 类型 | 说明 |
|------|------|------|
| `embedding_id` | SERIAL (PK) | |
| `primary_embedding` | VECTOR | 标准答案向量（pgvector）|
| `provider` | TEXT | 嵌入供应商（`gemini`/`doubao`/`voyage`）|
| `model_id` | TEXT | 模型 ID |
| `input_text` | TEXT | 原始输入文本（用于去重） |

### `user_progress_of_language_items`

FSRS 每题学习状态。

| 列名 | 类型 | 说明 |
|------|------|------|
| `user_id` | UUID | 外键 → users |
| `item_id` | INTEGER | 外键 → language_items（唯一约束：user_id + item_id）|
| `question_id` | INTEGER | |
| `stability` | FLOAT | FSRS 记忆稳定性 |
| `difficulty` | FLOAT | FSRS 难度（1.0-10.0）|
| `state` | INTEGER | 0=新题，1=复习中 |
| `recent_history` | JSONB / INT[] | 最近 5 次评分记录 |
| `is_mastered` | BOOLEAN | 最近 5 次：≥4 次 rating=4 且无 rating≤2 |
| `last_review` | TIMESTAMP | |
| `next_review` | TIMESTAMP | 下次复习时间（UTC）|

### `user_progress_of_lessons`

课时进度。

| 列名 | 类型 | 说明 |
|------|------|------|
| `user_id` | UUID | |
| `course_id` | INTEGER | |
| `last_completed_lesson_id` | INTEGER | 最后完成的课时 ID |
| `viewed_lesson_id` | INTEGER | 最后查看的课时 ID |
| `practice_question_index` | INTEGER | 练习断点（账号级续练）|
| `practice_question_updated_at` | TIMESTAMP | |

### `user_courses`

用户报名状态。

| 列名 | 类型 | 说明 |
|------|------|------|
| `user_id` | UUID | |
| `course_id` | INTEGER | |
| `status` | TEXT | `active` / `paused` / `completed` |

### `review_logs`

练习流水记录（用于统计今日复习数、历史分析）。

| 列名 | 类型 | 说明 |
|------|------|------|
| `log_id` | SERIAL (PK) | |
| `user_id` | UUID | |
| `item_id` | INTEGER | |
| `question_id` | INTEGER | |
| `course_id` | INTEGER | |
| `lesson_id` | INTEGER | |
| `rating` | INTEGER | 1-4（评估结果 level）|
| `state` | INTEGER | 0=新题，1=复习 |
| `review_time` | TIMESTAMP | |
| `stability` | FLOAT | 评估后的稳定性 |
| `difficulty` | FLOAT | 评估后的难度 |
| `input_mode` | TEXT | `text` / `speech` / `forfeit` |
| `asr_text` | TEXT | 语音识别原文（语音模式）|
| `asr_confidence` | FLOAT | ASR 置信度 |
| `vector_score` | FLOAT | 向量相似度得分 |
| `audio_duration_ms` | INTEGER | 录音时长（毫秒）|

### `vocabulary_knowledge`

词语释义缓存（用于 `/study/knowledge` 接口）。

| 列名 | 类型 | 说明 |
|------|------|------|
| `course_id` | INTEGER | |
| `lesson_id` | INTEGER | |
| `word` | TEXT | |
| `pinyin` | TEXT | |
| `part_of_speech` | TEXT | |
| `definition` | TEXT | |
| `example` | JSONB | 例句 |
| PK | (course_id, lesson_id, word, definition) | |

## 表关系图

```
users
  └──< user_courses >── courses
  └──< user_progress_of_lessons (course_id, user_id)
  └──< user_progress_of_language_items (item_id, user_id)
  └──< review_logs

courses
  └──< lessons
  └──< language_items
          └── answer_embeddings (answer_embedding_id)

vocabulary_knowledge (独立缓存，按 course_id+lesson_id+word 索引)
```

## 索引

```sql
-- 核心唯一索引
CREATE UNIQUE INDEX user_progress_language_items_user_item_uidx
  ON user_progress_of_language_items (user_id, item_id);

-- 复习日志索引
CREATE INDEX review_logs_user_item_time_idx
  ON review_logs (user_id, item_id, review_time DESC);
CREATE INDEX review_logs_user_course_lesson_time_idx
  ON review_logs (user_id, course_id, lesson_id, review_time DESC);
```
