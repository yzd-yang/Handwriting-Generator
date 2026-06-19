# AGENTS.md

## Project Overview

Handwriting text generation web app — converts user text into realistic handwriting images or PDFs using random perturbations (font size jitter, position offset, rotation, strikethrough, ink depth).

Architecture: **Vue 3 frontend** (Vite + Tailwind CSS) + **FastAPI backend** (Python 3.10+), deployed via Docker Compose.

## Directory Layout

| Directory | Role | Entry point |
|-----------|------|-------------|
| `frontendVite/` | Vue 3 SPA (Vite, Tailwind CSS, Tiptap, PWA) | `src/main.js` |
| `backend/` | FastAPI app + handwriting rendering engine | `app.py` |
| `serverless/` | Vercel serverless function (email only) | `api/sendEmail.js` |
| `ttf_files/` | Bundled `.ttf` font assets, mounted into backend | — |
| `mysql/` | MySQL Dockerfile + init SQL (optional, not required) | — |

`frontend/` is the old Vue CLI frontend — deprecated, use `frontendVite/` instead.

## Commands

### Frontend (run from `frontendVite/`)

```bash
npm install                 # install dependencies
npm run dev                 # dev server on :5173, proxies /api → :5005
npm run build               # production build → dist/
npm run lint                # ESLint + Prettier
```

### Backend (run from `backend/`)

```bash
pip install -r requirements.txt          # or: poetry install
python app.py                            # uvicorn dev server on :5005
```

Production backend runs via gunicorn: `gunicorn app:app -b 0.0.0.0:5005 -w 1 -k uvicorn.workers.UvicornWorker --timeout 300`

### Docker (from repo root)

```bash
docker compose up -d   # frontend on :2345, backend on :5005
```

### Tests (run from `backend/`)

```bash
pytest tests/test_generate_concurrency.py
```

Concurrency test is **integration-only** — requires a running backend at `HANDWRITING_BASE_URL` (default `http://127.0.0.1:5005`). No unit test suite exists.

### Release

Semantic-release on `main` branch (`release.config.js`). Generates changelog, GitHub release, and git tag.

## Architecture Notes

### Async Task Queue (backend)

The generate endpoint (`POST /api/generate_handwriting`) does **not** render synchronously. Flow:

1. Submit → returns `{ status: "accepted", task_id: "..." }` immediately
2. Background task runs `generate_handwriting_impl` with semaphore (`MAX_CONCURRENT_EXECUTIONS = 2`)
3. Task state stored in **SQLite** (`backend/tasks.db`, WAL mode) — `task_store.py`
4. Large result files (images/PDF) stored on disk under `backend/temp/task_results/<task_id>/`
5. Client polls `GET /api/generate_handwriting/task/{task_id}` or uses WebSocket at `/api/generate_handwriting/ws/{task_id}`
6. Result fetched via `GET /api/generate_handwriting/task/{task_id}/result` — then auto-deleted

Task TTL: 30 minutes. Max active tasks: 8. Queue full → HTTP 503.

### Handwriting Rendering

Uses the `handright` library (`handrightbeta==8.7.0`). `handwrite()` returns a **lazy map** — CPU-intensive rendering happens when the generator is consumed in the for-loop, not at call time.

### Paragraph Layout Pre-processing

`apply_paragraph_layout()` in `app.py` transforms text before `handwrite()` to simulate first-line indent, center/right alignment, and paragraph spacing — features handright doesn't natively support. Uses full-width spaces for padding (works well for CJK monospace fonts, less accurate for proportional Latin fonts).

### Font Assets

At startup, `sync_font_assets()` copies `.ttf` files from `FONT_ASSETS_BUNDLED_DIR` → `FONT_ASSETS_DIR` (only if destination doesn't already have the file). In Docker, bundled fonts are at `/app/font_assets`, host fonts mounted at `/app/font_assets_host`.

### Pandoc Dependency

Backend uses `pypandoc` for `.docx` text extraction. If Pandoc isn't installed, `app.py` auto-downloads it at startup. Docker image installs it via `apt-get`.

### File Upload Safety

`secure_filename()` strips Chinese characters from filenames. The code compensates by prepending `uuid4().hex` to avoid collisions.

### Document Import (docx/pdf)

- **docx**: pypandoc converts to HTML, regex extracts `<body>` content, strips wrapper tags
- **pdf**: PyPDF2 extracts text, wraps in `<p>` tags for HTML output
- Frontend TiptapEditor displays HTML, converts to plain text before sending to backend for rendering

## Frontend Details

- **Framework**: Vue 3 + Vuex + Vue Router + vue-i18n
- **Build**: Vite
- **UI**: Tailwind CSS + SweetAlert2
- **Rich Text**: Tiptap (bold, italic, underline, lists, text alignment)
- **HTTP**: axios with `axios-retry` (3 retries, exponential backoff, skips retry on 503 queue_full)
- **Monitoring**: Sentry (error tracking)
- **PWA**: vite-plugin-pwa

## Conventions

- All form field values are **strings** in the API contract (see `GenerateHandwritingParams` in `task_types.py`) — even numeric fields like `font_size`, `line_spacing`, etc.
- `paper_type` values: `"blank"`, `"lines"`, `"grid"`, `"dots"`. Legacy requests use `isUnderlined` which maps to `"lines"` / `"blank"`.
- `fill` field is a string like `"(0, 0, 0, 255)"` — currently unused in rendering (ink color is derived elsewhere).
- Backend logging goes to both console and `backend/logs/app.log`.
- `tasks.db` and `*.pyc` are gitignored; don't commit them.

## Env Variables

| Variable | Default | Where |
|----------|---------|-------|
| `FONT_ASSETS_DIR` | `./font_assets` | Backend — where fonts are read from |
| `FONT_ASSETS_BUNDLED_DIR` | `./font_assets` | Backend — source for font sync |
| `ENABLE_USER_AUTH` | `"false"` | Backend — auth is currently disabled/removed |
| `MYSQL_HOST` | `"db"` | Backend — unused unless auth is re-enabled |
| `HANDWRITING_BASE_URL` | `http://127.0.0.1:5005` | Tests — backend URL for concurrency tests |

## Gotchas

- Backend generates temp files in `./temp/` and `./textfileprocess/`/`./imagefileprocess/` — cleanup is best-effort with retry logic. Don't assume temp dirs are clean.
- The concurrency test (`test_generate_concurrency.py`) is a load test that submits multiple requests in parallel — it needs a live backend, not a mock.
- `right_margin` in the Template constructor is adjusted: `right_margin - word_spacing * 2`. This is intentional compensation for handright's layout algorithm.
- Watchtower in docker-compose auto-pulls new images every 6 hours and does rolling restarts.
- TiptapEditor emits HTML; frontend converts to plain text via `htmlToPlainText()` before sending to backend.
