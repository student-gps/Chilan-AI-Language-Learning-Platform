---
title: 架构文档 — 前端（frontend）
generated: 2026-06-17
part: frontend
---

# 架构文档 — 前端

## 技术栈

| 类别 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 框架 | React | 19.x | Hooks-only，无 Class Component |
| 构建 | Vite | 7.x | HMR + 代码分割 |
| 样式 | TailwindCSS | v4（PostCSS 插件模式）| 无 tailwind.config.js；用 `@import "tailwindcss"` |
| 路由 | React Router | v7 | `useNavigate`/`<Routes>`/`element=` |
| 数据请求 | TanStack Query | v5 | object API，无 onSuccess/onError |
| 动画 | Framer Motion | v12 | AnimatePresence + motion |
| 国际化 | i18next + react-i18next | v25/v16 | 10+ 种语言 |
| 视频渲染 | Remotion | v4 | 讲解视频离线渲染 |
| HTTP 客户端 | Axios | v1.x | 统一拦截器 |
| 图标 | Lucide React | latest | |
| 代码规范 | ESLint | v9 flat config | `eslint.config.js` 数组格式 |
| 语言 | JavaScript/JSX | — | **无 TypeScript** |

## 架构模式

**单页应用（SPA）+ 组件化 + 路由懒加载**

- 所有页面组件通过 `React.lazy` 懒加载
- `ProtectedRoute` 守卫（从 localStorage 读取 JWT 有效性）
- 全局状态：TanStack Query 缓存 + 本地 useState（无全局 Redux/Zustand）
- 国际化：i18n 实例统一管理，`useTranslation()` hook 访问

## 路由结构

```
/                       → Home（公开）
/auth                   → Auth（登录/注册/OAuth）
/classroom              → Classroom（需登录）
/study/:courseId        → StudyPage（核心学习流，需登录）
/overview               → Learning_Overview（需登录）
/settings               → Personal_Setting（需登录）
/course/:courseId       → CoursePage（需登录）
/learn/pinyin           → PinyinPage（需登录）
/learn/intro            → CourseIntroPage（需登录）
/learn/hanzi            → HanziIntroPage（需登录）
/learn/typing           → TypingIntroPage（需登录）
/dev                    → DevTools（无守卫）
/dev/teaching-preview   → LocalTeachingPreview
/dev/course-maintenance → CourseMaintenance
/dev/course-sync        → CourseSync
/dev/content-builder    → ContentBuilderConsole
```

## 核心学习流：StudyPage（`pages/studyPage/index.jsx`）

```
mode 状态机：
loading → teaching / practice / review / completed / lesson_finished / error / not_enrolled

teaching（讲解）：
  - 根据 pipeline_id 选择 TeachingSection 或 NewConceptTeachingSection
  - 用户看讲义时后台并发预加载 practice_items
  - onStartPractice() → 同时提交 content_viewed 并等待 practice_items

practice/review（练习）：
  - PracticeSection 管理题目推进
  - POST /study/evaluate → 三层评估 → PracticeFeedbackPanel 展示
  - onAllDone() → POST /study/complete_lesson → mode='lesson_finished'
```

## API 调用规范

所有 HTTP 请求必须通过 `src/api/apiClient.js`（Axios 实例），包含：
- base URL 从 `VITE_APP_API_BASE_URL` 环境变量读取（注意前缀 `VITE_APP_`）
- 401 拦截器自动跳转到 `/auth`

所有查询定义集中在 `src/api/queries.js`：
```js
// 正确：从 queries.js 取 queryKey
import { queryKeys, myCoursesQuery } from '../api/queries';
useQuery({ ...myCoursesQuery(userId) })

// 错误：内联写死 queryKey
useQuery({ queryKey: ['my-courses', userId], queryFn: ... })
```

## 国际化（i18n）

- 翻译键定义在 `src/i18n.js`
- UI 文字必须通过 `useTranslation()` hook
- 支持语言：中文(zh)、英文(en)、日文(ja)、法文(fr)、德文(de)、韩文(ko)、俄文(ru)、西班牙文(es)、葡萄牙文(pt)、越南文(vi)、泰文(th)

## Remotion 视频模板（`src/videoTemplates/`）

| 模板 | 用途 |
|------|------|
| `BlackboardShell.jsx` | 黑板外壳容器 |
| `LineFocusTemplate.jsx` | 逐行对话高亮（中文） |
| `VocabSpotlightTemplate.jsx` | 词汇聚焦 |
| `GrammarPatternTemplate.jsx` | 语法句型 |
| `GrammarTableTemplate.jsx` | 语法对照表 |
| `PinyinGridTemplate.jsx` | 拼音音节表 |
| `PinyinTonesTemplate.jsx` | 四声对比 |
| `JapaneseLineFocusTemplate.jsx` | 逐行对话（日语）|
| `JapaneseSentenceTemplate.jsx` | 日语句型 |
| `JapaneseVocabTemplate.jsx` | 日语词汇 |
| `ExplanationSegmentTemplate.jsx` | 通用 segment 容器 |

## 认证流程

1. 邮件注册/Google OAuth/Apple OAuth → 获取 JWT access_token
2. JWT 存入 localStorage（`authStorage.js`）
3. `getValidToken()` 解析 JWT 有效性（前端检查 exp）
4. API 请求时通过 Axios 拦截器自动附带 Authorization header
5. 401 响应 → 自动重定向到 `/auth`

## 构建配置（`vite.config.js`）

手动代码分割 vendor chunks：
- `vendor-react`：React/ReactDOM
- `vendor-router`：React Router v7
- `vendor-i18n`：i18next
- `vendor-motion`：Framer Motion
- `vendor-icons`：Lucide React
- `vendor-remotion`：Remotion
- `vendor-api`：Axios + @react-oauth

## 高频错误预防

- TailwindCSS v4：**无** `tailwind.config.js`，CSS 用 `@import "tailwindcss"`
- 环境变量：`VITE_APP_API_BASE_URL`，**不是** `VITE_API_BASE_URL`
- TanStack Query v5：无 `onSuccess`/`onError`，用 `isPending` 不用 `isLoading`
- React Router v7：`useNavigate`/`<Routes>`/`element=`，**不是** `useHistory`
