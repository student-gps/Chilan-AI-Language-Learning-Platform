---
title: 组件清单 — 前端（frontend）
generated: 2026-06-17
part: frontend
---

# 前端组件清单

> 本文档仅记录 `src/` 下有意义的组件，省略样板文件。

---

## 页面（`src/pages/`）

| 文件 | 路由 | 功能摘要 |
|------|------|----------|
| `Home.jsx` | `/` | 首页（公开） |
| `auth/index.jsx` | `/auth` | 登录/注册/OAuth 入口 |
| `Classroom.jsx` | `/classroom` | 课程教室（选课、进度、统计）|
| `CoursePage.jsx` | `/course/:courseId` | 课程详情页 |
| `studyPage/index.jsx` | `/study/:courseId` | 学习流主页（状态机驱动）|
| `Learning_Overview.jsx` | `/overview` | 学习概览统计 |
| `personalSetting/index.jsx` | `/settings` | 用户设置（头像/密码/账户）|
| `PinyinPage.jsx` | `/learn/pinyin` | 拼音学习 |
| `CourseIntroPage.jsx` | `/learn/intro` | 课程介绍页（含视频）|
| `HanziIntroPage.jsx` | `/learn/hanzi` | 汉字介绍 |
| `TypingIntroPage.jsx` | `/learn/typing` | 打字练习入门 |
| `DevTools.jsx` | `/dev` | 开发者工具入口 |
| `CourseMaintenance.jsx` | `/dev/course-maintenance` | 课程重置维护（开发者）|
| `CourseSync.jsx` | `/dev/course-sync` | 课程同步面板（开发者）|
| `ContentBuilderConsole.jsx` | `/dev/content-builder` | 内容构建控制台（开发者）|
| `LocalTeachingPreview.jsx` | `/dev/teaching-preview` | 本地讲义预览（开发者）|

---

## 学习流组件（`src/pages/studyPage/`）

### 学习流编排器

#### `studyPage/index.jsx`
学习会话主状态机，串联 teaching → practice → 完成 整个流程。

**核心状态：**
```js
mode: 'loading' | 'teaching' | 'practice' | 'review' | 'completed' | 'lesson_finished' | 'error' | 'not_enrolled'
studyData        // 课时内容 + 练习题
courseInfo       // 课程元信息
practiceItemsPromiseRef  // 后台预加载的练习题 Promise
```

**关键流程：**
- `initFlow()` → GET `/study/init`
- `handleStartPractice()` → 并发提交 content_viewed + 等待 practice_items
- `handleLessonComplete()` → POST `/study/complete_lesson`

---

### 讲解模式（`teaching/`）

#### `teaching/index.jsx`
讲解模式总控，管理音频播放器、幻灯片、词汇/对话切换。

**Props:** `data`, `courseInfo`, `courseId`, `userId`, `onStartPractice`, `canStartPractice`, `hasPracticeItems`

**核心 State:** `diagPinyin/diagTrans`（对话显示开关）、`vocabPinyin/vocabTrans`（词汇显示开关）

---

#### `teaching/components/LessonReference.jsx`
语言检测路由：根据 `inferLessonReferenceLanguage()` 自动选择 `ChineseLessonReference` 或 `JapaneseLessonReference`。

**导出函数：** `inferLessonReferenceLanguage({data, courseContent, lessonMetadata, courseInfo, courseId, targetLanguage})`

---

#### `teaching/components/ChineseLessonReference.jsx`
中文课时内容布局：对话行 + 词汇表，含拼音/翻译叠加层控制。

**Props:** `lineItems`, `vocabulary`, `diagPinyin/diagTrans`, `vocabPinyin/vocabTrans`, `playDialogueAudio`, `playTtsFallback`

---

#### `teaching/components/JapaneseLessonReference.jsx`
日语课时内容布局：句型、例句（带注释）、对话、词汇（含汉字分解）、练习预览。

**Props:** `courseContent`, `lessonMetadata`, `playingKey`, `playTextAudio`

---

#### `teaching/components/LessonSlideDeckPlayer.jsx`
幻灯片播放器：16:9 图片 + 同步字幕 + 进度条 + 速度控制 + 全屏。

**Props:** `deck`（含 slides 数组，每张含 image/audio/duration_ms/caption_cues）, `apiBase`

**核心 State:** `index`（当前幻灯片）, `playing`, `localMs`（幻灯片内播放位置）, `rate`, `fullscreen`

---

#### `teaching/components/DialogueSection.jsx`
对话显示区：逐行展示说话人+内容，支持拼音叠加、翻译叠加、音频播放。

**Props:** `lineItems`, `playDialogueAudio`, `diagPinyin/setDiagPinyin`, `diagTrans/setDiagTrans`

---

#### `teaching/components/VocabularySection.jsx`
词汇表：word/拼音/词性/释义/翻译，每行可切换拼音/翻译显示，支持 TTS 播放。

**Props:** `vocabulary`, `vocabPinyin`, `vocabTrans`, `playTtsFallback`, `targetLanguage`

---

### 练习模式（`practice/`）

#### `practice/PracticeSection.jsx`
练习流程主控，管理当前题目推进、评估调用、反馈显示、键盘快捷键。

**Props:** `questions`, `isReview`, `onAllDone`, `userId`, `courseId`, `lessonId`, `lessonAudioAssets`, `initialIndex`

**核心 Hooks 组合：** `usePracticeFlow` + `useSpeechPractice` + `usePracticeKeyboardShortcuts` + `usePracticeKnowledgeDetails`

---

#### `practice/components/PracticeAnswerPanel.jsx`
答题区调度器：根据 speechMode 分发到 `TextAnswerPanel` 或 `SpeechAnswerPanel`。

---

#### `practice/components/TextAnswerPanel.jsx`
文字输入答题区。

**Props:** `value`, `inputRef`, `onChange`, `onFocus/onBlur`, `placeholder`, `disabled`, `isFocused`, `statusTone`

---

#### `practice/components/SpeechAnswerPanel.jsx`
语音录制答题区：实时波形可视化 + 录音计时器 + 转写预览 + 录制/提交双按钮。

**Props:** `isRecording`, `isTranscribing`, `liveWaveform`, `speechPreviewText`, `speechInlineHint`, `onPrimaryAction`, `onSubmit`, `primaryLabel`, `showSubmit`

---

#### `practice/components/PracticePromptCard.jsx`
题目卡展示：听写题显示大型播放按钮，其他题型显示文字 + 可选音频重播。

**Props:** `originalText`, `questionType`, `currentQuestion`, `promptLabel`, `onPlayAudio`

---

#### `practice/components/PracticeFeedbackPanel.jsx`
评估反馈展示：标准答案 + AI 反馈消息（打字机动画）+ ASR 识别结果 + 重试/跳过/下一题按钮 + 词语上下文卡。

**Props:** `feedback`（含 level/message/recognizedText/forfeited）, `currentQuestion`, `knowledgeDetails`, `onRetry/onSkip/onNext`

**逻辑：** level=1 → 显示重试；level≥2 → 显示下一题

---

#### `practice/components/AIThinkingIndicator.jsx`
LLM 分析中动画：闪烁图标 + 跳动点 + 边框脉冲。

**Props:** `label?`（自定义提示文字）

---

#### `practice/components/WordContextCard.jsx`
词语上下文卡：释义 + 例句（可切换拼音/翻译叠加层）+ 其他词义。支持中文/日文（`targetLanguage` 参数）。

**Props:** `word`, `pinyin`, `metadata`, `knowledgeData`（含 current_sense/other_senses）, `targetLanguage`

---

#### `practice/hooks/usePracticeFlow.js`
练习主 Hook：题目推进逻辑、答案提交、评估调用（POST `/study/evaluate`）、FSRS 反馈处理。

---

#### `practice/hooks/useSpeechPractice.js`
语音练习 Hook：MediaRecorder 录音控制、实时波形采样、POST `/study/speech/transcribe` 提交、置信度判断。

---

#### `practice/hooks/usePracticeKnowledgeDetails.js`
按需加载词语知识 Hook：GET `/study/knowledge` + 结果缓存。

---

#### `practice/hooks/usePracticeKeyboardShortcuts.js`
键盘快捷键 Hook：Enter 提交、Escape 跳过、空格重播音频等。

---

#### `practice/utils/langDetect.js`
语言检测工具：判断输入字符所属语言（用于自动切换输入模式）。

---

#### `practice/questionTypeConfig.js`
各题型配置映射：`questionType → { inputType, promptLabel, placeholder, speechConfig, ... }`

---

### 其他子组件

#### `studyPage/FinishCard.jsx`
课程完成卡：庆祝动画 + 学习统计 + 下一课程入口。

#### `studyPage/PinyinPopover.jsx`
拼音参考弹窗：全部声母/韵母/声调快查表。

#### `studyPage/components/AnnotatedSentence.jsx`
带拼音注释的句子：汉字上方显示拼音（Ruby 注音风格）。

---

### 新概念英语专用

#### `studyPage/english/NewConceptTeachingSection.jsx`
新概念英语讲解模式：替代标准 TeachingSection，针对英语课时优化的 UI 布局。

---

## 全局组件（`src/components/`）

#### `components/Navbar.jsx`
顶部导航栏：Logo + 路由导航 + 用户头像/登出 + 语言切换。

---

## 工具函数（`src/utils/`）

#### `utils/authStorage.js`
JWT localStorage 管理。

**导出：**
```js
clearAuthStorage()                          // 清除所有 auth 键
isTokenExpired(token, skewSeconds=30)       // JWT exp 检查
getValidToken()                             // 返回有效 token 或 null
getAuthState()                              // { token, isLoggedIn, userId, userEmail }
```

#### `utils/audioPlayback.js`
音频播放工具：全局音频互斥（claimGlobalAudio / releaseGlobalAudio），避免多音频并发。

#### `utils/lessonNormalizer.js`
Lesson JSON 格式标准化：兼容不同版本的 lesson 数据结构。

#### `utils/languageOptions.js`
语言选项配置：语言代码 → 显示名称、flag emoji、TTS 语音名称映射。

---

## API 层（`src/api/`）

#### `api/apiClient.js`
Axios 实例：`baseURL = VITE_APP_API_BASE_URL`，401 拦截 → 清除 auth → 跳转 `/auth`。

#### `api/queries.js`
TanStack Query v5 查询定义。

**导出的 queryKey 工厂：**
```js
queryKeys.courses()
queryKeys.course(courseId)
queryKeys.lessons(courseId)
queryKeys.myCourses(userId)
queryKeys.classroomStats(userId)
```

**导出的查询定义函数：**
```js
coursesQuery()          // GET /courses，staleTime: 10min
courseQuery(courseId)   // GET /courses/:id，staleTime: 10min
lessonsQuery(courseId)  // GET /courses/:id/lessons，staleTime: 10min
myCoursesQuery(userId)  // GET /my-courses/:userId，staleTime: 1min
overviewStatsQuery(uid) // GET /overview/stats/:uid，staleTime: 1min
classroomStatsQuery(uid)// GET /classroom/stats/:uid，staleTime: 30s
```

---

## Remotion 视频模板（`src/videoTemplates/`）

### 讲解视频系列（`explanation/`）

| 组件 | 用途 |
|------|------|
| `BlackboardShell.jsx` | 黑板风格外壳容器（所有讲解视频的根布局）|
| `ExplanationSegmentTemplate.jsx` | 通用 segment 容器（从 video_render_plan 的 scene 渲染）|
| `LineFocusTemplate.jsx` | 逐行对话高亮（中文）|
| `VocabSpotlightTemplate.jsx` | 词汇聚焦展示 |
| `GrammarPatternTemplate.jsx` | 语法句型讲解 |
| `GrammarTableTemplate.jsx` | 语法对照表 |
| `PinyinGridTemplate.jsx` | 拼音音节表 |
| `PinyinTonesTemplate.jsx` | 四声对比 |
| `LessonRecapTemplate.jsx` | 课时总结 |
| `UsageFocusTemplate.jsx` | 用法专项讲解 |
| `JapaneseLineFocusTemplate.jsx` | 逐行对话高亮（日语）|
| `JapaneseSentenceTemplate.jsx` | 日语句型 |
| `JapaneseVocabTemplate.jsx` | 日语词汇 |
| `JapaneseGrammarTemplate.jsx` | 日语语法 |
| `SubtitleBar.jsx` | 视频字幕条 |

### 课程介绍视频（`courseIntro/`）

| 组件 | 用途 |
|------|------|
| `CourseIntroVideo.jsx` | 课程介绍视频（在 CourseIntroPage 中播放）|
