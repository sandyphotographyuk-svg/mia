# Mia — Expert Engineer & Personal Companion

Mia is a local-first AI companion: FastAPI backend (Ollama/Qwen for chat, code, SQL,
diagrams, charts, UI schemas), Hugging Face visual pipeline (FLUX.2-klein / Qwen-Image
with character-consistent avatars + animated GIF previews), Celery reminders + daily
briefings, WebRTC signalling, and a React + Tailwind dashboard.

## Architecture

```
mia/
├── backend/
│   ├── main.py                 # FastAPI entrypoint (/health, /api/*, /outputs, /ws)
│   ├── core/                   # config, security (JWT/bcrypt), database, celery_app
│   ├── agents/                 # ollama_client, persona prompts, mia_agent orchestrator
│   ├── services/               # code_sandbox, sql_sandbox, multimodal router,
│   │                           # image_gen (HF), video_render (GIF), notifier,
│   │                           # briefing, signalling (socket.io)
│   └── api/                    # routes_chat, routes_avatar, routes_render,
│                               # routes_reminders, routes_video
├── frontend/                   # React + Vite + Tailwind + Zustand + mermaid + socket.io
│   └── src/ (lib/api, store, components, pages: Chat, AvatarStudio, VideoCall, Reminders)
├── tests/                      # pytest suite (48 tests, phases 1–4)
└── docker-compose.yml          # api + worker + beat + postgres + redis (+ frontend)
```

## Prerequisites

| Tool | Needed for | Status / install |
|---|---|---|
| Python 3.11+ | backend, tests | ✅ 3.14.7 detected |
| Node 18+ / npm | frontend | ✅ Node v26 detected |
| Ollama + Qwen model | chat/coding/SQL | ✅ `qwen2.5-coder:7b` + `qwen3.8:27b` detected |
| Docker Desktop | postgres + redis + compose | ❌ **not installed — required for `docker compose up`** |
| GitHub auth (`gh auth login`) | pushing to `mia.git` | check with `gh auth status` |

## Quickstart (local, no Docker)

```bash
cd mia

# 1. env
cp .env.example .env
# edit .env: set HUGGINGFACE_API_KEY for real renders (else placeholders),
# TELEGRAM_BOT_TOKEN/CHAT_ID or GENERIC_WEBHOOK_URL for real pushes.

# 2. backend (sqlite fallback works with zero setup)
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend && uvicorn main:app --reload --port 8000
# → http://localhost:8000/health  {"status":"ok",...}
# → docs at http://localhost:8000/docs

# 3. frontend (new terminal)
cd frontend && npm install && npm run dev
# → http://localhost:5173 (proxies /api + /outputs → :8000)
```

## Quickstart (Docker — full stack)

```bash
cd mia
cp .env.example .env   # fill secrets; DATABASE_URL already points at compose postgres
docker compose up --build
# api → :8000 | frontend → :5173 | postgres → :5432 | redis → :6379
# worker + beat handle background reminder dispatch + 07:00 UTC daily briefing
```

> **Ollama from inside Docker:** the compose file sets `OLLAMA_BASE_URL=http://host.docker.internal:11434`
> so containers reach your Mac's Ollama. On Linux use `--network host` or export
> `OLLAMA_BASE_URL=http://<host-ip>:11434`.

## Environment variables

See `.env.example` (copy to `.env`, never commit it):

| Var | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy URL (compose postgres, or `sqlite:///./mia.db` local) | compose postgres |
| `REDIS_URL` / `CELERY_*` | queue + result backend | `redis://redis:6379/*` in compose |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | local LLM | `http://localhost:11434` / `qwen2.5-coder:7b` |
| `HUGGINGFACE_API_KEY` / `HF_IMAGE_MODEL` / `HF_IMAGE_ENDPOINT` | visual renders | FLUX.2-klein-4B (placeholder mode when key empty) |
| `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` / `GENERIC_WEBHOOK_URL` / `DESKTOP_NOTIFY_ENABLED` | reminder channels | desktop log on |
| `VITE_API_URL` / `VITE_SOCKET_URL` | frontend → backend | `http://localhost:8000` |

## API reference (key routes)

- `GET /health` · `GET /docs` (Swagger)
- Chat: `POST /api/chat/` `{message, session_id, mode:auto|general|coding|sql|diagram|chart|ui}` →
  `{reply, mode, artifact, session_id}` · `GET /api/chat/history/{session}` ·
  `POST /api/chat/run-code` · `POST /api/chat/run-sql`
- Avatar: `POST /api/avatar/generate` `{prompt, style, seed, character_ref}` ·
  `POST /api/avatar/render` · `GET /api/avatar/styles` ·
  `POST /api/avatar/profiles` · `GET /api/avatar/profiles`
- Render: `POST /api/render/preview` → animated GIF `{url, frames, fps}`
- Reminders: `POST/GET /api/reminders/` · `GET/DELETE /api/reminders/{id}` ·
  `POST /api/reminders/{id}/dispatch` · `POST /api/reminders/poll-due`
- Video: `POST /api/video/signal|/join|/leave` · `GET /api/video/history/{session}` ·
  `POST /api/video/daily-briefing` · Socket.IO signalling mounted at `/ws`
- Static renders served at `/outputs/*`

## Tests

```bash
cd mia
python3 -m venv .venv-test && source .venv-test/bin/activate
pip install fastapi httpx sqlalchemy pydantic pydantic-settings pytest pillow celery python-socketio
python -m pytest tests/ -v
# 48 passed (phases 1–4). Frontend: cd frontend && npm run build (runs tsc --noEmit + vite build)
```

## Character consistency (avatars)

Same `character_ref` token + same `seed` → same prompt prefix
(`STYLE_PRESETS` + identity phrase) → uniform Mia identity across renders.
Save named appearance profiles (`POST /api/avatar/profiles`) and reload them
from the Avatar Studio tab.

## Troubleshooting

- **Backend offline in UI** → `uvicorn main:app` running on :8000? Check `GET /health`.
- **Placeholder images** → set `HUGGINGFACE_API_KEY` for real FLUX/Qwen-Image renders.
- **Reminders never arrive** → run `worker + beat` (compose) or hit `POST /api/reminders/poll-due`;
  set Telegram/webhook env or use `desktop` channel.
- **Ollama unreachable** → `ollama serve` running? Chat returns an `[Mia offline …]` stub otherwise.
- **No Docker** → everything except postgres/redis/worker runs locally via sqlite + `poll-due`.
