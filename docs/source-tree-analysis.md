---
title: 源码目录树 — Chilan
generated: 2026-06-17
---

# 源码目录树（含注释）

## 顶层结构

```
Chilan/                         # 项目根目录
├── frontend/                   # React SPA（Vite 构建）
├── backend/                    # FastAPI 后端服务
├── docs/                       # 项目文档（本目录，AI Agent 知识库）
├── .github/workflows/          # CI/CD 工作流
├── CLAUDE.md                   # Claude Code 项目指令
├── AGENTS.md                   # 多 Agent 协作说明
└── README.md                   # 项目简介
```

## 前端：`frontend/`

```
frontend/
├── src/
│   ├── main.jsx                # 应用入口，挂载 React + i18n + QueryClient
│   ├── App.jsx                 # 路由配置，含 ProtectedRoute（JWT 校验）
│   ├── index.css               # TailwindCSS v4 @import + CSS 变量
│   ├── i18n.js                 # 多语言翻译配置（10+ 语言）
│   ├── api/
│   │   ├── apiClient.js        # Axios 实例（401 拦截 → /auth 跳转）
│   │   └── queries.js          # TanStack Query v5：queryKeys 工厂 + query 定义
│   ├── components/
│   │   └── Navbar.jsx          # 顶部导航栏（全局）
│   ├── pages/
│   │   ├── Home.jsx            # 首页
│   │   ├── Classroom.jsx       # 课程教室（选课、进度、统计）← 核心页面
│   │   ├── CoursePage.jsx      # 课程详情页
│   │   ├── auth/               # 认证模块（登录/注册/OAuth）
│   │   │   ├── index.jsx
│   │   │   ├── hooks/useAuthFlow.js
│   │   │   └── components/     # AuthRequirement, AuthSocialSection, AuthSuccessState
│   │   ├── studyPage/          # 学习核心模块 ← 最重要
│   │   │   ├── index.jsx       # 学习流编排器（teaching → practice → 完成）
│   │   │   ├── teaching/       # 讲解模式
│   │   │   │   ├── index.jsx
│   │   │   │   ├── hooks/useTeachingAudio.js
│   │   │   │   └── components/
│   │   │   │       ├── LessonReference.jsx     # 课文参考
│   │   │   │       ├── VocabularySection.jsx   # 词汇展示
│   │   │   │       ├── DialogueSection.jsx     # 对话音频播放
│   │   │   │       ├── LessonSlideDeckPlayer.jsx # 静态幻灯片播放器
│   │   │   │       ├── ChineseLessonReference.jsx
│   │   │   │       └── JapaneseLessonReference.jsx
│   │   │   ├── practice/       # 练习模式
│   │   │   │   ├── PracticeSection.jsx         # 练习流程主控
│   │   │   │   ├── hooks/
│   │   │   │   │   ├── usePracticeFlow.js      # 题目推进、答案评判调用
│   │   │   │   │   ├── useSpeechPractice.js    # 语音录制与 ASR 提交
│   │   │   │   │   ├── usePracticeKnowledgeDetails.js
│   │   │   │   │   └── usePracticeKeyboardShortcuts.js
│   │   │   │   ├── components/
│   │   │   │   │   ├── PracticeAnswerPanel.jsx     # 答题区域总控
│   │   │   │   │   ├── TextAnswerPanel.jsx         # 文字输入
│   │   │   │   │   ├── SpeechAnswerPanel.jsx       # 语音录制 UI
│   │   │   │   │   ├── PracticeFeedbackPanel.jsx   # 三层评估反馈展示
│   │   │   │   │   ├── PracticePromptCard.jsx      # 题目卡
│   │   │   │   │   ├── AIThinkingIndicator.jsx     # LLM 思考动画
│   │   │   │   │   └── WordContextCard.jsx         # 词语上下文
│   │   │   │   ├── utils/langDetect.js
│   │   │   │   └── questionTypeConfig.js          # 各题型配置映射
│   │   │   ├── english/
│   │   │   │   └── NewConceptTeachingSection.jsx   # 新概念英语专用讲解
│   │   │   ├── FinishCard.jsx                      # 课程完成卡
│   │   │   ├── PinyinPopover.jsx                   # 拼音参考弹窗
│   │   │   └── components/
│   │   │       └── AnnotatedSentence.jsx           # 带拼音注释的句子
│   │   ├── personalSetting/    # 用户设置（头像、密码、账户删除）
│   │   ├── Learning_Overview.jsx   # 学习概览统计
│   │   ├── PinyinPage.jsx          # 拼音学习页
│   │   ├── CourseIntroPage.jsx     # 课程介绍页（含 Remotion 视频）
│   │   ├── HanziIntroPage.jsx      # 汉字介绍页
│   │   ├── TypingIntroPage.jsx     # 打字练习入门页
│   │   ├── DevTools.jsx            # 开发者工具入口
│   │   ├── CourseMaintenance.jsx   # 课程重置维护（开发者）
│   │   ├── CourseSync.jsx          # 课程同步面板（开发者）
│   │   ├── ContentBuilderConsole.jsx # 内容构建控制台（开发者）
│   │   └── LocalTeachingPreview.jsx  # 本地讲义预览（开发者）
│   ├── utils/
│   │   ├── authStorage.js      # JWT localStorage 读写（getValidToken, getAuthState）
│   │   ├── audioPlayback.js    # 音频播放工具函数
│   │   ├── lessonNormalizer.js # Lesson JSON 格式标准化
│   │   └── languageOptions.js  # 语言选项配置
│   ├── videoTemplates/         # Remotion 视频模板（解说视频）
│   │   ├── explanation/        # 黑板风格讲解视频系列
│   │   │   ├── BlackboardShell.jsx
│   │   │   ├── LineFocusTemplate.jsx
│   │   │   ├── VocabSpotlightTemplate.jsx
│   │   │   ├── GrammarPatternTemplate.jsx
│   │   │   ├── GrammarTableTemplate.jsx
│   │   │   ├── PinyinGridTemplate.jsx
│   │   │   ├── PinyinTonesTemplate.jsx
│   │   │   ├── LessonRecapTemplate.jsx
│   │   │   ├── UsageFocusTemplate.jsx
│   │   │   ├── JapaneseLineFocusTemplate.jsx  # 日语专用
│   │   │   ├── JapaneseSentenceTemplate.jsx
│   │   │   ├── JapaneseVocabTemplate.jsx
│   │   │   ├── JapaneseGrammarTemplate.jsx
│   │   │   ├── ExplanationSegmentTemplate.jsx # 通用 segment 容器
│   │   │   └── SubtitleBar.jsx                # 字幕条
│   │   └── courseIntro/
│   │       └── CourseIntroVideo.jsx           # 课程介绍视频
│   └── assets/
│       └── patterns.js         # 背景装饰图案
├── remotion/                   # Remotion 入口配置
├── scripts/                    # 构建辅助脚本
├── public/                     # 静态资源（音频等）
├── index.html                  # HTML 入口
├── vite.config.js              # Vite 配置（代码分割 vendor chunks）
├── postcss.config.js           # PostCSS（@tailwindcss/postcss）
├── eslint.config.js            # ESLint v9 flat config
└── package.json                # 依赖清单
```

## 后端：`backend/`

```
backend/
├── main.py                     # FastAPI 应用入口 + 路由注册 + 课程管理 API
├── routers/
│   ├── auth.py                 # 认证路由（/auth/*）：邮件验证/Google/Apple OAuth/JWT
│   └── study.py                # 学习核心路由（/study/*）：三层评估/TTS/ASR/进度
├── services/
│   ├── study/
│   │   ├── evaluator_service.py  # StudyEvaluator：三层评估逻辑
│   │   ├── scheduler.py          # FSRSScheduler：间隔复习算法
│   │   ├── init_flow_service.py  # 初始化学习流（决定 teaching/practice/review 模式）
│   │   └── lesson_progress_service.py # 课时进度持久化
│   ├── llm/
│   │   ├── base_engine.py        # LLMEngine：Gemini API 封装（支持 Vertex AI）
│   │   ├── prompts.py            # 评估 prompt 模板（15+ 题型，动态生成多语言版本）
│   │   └── tools.py              # LanguageTools：embedding + judge_with_ai
│   ├── speech/
│   │   └── asr_service.py        # ASRService：Whisper 语音识别
│   ├── storage/
│   │   ├── media_storage.py      # 工厂函数：get_media_storage() → R2Storage
│   │   ├── r2_storage.py         # R2Storage：Cloudflare R2（S3 兼容，boto3）
│   │   └── tencent_cos_storage.py # TencentCOS：旧版腾讯云存储（已弃用）
│   ├── maintenance/
│   │   ├── course_reset.py       # 课程数据重置工具
│   │   ├── course_sync.py        # 课程同步工具
│   │   └── content_builder_runner.py # 内容构建 Runner
│   ├── course_enrollment_service.py  # 课程报名业务常量与逻辑
│   ├── media_pipeline_registry.py    # Pipeline 注册表（integrated_chinese/minna_no_nihongo 等）
│   └── utils/monitor.py             # PerformanceMonitor（各 Tier 耗时记录）
├── database/
│   ├── connection.py           # PostgreSQL 连接池（psycopg2，支持本地/云端切换）
│   ├── sync_to_db.py           # 内容同步主脚本（中文课程）
│   ├── sync_to_db_ja.py        # 日语课程同步
│   ├── utils.py                # 密码哈希、JWT 生成（PyJWT）
│   └── init_cloud_schema.py    # 初始化云端 DB Schema
├── config/
│   └── env.py                  # 环境变量辅助函数（get_env/get_env_int/get_env_bool）
├── content_builder/            # 离线内容生成流水线（非 API）
│   ├── core/
│   │   ├── lesson_schema.py    # Lesson JSON 数据结构定义
│   │   ├── llm_providers.py    # 多 LLM 供应商工厂
│   │   ├── pipeline.py         # 流水线基类
│   │   └── paths.py            # 路径约定
│   ├── zh/integrated_chinese/  # 中文综合中文流水线
│   ├── en/new_concept_english/ # 新概念英语流水线
│   └── ja/minna_no_nihongo/    # 日语大家的日本语流水线
├── tests/                      # pytest 测试套件
│   ├── test_evaluator_unit.py
│   ├── test_scheduler_unit.py
│   ├── test_study_evaluate.py
│   ├── test_auth_login.py
│   └── ...（其他集成测试）
└── requirements.txt            # Python 依赖
```

## 关键集成点

| 文件 | 方向 | 说明 |
|------|------|------|
| `frontend/src/api/apiClient.js` | → backend | 所有 HTTP 请求的统一出口 |
| `backend/routers/study.py` L438 | ← frontend | `POST /study/evaluate` 三层评估入口 |
| `backend/services/study/evaluator_service.py` | 内部 | 三层评估核心逻辑 |
| `backend/services/llm/base_engine.py` | → Gemini API | LLM 推理封装 |
| `backend/services/storage/r2_storage.py` | → Cloudflare R2 | 媒体文件上传/签名 URL |
| `backend/database/connection.py` | → Neon PostgreSQL | 连接池管理 |
