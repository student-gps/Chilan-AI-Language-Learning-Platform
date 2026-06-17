---
project_name: Chilan
user_name: gaopeng16
date: 2026-06-17
sections_completed:
  - technology_stack
  - architecture_constraints
  - framework_rules
  - code_style
  - directory_conventions
status: complete
optimized_for_llm: true
---

# Project Context for AI Agents

> 本文件供 AI coding agent 阅读。重点是"容易写错的地方"和"禁止做什么"，不是介绍架构。

---

## 技术栈版本

| 层 | 技术 | 版本 |
|----|------|------|
| 前端框架 | React | 19.x |
| 构建工具 | Vite | 7.x |
| 样式 | TailwindCSS | **v4**（PostCSS 插件模式） |
| 路由 | React Router | **v7** |
| 数据请求 | TanStack Query | **v5** |
| 动画 | Framer Motion | v12 |
| 国际化 | i18next + react-i18next | v25 / v16 |
| 视频渲染 | Remotion | v4 |
| 图标 | Lucide React | latest |
| HTTP 客户端 | Axios | v1.x |
| 代码规范 | ESLint | **v9**（flat config） |
| 语言 | **纯 JS/JSX，无 TypeScript** | — |
| 后端框架 | FastAPI | latest |
| 运行时 | Python | **3.13** |
| 数据库驱动 | psycopg2-binary（非 psycopg3） | latest |
| 主 LLM | Gemini 2.0 Flash | via `services/llm/` 工厂 |
| 向量嵌入 | VoyageAI / Doubao / Gemini | 可配置切换 |
| 媒体存储 | Cloudflare R2 | via boto3 |
| TTS | Edge TTS | latest |

---

## 关键架构约束

### 答案评估（三层系统）

绝对不能绕过，前端禁止直接调 LLM 做答案判断。

```
用户答案
  │
  ▼
Tier 1: Regex 精确匹配        → 通过则直接返回正确
  │ 不通过
  ▼
Tier 2: Embedding 语义相似度   → 相似度 > 阈值则返回正确
  │ 不通过
  ▼
Tier 3: LLM 深度分析          → 返回判断 + 详细反馈
```

**入口唯一：** `POST /study/evaluate` → `backend/services/study/evaluator_service.py`

### LLM 调用

- ✅ 必须通过 `backend/services/llm/` 工厂函数
- ❌ 禁止在 router / service 业务代码里直接实例化 `genai.GenerativeModel()` 等 SDK 客户端
- 默认 provider：Gemini 2.0 Flash；其他 provider 通过环境变量切换

### 媒体文件

- ✅ 媒体文件存 Cloudflare R2，通过 `get_media_storage()` 工厂获取实例
- ❌ 禁止用本地文件系统存媒体
- ❌ 禁止用 `FileResponse` 直接返回媒体内容

### API 请求（前端）

- ✅ 所有 HTTP 请求必须通过 `frontend/src/api/apiClient.js`（已含 401 自动跳转拦截器）
- ❌ 禁止在组件里裸调 `axios.create()` 或 `fetch()`

---

## 容易写错的规则（AI 高频错误）

### TailwindCSS v4 ← 最高风险

❌ **禁止生成：**
```js
// tailwind.config.js — v4 中不存在这个文件
module.exports = { content: [...], theme: { extend: {} } }
```
```css
/* 禁止 v3 指令 */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

✅ **正确写法：**
```css
/* frontend/src/index.css */
@import "tailwindcss";
/* 自定义 token 用 CSS 变量 */
@theme { --color-brand: #3b82f6; }
```

PostCSS 配置用 `@tailwindcss/postcss`，不是旧版 `tailwindcss` PostCSS plugin。

---

### Vite 环境变量前缀

❌ `import.meta.env.VITE_API_BASE_URL`  
✅ `import.meta.env.VITE_APP_API_BASE_URL`

---

### TanStack Query v5

❌ **禁止 v4 位置参数写法：**
```js
useQuery(['lessons', id], fetchLesson)
useQuery({ queryKey: [...], queryFn: fetch, onSuccess: (d) => {} })
```

✅ **正确写法：**
```js
useQuery({ queryKey: ['lessons', id], queryFn: () => fetchLesson(id) })
// 副作用用 useEffect 监听 data，不用 onSuccess
```

- `onSuccess` / `onError` 已从 `useQuery` 移除，用 `useEffect`
- 首次加载判断用 `isPending`，不是 `isLoading`

---

### QueryKey 工厂

❌ 组件里内联 `queryKey: ['user-lessons']`  
✅ 从 `frontend/src/api/queries.js` 的 `queryKeys` 工厂取：
```js
import { queryKeys } from '../api/queries';
useQuery({ queryKey: queryKeys.lessons(courseId), queryFn: ... })
```

---

### React Router v7

❌ 禁止：`useHistory`、`<Switch>`、`component=` prop  
✅ 使用：`useNavigate`、`<Routes>`、`element=` prop

---

### ESLint v9 Flat Config

❌ 禁止生成 `.eslintrc.json` / `.eslintrc.js`  
✅ 配置文件是 `frontend/eslint.config.js`，格式为数组导出：
```js
export default [ { rules: { ... } } ]
```

---

### 无 TypeScript

- ✅ 前端所有文件后缀 `.js` 或 `.jsx`
- ❌ 禁止 `.ts` / `.tsx` / 类型注解 / `interface` / `as Type`
- ❌ 禁止 `PropTypes`（项目未使用）
- 文件命名：React 组件用 `PascalCase.jsx`，hooks 用 `useCamelCase.js`，工具函数用 `camelCase.js`

---

### Python 3.13 类型注解

❌ `from typing import List, Dict, Optional`  
✅ 内置泛型语法：
```python
def foo(items: list[str]) -> dict | None: ...
```

---

### 数据库驱动

- ✅ 继续使用 `psycopg2-binary`（v2）
- ❌ 禁止建议迁移到 `psycopg`（psycopg3），两者 API 不兼容

---

### JWT 双库职责

项目同时使用两个 JWT 库，职责不同：
- `python-jose`：解析 Google / Apple OAuth token
- `PyJWT`：生成和验证项目内部 JWT

生成新的认证相关代码时，按现有 `backend/routers/auth.py` 的模式选用，不要混用或"统一"。

---

## 代码风格

- 注释语言：中文
- ESLint `no-unused-vars` 例外：大写开头的变量名（组件、常量）和 `motion` 变量不报错；函数参数以 `_` 开头不报错
- 国际化：UI 文字必须通过 `useTranslation()` hook，翻译键定义在 `frontend/src/i18n.js`
- API 查询定义统一放在 `frontend/src/api/queries.js`，不要分散在各页面

---

## 目录结构约定

```
frontend/src/
  api/          # apiClient.js + queries.js，所有 HTTP 和查询定义
  pages/        # 按功能模块分目录，每个模块下有 hooks/ components/ utils/
  videoTemplates/  # Remotion 视频组件
  utils/        # 通用工具函数
  i18n.js       # 国际化翻译

backend/
  routers/      # FastAPI 路由层，只做请求解析和响应格式化
  services/     # 业务逻辑层（study/, llm/, speech/, storage/）
  database/     # DB 连接和同步脚本
  content_builder/  # 离线内容生成流水线，不是 API
  config/env.py # 所有环境变量通过 get_env() 读取
```

---

## 使用说明

**AI Agent 读本文件时：**
- 实现任何功能前先读这个文件
- 所有 ❌ 规则是硬约束，不是建议
- 遇到不确定的地方，选限制更严的那个

**Human 维护本文件时：**
- 只记录"不明显"的规则，AI 本来就知道的不用写
- 技术栈版本升级时同步更新
- 规则变得"理所当然"之后可以删掉

_Last updated: 2026-06-17_
