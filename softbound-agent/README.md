# Softbound Agentic Framework

Orchestrated agents for intent → audience → world → story → scenes → evaluation → variants. Each agent can call an open-source LLM when prompts are set; with empty prompts (default), agents use fallback logic so the pipeline runs without an API.

## Setup

From the `softbound` directory:

```bash
pip install -r requirements.txt   # includes requests for LLM client
```

## Running

Set `PYTHONPATH` to this directory, then import and run:

```bash
cd /path/to/softbound
PYTHONPATH=softbound-agent python3 -c "
from orchestrator import CreativeOrchestratorAgent
o = CreativeOrchestratorAgent()
p = o.run(
    {'artist_style': 'sketch', 'product_philosophy': 'gentle', 'emotional_promise': 'calm'},
    {'age_range': '3-5', 'emotional_needs': 'security', 'attention_span': 'short', 'culture': '', 'coplay': ''}
)
print(p.story.theme, p.scenes, p.evaluation, p.variants)
"
```

## LLM (optional)

The framework uses an **OpenAI-compatible** chat API so you can point at Ollama, OpenRouter, Together, or any compatible endpoint.

| Env var | Default | Description |
|--------|---------|-------------|
| `OPENAI_API_BASE` | `http://localhost:11434/v1` | Base URL (e.g. Ollama) |
| `OPENAI_API_KEY` | (none) | API key if required |
| `OPENAI_MODEL` | `llama3.2` | Model name |

Example with Ollama:

```bash
# Ensure Ollama is running and a model is pulled, then:
export OPENAI_API_BASE=http://localhost:11434/v1
export OPENAI_MODEL=llama3.2
PYTHONPATH=softbound-agent python3 your_script.py
```

## Adding prompts later

Each agent has **empty** `SYSTEM_PROMPT` and `USER_PROMPT_TEMPLATE` by default. When both are empty, the agent does not call the LLM and uses built-in fallback behavior.

To enable LLM for an agent:

1. **Class attributes** (simple): set `SYSTEM_PROMPT` and/or `USER_PROMPT_TEMPLATE` on the agent class. Use `{placeholders}` in the user template; they are filled from keyword arguments passed to `maybe_call_llm(**context)`.

2. **Override methods** (flexible): override `get_system_prompt()` and `get_user_prompt(**context)` to build prompts dynamically, or override `_parse_llm_response()` to turn raw LLM text into your data models.

Example for `IntentAgent` (import from `agents`):

```python
from agents import IntentAgent

class MyIntentAgent(IntentAgent):
    SYSTEM_PROMPT = "You refine creative intent for child-friendly content."
    USER_PROMPT_TEMPLATE = "Artist style: {artist_style}. Philosophy: {product_philosophy}. Refine in one short line."

# Use MyIntentAgent() in your pipeline, or patch IntentAgent.SYSTEM_PROMPT / USER_PROMPT_TEMPLATE.
```

## Layout

```
softbound-agent/
├── __init__.py          # Public API (models, agents, orchestrator)
├── README.md
├── orchestrator.py     # CreativeOrchestrator.run() → World + Story
├── core/               # Shared infrastructure
│   ├── __init__.py
│   ├── models.py       # Intent, AudienceExperience, World, Story, Scene, StoryPackage
│   ├── llm_client.py   # complete(), is_available() — OpenAI-compatible API
│   └── base_agent.py   # BaseAgentMixin (prompts, maybe_call_llm)
└── agents/             # Pipeline and helper agents
    ├── __init__.py
    ├── intent.py       # IntentAgent (Layer 1)
    ├── audience.py     # AudienceAgent (Layer 2)
    ├── world.py        # WorldAgent, StoryAgent (Layers 3–4)
    └── helpers.py      # KnowledgeGuardianAgent, EvaluationAgent, VariantAgent
```

Imports: `from core import Intent, Story, complete, BaseAgentMixin`; `from agents import IntentAgent, WorldAgent, ...`; `from orchestrator import CreativeOrchestratorAgent`.
