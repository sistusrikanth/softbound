# Softbound Backend

FastAPI server that accepts world-building input from a frontend and runs LLM agents for world-building and the **Softbound Studio** co-author flow.

**Frontend:** the World Bible Studio React app lives in [`studio/`](./studio/). See [studio/README.md](./studio/README.md) for running the full stack.

**API contracts:** see [FRONTEND_INTEGRATION.md](./FRONTEND_INTEGRATION.md) for endpoint details, TypeScript types, and example `fetch` calls.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn server:app --reload --port 3000
```

If `GEMINI_API_KEY` is set in your environment, the server uses Gemini automatically. Otherwise it defaults to `mock`. Override with `LLM_PROVIDER=mock` or `LLM_PROVIDER=gemini`.

Supported models include `gemini-3-flash-preview`, `gemini-2.5-flash`, `gemini-3.1-flash-lite-preview`, `gemma3-1b-it` (set via `GEMINI_MODEL`).

## API

### Health

- `GET /health`

### Expand description

- `POST /api/expand-description`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `description` | string | yes | Short description to expand |
| `world_style` | string | no | Style context for tone |
| `characters` | array | no | Existing characters for context |

Response: `{ "message": "Description expanded", "description": "..." }`

### Suggest characters

- `POST /api/suggest-characters`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | yes | Story / world description (short or current) |
| `expanded_description` | string | no | Expanded description from "Help me expand"; used when present |
| `existing_characters` | array | no | Characters to avoid duplicating |
| `world_style` | string | no | Style context |
| `count` | number | no | Number of characters to suggest (default `3`) |

Response: `{ "message": "Characters suggested", "characters": [{ "name", "description" }, ...] }`

### Generate style prompt

- `POST /api/generate-style-prompt`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `style_description` | string | yes | Short style description to expand |
| `text` | string | no | Story context |

Response: `{ "message": "Style prompt generated", "style_prompt": "..." }`

### Generate world

- `POST /api/world`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | yes | Seed / free-form world text |
| `characters` | array | yes | Character names or `{ name, description }` objects |
| `world_style` | string | yes | Tone / aesthetic guide |
| `mode` | string | no | `"standalone"` (default) or `"agentic"` |
| `max_iterations` | number | no | Agentic critique/refine cycles (default `3`) |
| `include_trace` | boolean | no | Include step-by-step trace in response |

### Manual API test script

With the server running:

```bash
./test_api.sh
```

Override the base URL if needed:

```bash
BASE_URL=http://localhost:3001 ./test_api.sh
```

### Examples

```bash
curl -X POST http://localhost:3000/api/expand-description \
  -H "Content-Type: application/json" \
  -d '{"description": "A city built on the bones of a dead god"}'

curl -X POST http://localhost:3000/api/suggest-characters \
  -H "Content-Type: application/json" \
  -d '{"text": "A city built on the bones of a dead god", "count": 2}'

curl -X POST http://localhost:3000/api/generate-style-prompt \
  -H "Content-Type: application/json" \
  -d '{"style_description": "dark fantasy, melancholic"}'

curl -X POST http://localhost:3000/api/world \
  -H "Content-Type: application/json" \
  -d '{
    "text": "A city built on the bones of a dead god",
    "characters": ["Mira, a scavenger"],
    "world_style": "dark fantasy, melancholic"
  }'

curl -X POST http://localhost:3000/api/world \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Floating islands connected by silk bridges",
    "characters": [],
    "world_style": "whimsical steampunk",
    "mode": "agentic",
    "max_iterations": 2,
    "include_trace": true
  }'
```

## Project layout

```
agents/                         # LLM agents (world, description, characters, style)
agents/world_agent.py           # WorldAgent (standalone + agentic world generation)
agents/world_description_agent.py
agents/world_characters_agent.py
agents/world_style_agent.py
lib/llm/                # Gemini client + mock provider
server.py               # FastAPI routes
```

## Cloud deployment

- `PORT` from environment
- Start: `uvicorn server:app --host 0.0.0.0 --port $PORT`
- Set `GEMINI_API_KEY` in the host's secrets/config
