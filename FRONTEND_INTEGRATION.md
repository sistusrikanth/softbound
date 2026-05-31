# Frontend Integration Guide

This document describes how to connect the Softbound UI to the backend API.

## Base URL

| Environment | URL |
|-------------|-----|
| Local dev | `http://localhost:3000` |
| Production | Set via your deployment (e.g. `https://api.softbound.example`) |

All endpoints accept and return JSON. Set the header:

```
Content-Type: application/json
```

CORS is enabled for all origins, so browser `fetch` calls from your frontend will work without extra configuration.

## Quick start

1. Start the backend:

```bash
cd softbound-backend
source .venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --reload --port 3000
```

2. Verify it is running:

```bash
curl http://localhost:3000/health
# → {"ok": true}
```

3. Point your frontend API client at `http://localhost:3000`.

---

## UI → API mapping

| UI section | Button / action | Endpoint | What to do with the response |
|------------|-----------------|----------|------------------------------|
| **Description** | Help me expand | `POST /api/expand-description` | Replace the description textarea with `response.description`. Store the expanded text separately if you want to pass it to other endpoints. |
| **Characters** | Suggest characters | `POST /api/suggest-characters` | Append each item in `response.characters` to the character list. Image upload stays on the frontend — the backend only returns `name` and `description`. |
| **Characters** | Add character | *(no API call)* | Handle locally: image, name, short description. |
| **Style** | Generate style prompt | `POST /api/generate-style-prompt` | Replace the style textarea with `response.style_prompt`. |
| **World generation** *(if used)* | Generate world | `POST /api/world` | Display `response.world` (markdown string). |

---

## Recommended frontend state

Keep these fields in your creation form state:

```typescript
type Character = {
  id: string;           // frontend-generated UUID
  name: string;
  description: string;
  imageUrl?: string;    // frontend only — never sent to backend
};

type CreationFormState = {
  description: string;           // current text in the description textarea
  expandedDescription?: string;  // set after "Help me expand"
  characters: Character[];
  styleDescription: string;      // current text in the style textarea
  expandedStylePrompt?: string;  // set after "Generate style prompt"
};
```

When the user clicks **Help me expand**, save the result to both `description` (for display) and `expandedDescription` (for richer context in later calls).

---

## TypeScript types

```typescript
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:3000";

// --- Shared ---

type ApiCharacter = {
  name: string;
  description: string;
};

type ApiError = {
  detail: {
    error: string;
    detail: string;
  };
};

// --- Expand description ---

type ExpandDescriptionRequest = {
  description: string;
  world_style?: string;
  characters?: ApiCharacter[];
};

type ExpandDescriptionResponse = {
  message: string;
  description: string;
};

// --- Suggest characters ---

type SuggestCharactersRequest = {
  text: string;
  expanded_description?: string;
  existing_characters?: ApiCharacter[];
  world_style?: string;
  count?: number; // default 3
};

type SuggestCharactersResponse = {
  message: string;
  characters: ApiCharacter[];
};

// --- Generate style prompt ---

type GenerateStyleRequest = {
  style_description: string;
  text?: string;
};

type GenerateStyleResponse = {
  message: string;
  style_prompt: string;
};

// --- Generate world ---

type GenerateWorldRequest = {
  text: string;
  characters: (string | ApiCharacter)[];
  world_style: string;
  mode?: "standalone" | "agentic";
  max_iterations?: number;
  include_trace?: boolean;
};

type GenerateWorldResponse = {
  message: string;
  mode: "standalone" | "agentic";
  iterations: number;
  world: string;
  trace?: unknown[];
};
```

---

## API reference

### Health check

```
GET /health
```

**Response `200`**

```json
{ "ok": true }
```

Use this on app load or in a settings/debug panel to confirm the backend is reachable.

---

### Expand description

```
POST /api/expand-description
```

Expands a short description into richer prose.

**Request body**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `description` | string | yes | Current description textarea value |
| `world_style` | string | no | Style context for tone |
| `characters` | array | no | Existing characters for context |

**Response `200`**

```json
{
  "message": "Description expanded",
  "description": "A sprawling city rises from the ribcage of a fallen titan..."
}
```

**Example**

```typescript
async function expandDescription(
  description: string,
  worldStyle?: string,
  characters?: ApiCharacter[]
): Promise<string> {
  const res = await fetch(`${API_BASE}/api/expand-description`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      description,
      world_style: worldStyle ?? "",
      characters: characters ?? [],
    }),
  });

  if (!res.ok) throw await res.json();
  const data: ExpandDescriptionResponse = await res.json();
  return data.description;
}
```

---

### Suggest characters

```
POST /api/suggest-characters
```

Suggests new characters based on the story description.

**Request body**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `text` | string | yes | Short / original description (fallback context) |
| `expanded_description` | string | no | **Pass this when the user has expanded the description.** Takes priority over `text`. |
| `existing_characters` | array | no | Characters already in the list — backend avoids duplicates |
| `world_style` | string | no | Style context |
| `count` | number | no | How many to suggest (default `3`) |

**Response `200`**

```json
{
  "message": "Characters suggested",
  "characters": [
    {
      "name": "Mira Ashford",
      "description": "A sharp-eyed scavenger who maps the god-bone tunnels."
    }
  ]
}
```

**Example**

```typescript
async function suggestCharacters(
  text: string,
  options: {
    expandedDescription?: string;
    existingCharacters?: ApiCharacter[];
    worldStyle?: string;
    count?: number;
  } = {}
): Promise<ApiCharacter[]> {
  const res = await fetch(`${API_BASE}/api/suggest-characters`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text,
      expanded_description: options.expandedDescription ?? "",
      existing_characters: options.existingCharacters ?? [],
      world_style: options.worldStyle ?? "",
      count: options.count ?? 3,
    }),
  });

  if (!res.ok) throw await res.json();
  const data: SuggestCharactersResponse = await res.json();
  return data.characters;
}
```

After receiving characters, map them into your local `Character` type (add `id`, leave `imageUrl` empty for the user to fill in):

```typescript
const newCharacters: Character[] = suggested.map((c) => ({
  id: crypto.randomUUID(),
  name: c.name,
  description: c.description,
}));
```

---

### Generate style prompt

```
POST /api/generate-style-prompt
```

Expands a short style description into a detailed style prompt.

**Request body**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `style_description` | string | yes | Current style textarea value |
| `text` | string | no | Story / description for additional context |

**Response `200`**

```json
{
  "message": "Style prompt generated",
  "style_prompt": "Dark fantasy with a melancholic, elegiac tone. Visual palette: ..."
}
```

**Example**

```typescript
async function generateStylePrompt(
  styleDescription: string,
  storyText?: string
): Promise<string> {
  const res = await fetch(`${API_BASE}/api/generate-style-prompt`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      style_description: styleDescription,
      text: storyText ?? "",
    }),
  });

  if (!res.ok) throw await res.json();
  const data: GenerateStyleResponse = await res.json();
  return data.style_prompt;
}
```

---

### Generate world

```
POST /api/world
```

Generates a full world description from seed text, characters, and style. Use this if your flow includes a final "generate world" step.

**Request body**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `text` | string | yes | Seed / story text |
| `characters` | array | yes | Strings or `{ name, description }` objects |
| `world_style` | string | yes | Style guide |
| `mode` | string | no | `"standalone"` (default) or `"agentic"` |
| `max_iterations` | number | no | Agentic refine cycles (default `3`) |
| `include_trace` | boolean | no | Include step-by-step trace |

**Response `200`**

```json
{
  "message": "World generated",
  "mode": "standalone",
  "iterations": 1,
  "world": "## Setting\n\nAn evocative world built from the seed text..."
}
```

Pass the best available description as `text` (prefer `expandedDescription` if set). Pass characters as `{ name, description }` objects and the expanded style prompt as `world_style` when available.

---

## Error handling

All LLM endpoints return **`500`** on failure:

```json
{
  "detail": {
    "error": "Description expansion failed",
    "detail": "Human-readable error message"
  }
}
```

Validation errors (missing required fields, wrong types) return **`422`** with FastAPI's standard validation error body.

**Recommended UI pattern:**

```typescript
async function callApi<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const message =
      err?.detail?.detail ??
      err?.detail?.error ??
      `Request failed (${res.status})`;
    throw new Error(message);
  }

  return res.json();
}
```

Show a loading spinner on the button while the request is in flight. LLM calls typically take **2–15 seconds** depending on provider and payload size — disable the button and show progress text like "Expanding…".

---

## End-to-end flow example

```
User types short description
        │
        ▼
[Help me expand] ──► POST /api/expand-description
        │                    │
        │                    └──► update description + store expandedDescription
        ▼
[Suggest characters] ──► POST /api/suggest-characters
        │                      (pass expanded_description if set)
        │                    └──► append characters to list
        ▼
User edits style description
        │
        ▼
[Generate style prompt] ──► POST /api/generate-style-prompt
        │                           └──► update style textarea
        ▼
[Generate world] ──► POST /api/world  (optional final step)
```

**Payload wiring for suggest characters:**

```typescript
await suggestCharacters(form.description, {
  expandedDescription: form.expandedDescription,
  existingCharacters: form.characters.map(({ name, description }) => ({
    name,
    description,
  })),
  worldStyle: form.expandedStylePrompt ?? form.styleDescription,
  count: 3,
});
```

**Payload wiring for generate style prompt:**

```typescript
await generateStylePrompt(form.styleDescription, form.expandedDescription ?? form.description);
```

---

## curl examples (manual testing)

```bash
# Health
curl http://localhost:3000/health

# Expand description
curl -X POST http://localhost:3000/api/expand-description \
  -H "Content-Type: application/json" \
  -d '{"description": "A city built on the bones of a dead god"}'

# Suggest characters (with expanded description)
curl -X POST http://localhost:3000/api/suggest-characters \
  -H "Content-Type: application/json" \
  -d '{
    "text": "A city built on the bones of a dead god",
    "expanded_description": "A sprawling city rises from the ribcage of a fallen titan...",
    "count": 2
  }'

# Generate style prompt
curl -X POST http://localhost:3000/api/generate-style-prompt \
  -H "Content-Type: application/json" \
  -d '{"style_description": "dark fantasy, melancholic"}'

# Generate world
curl -X POST http://localhost:3000/api/world \
  -H "Content-Type: application/json" \
  -d '{
    "text": "A city built on the bones of a dead god",
    "characters": [{"name": "Mira", "description": "A scavenger"}],
    "world_style": "dark fantasy, melancholic"
  }'
```

---

## Environment variable for the frontend

Add to your frontend `.env`:

```
VITE_API_BASE_URL=http://localhost:3000
```

For Next.js use `NEXT_PUBLIC_API_BASE_URL` instead. Update the production value when the backend is deployed.

---

## Notes

- **No auth** — endpoints are currently open. Add auth at the gateway or in FastAPI before production.
- **No persistence** — the backend is stateless. All form state lives in the frontend.
- **Images** — character images are frontend-only. The backend never receives or returns image URLs.
- **Mock mode** — when running locally without `GEMINI_API_KEY`, the backend returns deterministic mock responses. Useful for UI development without LLM costs.
- **Interactive API docs** — with the server running, open `http://localhost:3000/docs` for Swagger UI to try endpoints in the browser.
