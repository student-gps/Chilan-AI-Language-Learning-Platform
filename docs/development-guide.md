---
title: 开发指南
generated: 2026-06-17
---

# 开发指南

## 环境要求

| 工具 | 版本 | 说明 |
|------|------|------|
| Node.js | 20+ | 前端构建/开发 |
| Python | 3.13 | 后端运行时（使用 `list[str]` 等内置泛型）|
| PostgreSQL | 15+ | 本地开发可选（或直接连 Neon Cloud）|
| ffmpeg | 任意 | 仅内容构建流水线的视频渲染需要 |

---

## 后端快速启动

```bash
cd backend

# 安装依赖
pip install -r requirements.txt   # 或: pipenv install

# 创建并填写 backend/.env（仓库当前未提交 .env.example；参考下方环境变量清单）

# 启动开发服务器（热重载，端口 8000）
python main.py
```

**验证：** 访问 `http://localhost:8000/health` → `{ "status": "ok" }`

### 后端 `.env` 必填变量

```bash
# 数据库
APP_DATABASE_URL=postgresql://user:pass@neon-host/dbname?sslmode=require
DB_MODE=cloud              # 或 local（用 APP_DATABASE_URL_LOCAL）

# LLM（评估）
LLM_JUDGE_PROVIDER=gemini
LLM_JUDGE_GEMINI_API_KEY=...
LLM_JUDGE_GEMINI_MODEL_ID=gemini-2.5-flash

# Embedding（当前代码路径支持 gemini / doubao）
LLM_EMBED_PROVIDER=gemini         # 或 doubao
LLM_EMBED_GEMINI_API_KEY=...
# LLM_EMBED_DOUBAO_API_KEY=...
# LLM_EMBED_DOUBAO_MODEL_ID=...

# ASR（OpenAI Whisper API 兼容）
ASR_PROVIDER=openai
ASR_OPENAI_API_KEY=...            # 或复用 LLM_OPENAI_API_KEY

# 媒体存储（Cloudflare R2）
STORAGE_R2_ACCOUNT_ID=...
STORAGE_R2_ACCESS_KEY_ID=...
STORAGE_R2_SECRET_ACCESS_KEY=...
STORAGE_R2_BUCKET=...
STORAGE_R2_PUBLIC_BASE_URL=...    # 可选（使用公开 URL 时填写）

# JWT
SECURITY_JWT_SECRET=...               # 任意随机字符串

# 邮件
MAIL_PROVIDER=smtp               # 或 resend
MAIL_SMTP_SERVER=... MAIL_SMTP_PORT=587 MAIL_SMTP_USERNAME=... MAIL_SMTP_PASSWORD=...
MAIL_SMTP_FROM=...               # 发件地址

# CORS（本地开发可不填，localhost:5173 已内置）
APP_CORS_ORIGINS=                 # 逗号分隔的额外来源
```

**可选变量：**
```bash
LLM_JUDGE_GEMINI_USE_VERTEX=false   # Vertex AI 模式
APP_DATABASE_URL_LOCAL=...          # 本地 DB URL
DB_POOL_MIN=1 DB_POOL_MAX=5         # 连接池大小
```

---

## 前端快速启动

```bash
cd frontend

npm install

# 启动开发服务器（端口 5173，热重载）
npm run dev
```

**验证：** 访问 `http://localhost:5173` → 首页正常加载

### 前端环境变量

```bash
# frontend/.env.development（已内置，无需修改）
VITE_APP_API_BASE_URL=http://localhost:8000

# frontend/.env.production（填写生产 API 地址）
VITE_APP_API_BASE_URL=https://api.chilanlearning.com
```

**重要：** 变量名必须以 `VITE_APP_` 开头（不是 `VITE_`）。

---

## 数据库初始化

```bash
cd backend

# 初始化云端 Schema（首次部署）
python database/init_cloud_schema.py

# 同步课时内容 JSON → PostgreSQL（中文课程）
python database/sync_to_db.py

# 同步日语课程
python database/sync_to_db_ja.py
```

---

## 内容构建流水线（离线，非 API）

```bash
cd backend

# Step 1：PDF → LLM 提取 → Lesson JSON + 对话音频
# 先将 PDF 放入 content_builder/artifacts/raw_materials/
python content_builder/generate.py

# Step 2：Lesson JSON → TTS 旁白
python content_builder/render_narration.py                            # 处理全部 JSON
python content_builder/render_narration.py artifacts/output_json/lesson101_data.json  # 单文件

# Step 2（含视频渲染）：需要 ffmpeg + Remotion
python content_builder/render_narration.py --render-video
python content_builder/render_narration.py --render-video --lang fr   # 法语学习者版

# Step 3（发布）：上传 R2 + 同步 PostgreSQL
python database/sync_to_db.py
```

---

## 前端命令速查

```bash
npm run dev         # 开发服务器（localhost:5173）
npm run build       # 生产构建 → dist/
npm run lint        # ESLint 检查
npm run video:render 101   # 渲染 lesson 101 的讲解视频（Remotion）
```

---

## 测试

### 后端（pytest）

```bash
cd backend

# 全部测试
pytest

# 单文件
pytest tests/test_evaluator_unit.py -v

# 单测试
pytest tests/test_study_evaluate.py::test_correct_answer -v
```

**测试文件：**
- `tests/test_evaluator_unit.py` — StudyEvaluator 单元测试
- `tests/test_scheduler_unit.py` — FSRSScheduler 单元测试
- `tests/test_study_evaluate.py` — `/study/evaluate` 集成测试
- `tests/test_auth_login.py` — 认证集成测试
- `tests/test_minna_no_nihongo_pipeline.py` — 日语流水线测试

**注意：** 集成测试需连接真实数据库（不 mock DB）。

---

## 开发工具页面

前端内置开发者工具，访问路径：`http://localhost:5173/dev`

| 工具 | 路径 | 说明 |
|------|------|------|
| DevTools | `/dev` | 开发工具入口 |
| CourseSync | `/dev/course-sync` | 课程同步控制台（调用 `/dev/course-sync/*`）|
| CourseMaintenance | `/dev/course-maintenance` | 课程数据重置 |
| ContentBuilderConsole | `/dev/content-builder` | 内容构建（流式输出）|
| LocalTeachingPreview | `/dev/teaching-preview` | 预览未同步的课时 JSON |

---

## 高频陷阱

### TailwindCSS v4
```css
/* 正确 */
@import "tailwindcss";

/* 错误（v3 用法） */
@tailwind base;
@tailwind components;
@tailwind utilities;
```
无 `tailwind.config.js`；用 CSS `@layer` 自定义。

### TanStack Query v5
```js
// 正确
const { data, isPending } = useQuery(myCoursesQuery(userId))
// 错误（v4 用法）
const { data, isLoading, onSuccess } = useQuery(...)
```
无 `onSuccess`/`onError` 回调；改用 `useEffect` 监听 `data`。

### React Router v7
```js
// 正确
import { useNavigate } from 'react-router-dom'
const navigate = useNavigate()

// 错误（v5 用法）
import { useHistory } from 'react-router-dom'
```

### 前端环境变量
```js
// 正确
import.meta.env.VITE_APP_API_BASE_URL

// 错误
import.meta.env.VITE_API_BASE_URL   // 缺少 APP_
process.env.REACT_APP_API_BASE_URL  // CRA 用法
```

### 后端 DB 驱动
```python
# 正确：psycopg2（v2）
import psycopg2

# 错误：不要用 psycopg3 API（asyncpg / asyncio + psycopg）
```

### Python 版本特性
```python
# 正确（Python 3.13 内置泛型）
def func(items: list[str]) -> dict[str, int]:

# 不需要
from typing import List, Dict
```

---

## CI/CD

GitHub Actions 工作流位于 `.github/workflows/`（具体配置参考工作流文件）。
