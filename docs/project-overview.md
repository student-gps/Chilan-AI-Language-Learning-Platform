---
title: 项目概述 — Chilan
generated: 2026-06-17
---

# Chilan 项目概述

## 是什么

Chilan 是一个 AI 驱动的语言学习平台，支持中文、英文、日文等多语言课程。核心创新是**三层答案评估系统**，解决传统系统把语义等价答案错判为错误的问题。

## 技术架构分类

| 维度 | 描述 |
|------|------|
| 仓库类型 | 多部分（Multi-part）：`frontend/` + `backend/` |
| 主要语言 | JavaScript（前端）/ Python（后端） |
| 架构模式 | SPA + REST API + Cloud DB |
| 部署目标 | Vercel（前端）+ 独立服务（后端）+ Neon PostgreSQL + Cloudflare R2 |

## 技术栈摘要

### 前端（`frontend/`）
React 19 + Vite 7 + TailwindCSS v4 + React Router v7 + TanStack Query v5 + Framer Motion + i18next + Remotion v4

### 后端（`backend/`）
Python 3.13 + FastAPI + psycopg2（PostgreSQL）+ Gemini 2.0 Flash（LLM）+ VoyageAI/Doubao/Gemini（Embedding）+ Edge TTS + Whisper ASR + boto3（Cloudflare R2）

## 核心功能模块

1. **三层答案评估**：Regex → Embedding 余弦相似度 → LLM 深度分析
2. **FSRS 间隔复习调度器**：基于 stability/difficulty 参数计算下次复习时间
3. **内容构建流水线**：PDF → LLM 提取 → Lesson JSON → TTS 音频 → Remotion 视频 → R2 + PostgreSQL
4. **多语言 UI**：10+ 种 UI 语言（中、英、日、法、德、韩、俄、西、葡、越、泰）
5. **多 LLM 供应商**：Gemini（默认）、Doubao、DeepSeek、Ali Qwen、Zhipu，工厂模式切换

## 课程体系

| 课程 | Pipeline ID | 目标语言 | 源语言 |
|------|-------------|----------|--------|
| Integrated Chinese | `integrated_chinese` | 中文 | 英/法/日/韩/越... |
| New Concept English | `new_concept_english` | 英文 | 中文 |
| Minna no Nihongo | `minna_no_nihongo` | 日文 | 中文 |

## 关键链接

- [架构文档 — 前端](./architecture-frontend.md)
- [架构文档 — 后端](./architecture-backend.md)
- [API 合约](./api-contracts-backend.md)
- [数据模型](./data-models-backend.md)
- [源码目录树](./source-tree-analysis.md)
- [开发指南](./development-guide.md)
- [集成架构](./integration-architecture.md)
- [项目规则（AI Agent 必读）](./project-context.md)
