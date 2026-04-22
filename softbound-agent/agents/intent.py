# Layer 1: Intent — Creative Intent & Philosophy Architect (show-bible draft)
from __future__ import annotations

import re

from core.base_agent import BaseAgentMixin
from core.models import Intent
from .prompts_common import GLOBAL_DIRECTIVE

# LLM output sections (must match SYSTEM_PROMPT). Map to Intent field names.
_MARKERS: tuple[tuple[str, str], ...] = (
    ("PRODUCT_PHILOSOPHY", "product_philosophy"),
    ("MOOD_AESTHETIC", "artist_style"),
    ("CREATIVE_THEMES", "emotional_promise"),
    ("SAFETY_CURRICULUM", "creative_boundaries"),
)


class IntentAgent(BaseAgentMixin):
    SYSTEM_PROMPT = GLOBAL_DIRECTIVE + """
You are the Creative Director and Senior Showrunner for a premium children’s IP (think PBS Kids / thoughtful family streaming).
Draft a **Product Intent and Creative Philosophy** document — a concise show-bible draft — for **Softbound**: calm, page-based, co-play storytelling for early childhood.

Ground choices in **early childhood narrative architecture** (attention, safety, mastery through repetition, hierarchical goals by age).

Produce **four blocks** in this **exact** order, each starting on its own line with these delimiters (include the dashes):

---PRODUCT_PHILOSOPHY---
**1. Product philosophy (the Why)**
- Name the core mission using one lens: *Emotional Procedural* (e.g. routine + strategy songs), *Environmental Narrative* (world + systems), or *Social Realism* (relationship truth) — or a clear hybrid.
- How this serves the **2026 parent’s necessity** (rest, connection, guilt relief) without moralizing.
- **Ethical North Star (Maisy Test):** Gender representation, Freedom, Safety, Social justice — one line each.

---MOOD_AESTHETIC---
**2. Mood and aesthetic (the Vibe)**
- **Stimulation profile:** low-stakes vs quest-like energy; tie to amygdala-safe vs older-kid pacing where relevant.
- **Visual:** style + how it supports **orienting response** (e.g. soft watercolor buffer, paper tactility).
- **Auditory + participation:** overall sound mood; use of **participatory pause** space (invitation to answer/imitate without demand).

---CREATIVE_THEMES---
**3. Creative themes & narrative engine (the How)**
- Primary **structural archetype** (e.g. diminishing arc, diagnostic arc, home–away–home).
- **Narrative engine:** repeatable sequence building mastery (refrain, strategy moment, ritual beat).
- **Failure cycle:** how setbacks work for the target band’s **hierarchical goal structures** (small tries, repair, no shame).

---SAFETY_CURRICULUM---
**4. Safety, non-goals, and curriculum**
- **Non-goals:** bullet list of what you will NOT do (e.g. sarcasm, imitable danger, shame).
- **Home / cuddle return:** how every arc lands back in safety after exploration.
- **Curriculum matrix:** a **markdown table** | Narrative beat | Learning / developmental goal | — at least 3 rows.

Use evocative language for mood; precise language for ethics and mechanics. Keep each block tight but complete."""

    USER_PROMPT_TEMPLATE = "{hints}"

    def create(self, input_data: dict | None = None) -> Intent:
        data = input_data if isinstance(input_data, dict) else {}
        hints = _hints(data)
        out = self.maybe_call_llm(hints=hints)
        base = _fallback(data)
        if out:
            parsed = _parse_delimited(out)
            if parsed:
                return Intent(
                    product_philosophy=parsed["product_philosophy"] or base.product_philosophy,
                    artist_style=parsed["artist_style"] or base.artist_style,
                    emotional_promise=parsed["emotional_promise"] or base.emotional_promise,
                    creative_boundaries=parsed["creative_boundaries"] or base.creative_boundaries,
                )
        return base


def _hints(data: dict) -> str:
    if not data:
        return (
            "No brief provided. Invent a coherent Softbound show bible: gentle, unhurried, "
            "early-childhood–appropriate; co-play friendly; no gamification or fear-as-hook."
        )
    parts = []
    for k, v in data.items():
        if isinstance(v, (dict, list)):
            parts.append(f"{k}: {v!s}")
        else:
            parts.append(f"{k}: {v}")
    return "Creator / product hints (use as anchors; still complete all four blocks):\n" + "\n".join(parts)


def _parse_delimited(text: str) -> dict[str, str] | None:
    if not (text or "").strip():
        return None
    keys = [mk for mk, _ in _MARKERS]
    pattern = re.compile(
        r"---\s*(" + "|".join(keys) + r")\s*---",
        re.IGNORECASE | re.MULTILINE,
    )
    matches = list(pattern.finditer(text))
    if not matches:
        return None
    field_by_marker = {mk: fld for mk, fld in _MARKERS}
    out: dict[str, str] = {fld: "" for _, fld in _MARKERS}
    for i, m in enumerate(matches):
        raw = m.group(1).upper()
        fld = field_by_marker.get(raw)
        if not fld:
            continue
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[fld] = text[m.end() : end].strip()
    if not any(out.values()):
        return None
    return out


def _fallback(data: dict) -> Intent:
    """Defaults aligned with Softbound when LLM is off or parsing fails."""
    return Intent(
        product_philosophy=data.get("product_philosophy")
        or (
            "Mission: Emotional Procedural hybrid — rhythm, reassurance, and small repeatable moves. "
            "Parents need calm co-presence without performance pressure; we reduce guilt by making "
            "slow, opt-in participation enough. Maisy Test: inclusive casting; agency within safe bounds; "
            "physical/emotional safety first; fairness without preachiness."
        ),
        artist_style=data.get("artist_style")
        or (
            "Low-stimulation, low-stakes pacing; soft edges and readable silhouettes; watercolor/paper tactility "
            "to invite orienting without chase. Quiet sound world with space for participatory pause — "
            "invite, never interrogate."
        ),
        emotional_promise=data.get("emotional_promise")
        or (
            "Home–away–home and small diagnostic beats: a question, a try, a gentle repair. "
            "Engine: refrain + strategy moment + return to calm. Failure: tiny setbacks, immediate repair, "
            "goals sized to early hierarchical planning (one clear next step)."
        ),
        creative_boundaries=data.get("creative_boundaries")
        or (
            "Non-goals: no sarcasm, no shame, no imitable danger, no fear-as-reward. "
            "Every exploration closes with home/cuddle return. "
            "| Beat | Goal |\n| --- | --- |\n| Opening stillness | Regulate attention |\n| Small problem | Name a feeling |\n| Repair | Model persistence |\n"
        ),
    )
