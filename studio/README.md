# Softbound Studio

World Bible Studio — a React front end for authoring Softbound worlds through a four-stage journey: **bible → style → stories → flow**.

Integrated with this repo's FastAPI backend for live co-author LLM calls, with automatic fallback to local mock logic when the API is offline.

## Run locally (full stack)

From the **repository root**:

**Terminal 1 — backend** (port 3000):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --reload --port 3000
```

Optional: set `GEMINI_API_KEY` in `.env` for real LLM responses. Without it, the backend uses deterministic mock responses.

**Terminal 2 — studio** (port 5173):

```bash
cd studio
npm install
npm run dev
```

Open http://localhost:5173. Vite proxies `/api` and `/health` to the backend.

The bottom-left badge shows **co-author: connected** when the backend is reachable, or **offline (local mock)** when using fallbacks only.

## Environment

Copy `.env.example` to `.env` if you need a non-proxied API URL in production:

```
VITE_API_BASE_URL=https://your-api.example.com
```

Leave empty for local dev (uses Vite proxy).

## Build

```bash
npm run build
npm run preview
```

## API mapping

| Studio action | Backend endpoint |
|---------------|------------------|
| Seed bible | `POST /api/studio/bible/generate` |
| Weave note / ask co-author | `POST /api/studio/bible/revise` |
| Reweave cast into bible | `POST /api/studio/bible/reweave` |
| Seed cast | `POST /api/studio/cast/seed` |
| Refine / flesh character | `POST /api/studio/characters/refine`, `/flesh` |
| Generate style library | `POST /api/studio/style/generate` |
| Propose / revise stories | `POST /api/studio/stories/propose`, `/revise` |

Legacy endpoints (`/api/expand-description`, `/api/suggest-characters`, etc.) remain available — see [FRONTEND_INTEGRATION.md](../FRONTEND_INTEGRATION.md) in the repo root.

## Features

- **Worlds gallery** — create, open, and delete worlds; progress dots show bible / style / stories / flow completion
- **Bible stage** — seed a world, co-author drafts, highlight text to leave margin notes, version history (manuscript or studio layout)
- **Cast** — characters with refine loop; reweave bible when the cast changes
- **Style stage** — pick a visual direction, generate a prompt library, reference image slots
- **Stories stage** — proposed vs saved stories, beat editor, co-author refine
- **Flow stage** — workflow canvas preview (stub wired for future integration)

Data persists in `localStorage` (`softbound:worlds:v2`).

## Project structure

```
softbound-studio/
├── src/lib/api.ts      # Backend client
├── src/lib/engine.ts   # Co-author facade (API + local fallback)
├── src/components/     # UI stages and editors
└── src/styles/         # Design CSS
```
