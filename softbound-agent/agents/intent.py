# Layer 1: Intent Agent — free-form text for lightweight LLMs
from __future__ import annotations

import re

from core.base_agent import BaseAgentMixin
from core.models import Intent
from .prompts_common import GLOBAL_DIRECTIVE

# Section headers the LLM should output (plain text, no JSON)
SECTION_HEADERS = [
    ("ARTISTIC STYLE", "artist_style"),
    ("PRODUCT PHILOSOPHY", "product_philosophy"),
    ("EMOTIONAL PROMISE", "emotional_promise"),
    ("CREATIVE BOUNDARIES", "creative_boundaries"),
]


class IntentAgent(BaseAgentMixin):
    SYSTEM_PROMPT = GLOBAL_DIRECTIVE + """
You define the intent behind a children's story. Reply with exactly four short sections, each on its own line with < 5 words each.
Use these exact labels followed by your answer. Generate new, varied ideas each time — do not repeat the same phrasing.

Derive missing features based on earlier sections provided. 

ARTISTIC STYLE: (style, voice, tone in one or two sentences)
PRODUCT PHILOSOPHY: (what the product aims to do for the child in one or two sentences)
EMOTIONAL PROMISE: (what the child is left with; what to avoid)
CREATIVE BOUNDARIES: (what is allowed and what is off-limits)

Return result as a list"""

    USER_PROMPT_TEMPLATE = "{hints}"

    def create(self, input_data: dict | None = None) -> Intent:
        input_data = input_data or {}
        hints = _hints(input_data)
        out = self.maybe_call_llm(hints=hints).split("\n")
        out = [line.strip() for line in out if line.strip()]
        # print(f"============= Intent Agent output: {out} =============")
        artist_style = out[0].split(":")[1].strip() if ":" in out[0] else out[0].strip()
        product_philosophy = out[1].split(":")[1].strip() if ":" in out[1] else out[1].strip()
        emotional_promise = out[2].split(":")[1].strip() if ":" in out[2] else out[2].strip()
        creative_boundaries = out[3].split(":")[1].strip() if ":" in out[3] else out[3].strip()
        return Intent(artist_style=artist_style, product_philosophy=product_philosophy, emotional_promise=emotional_promise, creative_boundaries=creative_boundaries)


def _hints(data: dict) -> str:
    if not data:
        return "No specific intent provided. Invent a fresh, coherent children's storytelling intent this time."
    parts = [f"{k}: {v}" if isinstance(v, str) else f"{k}: {v}" for k, v in data.items()]
    return "User hints (use as inspiration; still generate new wording): " + " | ".join(parts)

