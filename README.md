# Softbound

Agent pipeline for children’s story worlds: **intent → audience → world → story**, with optional LLM backends (Gemini, OpenRouter, or local).

## Setup

From this directory (`softbound/`):

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r softbound-agent/requirements.txt
```

Copy `softbound-agent/env.example` to `softbound-agent/.env` and set **`GEMINI_API_KEY`** (or export it). See [Google AI Studio](https://aistudio.google.com/apikey).

## Run the orchestrator

Use **`PYTHONPATH=softbound-agent`** so the `core` and `agents` packages resolve. Run from **`softbound/`** (repo root for this project):

### Gemini (recommended)

```bash
cd /path/to/softbound

SOFTBOUND_LLM_BACKEND=gemini PYTHONPATH=softbound-agent \
  python3 softbound-agent/orchestrator.py --store session_2.json
```

Runs the full pipeline (intent, audience, world, story), then saves **intent, audience, and world** to `session_2.json` before the story step completes. Omit the path to use the default file next to the orchestrator (see `--store` below).

Load a saved session and **skip LLM calls for layers 1–3** (only the story step runs):

```bash
SOFTBOUND_LLM_BACKEND=gemini PYTHONPATH=softbound-agent \
  python3 softbound-agent/orchestrator.py --load session_2.json
```

### CLI options

| Flag | Description |
|------|-------------|
| `--load PATH` | Load intent, audience, and world from JSON; no LLM for those layers. |
| `--store [PATH]` | After world is ready, save intent, audience, world to JSON. If you pass `--store` with no path, it uses **`softbound-agent/.softbound_session.json`**. |

### Environment (LLM)

| Variable | Purpose |
|----------|---------|
| `GEMINI_API_KEY` | Google AI Gemini API key (also `GOOGLE_API_KEY` is accepted). |
| `SOFTBOUND_LLM_BACKEND` | `gemini`, `openrouter`, or `local` to force a backend. |
| `GEMINI_MODEL` | Optional. Default: `gemini-2.0-flash-lite`. |
| `OPENROUTER_API_KEY` | If using OpenRouter instead of Gemini. |

If `SOFTBOUND_LLM_BACKEND` is unset, the client picks Gemini when a Gemini key is set, then OpenRouter, then local.

## Layout

```
softbound/
├── README.md                 # This file
└── softbound-agent/
    ├── orchestrator.py       # Entry: CreativeOrchestrator
    ├── env.example           # Copy to .env for GEMINI_API_KEY
    ├── core/                 # models, llm_client, session_store
    └── agents/               # Intent, Audience, World, Story agents
```

## License

See the repository root for license information.
