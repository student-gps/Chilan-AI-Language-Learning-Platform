# Contributing to Chilan

Thanks for your interest in contributing to Chilan.

Chilan is an AI-powered, course-based language learning project that combines a React frontend, a FastAPI backend, and a local content-production workflow. Contributions are welcome, especially around reliability, usability, documentation, and maintainability.

## Before you start

- Read the main [README](README.md) for the project overview and quick-start flow.
- Check the public docs in [docs/](docs/) for architecture and development details.
- If your change affects learning behavior, grading, or review logic, please describe the expected user impact clearly.

## Recommended contribution flow

1. **Open an issue or start a discussion first** for larger changes, especially if they affect:
   - answer evaluation logic,
   - review scheduling,
   - course or content data flow,
   - public APIs,
   - repository structure.

2. **Keep pull requests focused.** Small, reviewable PRs are much easier to merge than broad rewrites.

3. **Explain the why, not just the what.** In your PR description, include:
   - what changed,
   - why it changed,
   - how it was tested,
   - and whether docs were updated.

## Local development

### Frontend

```bash
cd frontend
npm install
npm run dev
npm run build
npm run lint
```

### Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## Project-specific notes

### 1. Use the existing app and service boundaries

- Frontend HTTP calls should go through `frontend/src/api/apiClient.js`.
- Backend learning and evaluation behavior should follow the existing route/service structure.
- Media and asset URLs should come from the backend flow rather than being hand-constructed in the frontend.

### 2. Be careful with learner-facing logic

Please call out any changes to:

- semantic answer grading,
- speech transcription handling,
- FSRS or review scheduling behavior,
- progress calculations,
- or course-access rules.

These areas are central to the product and usually require extra review.

### 3. Treat content tooling as a separate workflow

This repo contains local content-production utilities in addition to the live app. If your PR touches those workflows, explain:

- what pipeline or artifact flow is affected,
- whether changes are local-only or intended for public repo docs,
- and whether any generated files should remain untracked.

## Documentation expectations

If your change affects setup, architecture, developer workflow, or public project messaging, please update one or more of:

- [README.md](README.md)
- [README.zh.md](README.zh.md)
- [docs/index.md](docs/index.md)
- relevant docs under [docs/](docs/)

## Coding and review expectations

- Prefer consistency with the surrounding code over introducing a new pattern unnecessarily.
- Avoid unrelated refactors inside feature or fix PRs.
- Keep commits and PRs easy to review.
- If you are changing behavior, include enough context for maintainers to reproduce it.

## What is especially helpful

Contributions are particularly valuable in these areas:

- bug fixes in study flow or grading flow,
- review-scheduling correctness,
- frontend usability improvements,
- tests for important backend behavior,
- documentation improvements,
- and maintainability cleanup with clear scope.

## License

By contributing, you agree that your contributions will be licensed under the project’s [MIT License](LICENSE).
