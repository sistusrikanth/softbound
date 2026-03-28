# Softbound agent package

Python package for the **intent → audience → world → story** pipeline. The orchestrator is the main entry point.

**How to run:** see the parent [`README.md`](../README.md) (environment variables, `PYTHONPATH`, `--store` / `--load`).

## Quick start

```bash
cd ..   # softbound/
pip install -r softbound-agent/requirements.txt
```

```bash
SOFTBOUND_LLM_BACKEND=gemini PYTHONPATH=softbound-agent \
  python3 softbound-agent/orchestrator.py --load session_2.json
```

## Entry point

- **`orchestrator.py`** — `CreativeOrchestrator.run(load_path=..., store_path=...)`

Imports expect `PYTHONPATH` to include this directory (`softbound-agent`), so `core` and `agents` resolve.

## Layout

```
softbound-agent/
├── orchestrator.py
├── env.example
├── core/
│   ├── models.py       # Intent, AudienceExperience, World, Story, …
│   ├── llm_client.py   # complete(), is_available()
│   ├── session_store.py
│   └── base_agent.py
└── agents/
    ├── intent.py
    ├── audience.py
    └── world.py        # WorldAgent, StoryAgent
```

## LLM configuration

Details are in `core/llm_client.py` — Gemini (`GEMINI_API_KEY`), OpenRouter (`OPENROUTER_API_KEY`), or local (`SOFTBOUND_LLM_BACKEND=local`).
