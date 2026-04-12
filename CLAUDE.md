# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Chilan is an AI-powered Chinese language learning platform. Its core innovation is a **three-tier answer evaluation system**:
1. **Tier 1 (Regex)**: Fast exact/pattern matching
2. **Tier 2 (Vector Similarity)**: Embedding-based semantic comparison
3. **Tier 3 (LLM)**: Deep AI analysis with detailed feedback for genuinely incorrect answers

This solves the problem where semantically equivalent answers (e.g., "What do you usually do?" vs "What do you on usual?") are wrongly marked incorrect by traditional systems.

## Commands

### Backend (FastAPI, Python 3.13)
```bash
cd backend

# Install dependencies
pip install -r requirements.txt   # or: pipenv install

# Run development server (auto-reload on port 8000)
python main.py

# Run content builder pipeline (place PDFs in content_builder/raw_materials/ first)
python content_builder/main.py
python content_builder/main.py --render-explanation-video   # also render videos
```

### Frontend (React + Vite)
```bash
cd frontend

npm install
npm run dev        # Dev server on http://localhost:5173
npm run build      # Production build → dist/
npm run lint       # ESLint
npm run video:render 101   # Render a Remotion explanation video by lesson ID
```

### Database Sync
```bash
cd backend
python database/sync_to_db.py   # Sync lesson JSON files to PostgreSQL
```

## Architecture

### Request Flow
```
React SPA (port 5173) → FastAPI (port 8000) → PostgreSQL (Neon Cloud)
                                            → Tencent COS (media storage)
                                            → LLM/Embedding APIs
                                            → Speech APIs (Whisper ASR, Edge TTS)
```

### Backend Structure (`backend/`)
- **main.py** — FastAPI app, CORS config, route registration, media file serving (`/media/audio`)
- **routers/auth.py** — JWT auth, Google/Apple OAuth, email verification, password reset
- **routers/study.py** — Core study flow: three-tier evaluation (`/study/evaluate`), speech transcription, lesson completion, FSRS progress recording
- **services/study/evaluator_service.py** — The three-tier evaluation engine
- **services/study/scheduler.py** — FSRS (Free Spaced Repetition Scheduler) for review interval calculation
- **services/llm/** — LLM engine (Gemini 2.0 Flash default), embedding providers (Gemini, Doubao, Voyage), evaluation prompts
- **services/speech/asr_service.py** — Whisper-based speech recognition with noise filtering
- **services/storage/tencent_cos_storage.py** — Media file storage with signed URLs
- **database/connection.py** — PostgreSQL connection (Neon Cloud)
- **database/sync_to_db.py** — Syncs lesson JSON → database, creates embeddings
- **config/env.py** — Environment variable helpers (`get_env()`, `get_env_int()`, etc.)
- **content_builder/** — Automated pipeline: PDF → LLM extraction → lesson JSON → DB → optional video render

### Frontend Structure (`frontend/src/`)
- **App.jsx** — React Router config; protected routes require valid JWT in localStorage
- **pages/studyPage/index.jsx** — Study session orchestrator (teaching → practice → completion)
- **pages/studyPage/TeachingSection.jsx** — Vocabulary display, Remotion video, audio playback
- **pages/studyPage/PracticeSection.jsx** — Q&A flow, speech recording, three-tier feedback display
- **pages/Classroom.jsx** — Course dashboard, enrollment, progress overview
- **api/apiClient.js** — Axios client; base URL switches between `localhost:8000` (dev) and production via `.env.development` / `.env.production`
- **i18n.js** — 10+ language UI translations (Chinese, English, Japanese, French, German, Korean, Russian, Spanish, Portuguese, Vietnamese, Thai)
- **videoTemplates/** — Remotion React components for explanation videos

### Key Data Flow: Answer Evaluation
`PracticeSection` → `POST /study/evaluate` → `evaluator_service.py`:
1. Check Tier 1 (regex exact match) → if pass, done
2. Generate embedding for student answer → cosine similarity vs stored embeddings → if above threshold, pass
3. Call LLM with answer + context → parse judgment + explanation → return to frontend

### Content Builder Pipeline
`raw_materials/*.pdf` → LLM text extraction → structured lesson JSON → `sync_to_db.py` embeds vocabulary → Tencent COS stores audio/video → Remotion renders explanation videos

### FSRS Scheduler
Tracks `stability`, `difficulty`, and `next_review` per user per question. After 5+ consecutive correct answers, marks item as mastered. State stored in `user_progress_of_language_items` table.

## Environment Configuration

- **Backend**: `backend/.env` — DB URL, LLM API keys (Gemini, Claude, Doubao, Voyage, DeepSeek, Ali, Zhipu), Whisper ASR, TTS (Tencent/Edge), Tencent COS, email (Resend/SMTP), Google OAuth, JWT secret
- **Frontend dev**: `frontend/.env.development` — sets `VITE_API_BASE_URL=http://localhost:8000`
- **Frontend prod**: `frontend/.env.production` — production API URL

## Multi-Provider LLM Strategy

The platform supports multiple LLM and embedding providers with factory patterns in `content_builder/llm_providers.py`. Embedding providers (Gemini, Doubao, Voyage) are selectable via env vars. This allows swapping providers without code changes.

## Database Schema (PostgreSQL)

Key tables: `users`, `courses`, `language_items`, `user_courses`, `user_progress_of_language_items` (FSRS state), `user_progress_of_lessons`, `review_logs`, `vocabulary_knowledge` (cached embeddings), `user_login_history`.
