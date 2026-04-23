# Layers 3–4: World, Story
from __future__ import annotations

import re
from dataclasses import replace
from typing import Any

from core.base_agent import BaseAgentMixin
from core.models import (
    CaregivingUtility,
    Intent,
    AudienceExperience,
    ProfileDimension,
    Story,
    StoryArchetype,
    TheoryOfMindStatus,
    World,
)
from .narrative_engine import (
    archetype_composition_directive,
    extract_participatory_cues_from_text,
    hierarchical_goals_5_7_block,
    is_established_5_7,
    maisy_content_reminder,
    maisy_result_to_dict,
    parse_structural_archetype_line,
    select_structural_archetype,
    steve_burns_directive_block,
    validate_maisy_test,
)
from .story_page_animations import parse_page_animation_hints
from .prompts_common import GLOBAL_DIRECTIVE


def _intent_summary(intent: Intent) -> str:
    """Summary of intent for use in prompts (from IntentAgent output)."""
    parts = []
    if intent.product_philosophy:
        parts.append("Why / philosophy: " + intent.product_philosophy)
    if intent.artist_style:
        parts.append("Mood & aesthetic: " + intent.artist_style)
    if intent.emotional_promise:
        parts.append("Themes & narrative engine: " + intent.emotional_promise)
    if intent.creative_boundaries:
        parts.append("Safety & curriculum: " + intent.creative_boundaries)
    return "\n\n".join(parts) if parts else ""


def _dim_short(d: ProfileDimension) -> str:
    if not d.label and not d.explanation:
        return ""
    return f"{d.label} — {d.explanation}" if d.label and d.explanation else (d.label or d.explanation)


def _story_development_constraints(audience: AudienceExperience) -> str:
    cp = audience.child_profile
    if not cp:
        return (
            "Development: default early-childhood pacing; pair actions with clear outcomes for toddlers when applicable. "
            "Story: **4–6** pages, **small cast**, **plain** words — avoid cutesy name sprawl (see system story rules)."
        )
    L = cp.cognitive_load_index
    ovr = "reduce beats and density" if cp.cognitive_load_exceeds_demographic else "pacing ok for band"
    br = "always make causes visible on the same page" if cp.explicit_action_consequence_bridging else "keep causality clear"
    simp = (
        "Story load: keep **one simple through-line**; default **4–6 pages** and a **small cast** "
        "(see system simplicity rules). "
    )
    if cp.cognitive_load_exceeds_demographic or cp.theory_of_mind == TheoryOfMindStatus.PRE_TOM:
        simp += "Prefer **fewer names, shorter sentences, fewer new ideas per page** (this band needs easier text)."
    return (
        f"ToM={cp.theory_of_mind.value}. Cognitive load L≈{L:.2f} ({ovr}). "
        f"Bridging: {br}. {cp.milestone_notes or 'Milestones: (infer as needed).'} {simp}"
    )


def _audience_summary(audience: AudienceExperience) -> str:
    """Summary of audience for use in prompts (from AudienceAgent output)."""
    cp = audience.child_profile
    parts: list[str] = []
    if not cp:
        return ""
    if cp.age_range:
        parts.append("age≈" + cp.age_range)
    dims = (
        ("NC", cp.narrative_cognition),
        ("Lang", cp.language_capacity),
        ("Attn", cp.attention_profile),
        ("Emo", cp.emotional_processing),
        ("Interact", cp.interaction_style),
        ("Imag", cp.imagination_mode),
        ("Familiar", cp.familiarity_anchors),
        ("Engage", cp.engagement_drivers),
    )
    dim_strs = [f"{abbr}: {s}" for abbr, dim in dims if (s := _dim_short(dim))]
    if dim_strs:
        parts.append("; ".join(dim_strs))
        if cp.milestone_notes:
            parts.append("milestones: " + cp.milestone_notes)
        parts.append("ToM=" + cp.theory_of_mind.value)
        if cp.explicit_action_consequence_bridging:
            parts.append("action–consequence bridging: on (required for pre_tom band)")
        L = int(cp.cognitive_load_index * 1000) / 1000
        if cp.cognitive_load_exceeds_demographic:
            parts.append("cognitive load L=" + str(L) + " (exceeds band; simplify)")
        else:
            parts.append("cognitive load L=" + str(L) + " (within band)")
        if cp.profile_confidence:
            parts.append("conf=" + cp.profile_confidence)
        if cp.key_assumptions:
            parts.append("assume: " + cp.key_assumptions)
    else:
        if cp.emotional_needs:
            parts.append(cp.emotional_needs)
        if cp.attention_span:
            parts.append("attention: " + cp.attention_span)
        if cp.interests:
            parts.append("interests: " + ", ".join(cp.interests))
        if cp.sensitivities:
            parts.append("sensitivities: " + ", ".join(cp.sensitivities))
        if cp.milestone_notes:
            parts.append("milestones: " + cp.milestone_notes)
        parts.append("ToM=" + cp.theory_of_mind.value)
        if cp.explicit_action_consequence_bridging:
            parts.append("action–consequence bridging: on (pre_tom band: required)")
        L2 = int(cp.cognitive_load_index * 1000) / 1000
        if cp.cognitive_load_exceeds_demographic:
            parts.append("cognitive load L=" + str(L2) + " (exceeds band; simplify)")
        else:
            parts.append("cognitive load L=" + str(L2) + " (within band)")
    if dim_strs and (cp.interests or cp.sensitivities):
        if cp.interests:
            parts.append("also interests: " + ", ".join(cp.interests))
        if cp.sensitivities:
            parts.append("also sensitivities: " + ", ".join(cp.sensitivities))
    p = audience.parent
    if p.parent_age:
        parts.append("parent " + p.parent_age)
    if p.parent_job:
        parts.append(p.parent_job)
    if p.caregiving_utility and p.caregiving_utility != CaregivingUtility.UNSPECIFIED:
        u = p.caregiving_utility
        u_note = "tantrum/reset tool" if u == CaregivingUtility.TANTRUM_MITIGATION else "co-view / mediation"
        parts.append("caregiving: " + u.value + " (" + u_note + ")")
    if p.necessity_guilt_cycle_note:
        parts.append("necessity–guilt: " + p.necessity_guilt_cycle_note[:240])
    return ". ".join(parts) if parts else ""


def _world_context_structured(world: World) -> str:
    """Compact world summary from parsed fields (no full_output)."""
    parts: list[str] = []
    if world.sensory_environment:
        parts.append(f"Sensory environment: {world.sensory_environment}")
    if world.safe_harbor:
        parts.append(f"Safe Harbor (bibliotherapeutic): {world.safe_harbor}")
    if world.rules:
        parts.append(f"World rules: {world.rules}")
    if world.physics:
        parts.append(f"Physical world: {world.physics}")
    if world.interaction_physics:
        parts.append(f"Interaction / digital physics: {world.interaction_physics}")
    if world.visual_pacing:
        parts.append(f"Visual pacing (orienting): {world.visual_pacing}")
    if world.moral_logic:
        parts.append(f"Moral tone: {world.moral_logic}")
    if world.visual_style:
        parts.append(f"Look: {world.visual_style}")
    if world.characters:
        lines = []
        for c in world.characters:
            if isinstance(c, dict):
                name = c.get("name", "?")
                role = c.get("role", "")
                lines.append(f"{name} ({role})" if role else str(name))
            else:
                lines.append(str(c))
        if lines:
            parts.append("Characters: " + "; ".join(lines))
    return "\n".join(parts)


def _world_context_for_story_prompt(world: World) -> str:
    """
    Context for the story LLM. Avoids pasting all of `full_output` and then asking the model
    to emit another "world context" block (which duplicates what was in the user message).
    """
    structured = _world_context_structured(world).strip()
    if structured:
        return (
            structured
            + "\n\nAuthor instructions: The above is background only. Do not repeat or paste it into your "
            "story output. Begin with the story title, then page-by-page story text only (no second full "
            "world specification)."
        )
    raw = (world.full_output or "").strip()
    if raw:
        limit = 2800
        excerpt = raw if len(raw) <= limit else raw[:limit] + "…"
        return (
            "World design (excerpt — do not copy into your reply):\n"
            + excerpt
            + "\n\nAuthor instructions: Do not reproduce the block above in your output. Write only title, "
            "characters if needed, and page-by-page story."
        )
    return (
        "(No structured world fields; infer from intent.)\n\n"
        "Author instructions: Write title and page-by-page story only."
    )


def _parse_numbered_step_bodies(text: str) -> dict[int, str]:
    """Split by `Step N: ...` headers; return step number -> body (flexible header titles)."""
    text = (text or "").replace("\r\n", "\n")
    pat = re.compile(r"^\s*Step\s*(\d+)\s*:\s*[^\n]*$", re.IGNORECASE | re.MULTILINE)
    matches = list(pat.finditer(text))
    if not matches:
        return {}
    out: dict[int, str] = {}
    for i, m in enumerate(matches):
        n = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[n] = text[start:end].strip()
    return out


def _interactive_product_hint(intent: Intent) -> bool:
    t = f"{intent.product_philosophy}\n{intent.creative_boundaries}\n{intent.emotional_promise}\n{intent.artist_style}".lower()
    return any(
        w in t
        for w in (
            "tap",
            "tapping",
            "gesture",
            "shake",
            "tilt",
            "interactive",
            "touch the screen",
            "touch-friendly",
        )
    )


def _is_emergent_3_5(audience: AudienceExperience) -> bool:
    cp = audience.child_profile
    if not cp:
        return False
    if cp.theory_of_mind == TheoryOfMindStatus.EMERGENT:
        return True
    ar = (cp.age_range or "").lower()
    if re.search(r"\b(3|4|5)\s*[-–—~]\s*(3|4|5)\b", ar) or re.search(
        r"\b3\s*[-–—~]\s*5\b|preschool|3[-–]4|3[-–]5", ar
    ):
        return True
    return False


def _sensory_orienting_brief(intent: Intent, audience: AudienceExperience) -> str:
    """Context block for the world LLM: visual pacing, amygdala-safe design, 3–5 case, interactive hint."""
    lines: list[str] = []
    if _is_emergent_3_5(audience):
        lines.append(
            "Age band 3–5 (emergent / preschool): **Orienting response**—keep visual pacing SLOW. "
            "Favor *longer shot holds* (let each beat land before any cut or motion change), "
            "a low rate of new visual information per minute, and **only low-stakes environmental** friction "
            "(a stuck leaf, a damp sock, a cloudy sky) — *never* high-arousal threat, chase, or shaming. "
            "Constrain any conflict to the environment, not the child’s self-worth."
        )
    else:
        lines.append(
            "**Orienting / stimulation:** Design for a calm *orienting response*; avoid fast cuts, strobing, "
            "jarring color jumps, or predatory camera moves that spike amygdala load. Favor stillness, breath, and clarity."
        )
    lines.append(
        "**Safe Harbor (bibliotherapeutic):** The world is a *harbor*, not a battlefield. Unknowns appear as **creatures "
        "with needs** (hungry, lost, too loud, too cold) — **never** as *villains* or as figures who want to *harm* the child. "
        "Name repair and co-regulation, not retribution."
    )
    if _interactive_product_hint(intent):
        lines.append(
            "**Digital / magical thinking:** The experience may be *interactive* — if so, every tap, shake, or hold must "
            "have an **immediate, visible, on-screen** consequence (a puff of pollen, a lamp dims, a door peeks) so cause "
            "and effect is legible. Avoid delayed or off-screen 'magic' the child cannot see. If the product is *not* "
            "interactive, state that interaction is page-turn or passive view only, with no required gestures."
        )
    else:
        lines.append(
            "**Interactivity (default static):** Assume *page turn or passive look-listen* unless the intent explicitly "
            "calls for on-screen touch; in that case design legible, immediate *magical-thinking* micro-feedback on gesture."
        )
    return "\n\n".join(lines)


def _clean_bullet_section(section: str) -> str:
    lines: list[str] = []
    for line in section.splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"^[-*•]\s*", "", line)
        lines.append(line)
    return "\n".join(lines)


def _parse_character_lines(section: str) -> list[dict[str, Any]]:
    chars: list[dict[str, Any]] = []
    for line in section.splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^[-*•]\s*(.+?)\s*\(([^)]+)\)\s*:\s*(.*)$", line)
        if m:
            chars.append(
                {
                    "name": m.group(1).strip(),
                    "role": m.group(2).strip(),
                    "description": m.group(3).strip(),
                }
            )
            continue
        m = re.match(r"^[-*•]\s*(.+?)\s*:\s*(.+)$", line)
        if m:
            chars.append(
                {
                    "name": m.group(1).strip(),
                    "role": "",
                    "description": m.group(2).strip(),
                }
            )
            continue
        m = re.match(r"^[-*•]\s*(.+)$", line)
        if m:
            chars.append({"name": m.group(1).strip(), "role": "", "description": ""})
    return chars


def _split_tone_block(block: str) -> tuple[str, str]:
    """First sentence → moral_logic; remainder → visual_style (Step 4 or Step 6 tail)."""
    block = block.strip()
    if not block:
        return "", ""
    parts = re.split(r"(?<=[.!?])\s+", block, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return "", block


def _step1_header_title(text: str) -> str:
    m = re.search(r"^\s*Step\s*1\s*:\s*(.+)$", text, re.IGNORECASE | re.MULTILINE)
    return (m.group(1) or "").strip() if m else ""


def _split_natural_interaction_physics(block: str) -> tuple[str, str]:
    """First paragraph = embodied/natural; second = interactive (magical thinking) if present."""
    t = (block or "").strip()
    if not t:
        return "", ""
    if "\n\n" in t:
        a, b = t.split("\n\n", 1)
        if b.strip():
            return a.strip(), b.strip()
    lines = t.splitlines()
    for i, line in enumerate(lines):
        s = line.strip()
        if re.match(
            r"(?i)^(?:\*\*?\s*)*(?:Interactive|Digital|Magical|Gesture|On-screen|Touch|Tap|Shake|Hold)\b",
            s,
        ) or re.match(
            r"(?i)^(?:\*\*?\s*)*interactive\s*[/&]\s*digital",
            s,
        ):
            a = "\n".join(lines[:i]).strip()
            b = "\n".join(lines[i:]).strip()
            return a, b
    if re.search(r"(?i)^(interactive|digital|magical|gesture|tap|shake)\b", t):
        return "", t
    return t, ""


def _split_pacing_and_tone_look(block: str) -> tuple[str, str, str]:
    """First paragraph = visual / orienting pacing; remainder → moral + look."""
    t = (block or "").strip()
    if not t:
        return "", "", ""
    if "\n\n" in t:
        p1, rest = t.split("\n\n", 1)
        ml, vis = _split_tone_block(rest)
        if not vis and rest:
            ml, vis = "", rest
        return p1.strip(), (ml or "").strip(), (vis or "").strip()
    ml, vis = _split_tone_block(t)
    return "", (ml or "").strip(), (vis or "").strip()


def _str_defaults_for_world(intent: Intent, audience: AudienceExperience) -> dict[str, str]:
    p = (
        "Calm *orienting*: hold on each still or slow beat long enough to register; avoid strobe, whip-pans, "
        "or sudden high-contrast flashes. Favor a single clear focal point per moment."
    )
    if _is_emergent_3_5(audience):
        p += " **3–5 band: longer shot durations**, *very* slow visual rhythm, and **only low-stakes environmental** friction (weather, a stuck zipper on a leaf, a sleepy cloud)—*never* personal threat, chase, or shame."
    if _interactive_product_hint(intent):
        ip = (
            "If the build is interactive: each tap, shake, or short hold should produce a **synchronous, visible, "
            "on-surface* response (e.g. puff of dust, gentle bounce, a sound that matches the motion) — *magical thinking* "
            "in the Piagetian sense: the world answers the body right away, with no hidden off-screen result."
        )
    else:
        ip = "Assume **page turn / passive view**: no required gestures; if touch exists later, it must be optional and one-to-one with visible effect."
    return {
        "sensory_environment": "Light is soft and readable; air and sound are gentle; surfaces feel tactile; scale is friendly; the space breathes and does not race.",
        "safe_harbor": "A **bibliotherapeutic** harbor: unfamiliar beings carry *needs* (hungry, lost, too loud) — *never* villainy or the intent to harm. The tone allows repair, co-regulation, and curiosity without punishment arcs.",
        "visual_pacing": p,
        "interaction_physics": ip,
    }


def _apply_string_defaults(w: World, intent: Intent, audience: AudienceExperience) -> World:
    d = _str_defaults_for_world(intent, audience)
    o = w
    for k, v in d.items():
        if getattr(o, k) == "":  # type: ignore[misc]
            o = replace(o, **{k: v})
    return o


def _build_world_six(sections: dict[int, str], full_output: str) -> World:
    s1 = sections.get(1, "")
    s2 = sections.get(2, "")
    s3 = sections.get(3, "")
    s4 = sections.get(4, "")
    s5 = sections.get(5, "")
    s6 = sections.get(6, "")
    n_phys, i_phys = _split_natural_interaction_physics(s5)
    vp, ml, vs = _split_pacing_and_tone_look(s6)
    n_phys = _clean_bullet_section(n_phys) if n_phys else n_phys
    s3_c = _clean_bullet_section(s3) if s3 else s3
    s4_c = _clean_bullet_section(s4) if s4 else s4
    if i_phys:
        i_phys = i_phys.strip()
    return World(
        sensory_environment=s1.strip(),
        safe_harbor=(s3_c or s3).strip() if s3 else "",
        rules=(s4_c or s4).strip() if s4 else "",
        physics=(n_phys or s5).strip() if s5 else "",
        interaction_physics=i_phys,
        visual_pacing=vp,
        moral_logic=ml,
        visual_style=vs,
        characters=_parse_character_lines(s2) if s2 else [],
        extra={},
        full_output=full_output,
    )


def _build_world_legacy(sections: dict[int, str], full_output: str) -> World:
    s1, s2, s3, s4 = (sections.get(i, "") for i in range(1, 5))
    phys_raw = (s3 or "").strip()
    n_phys, i_phys = _split_natural_interaction_physics(phys_raw)
    if not i_phys and phys_raw:
        n_phys = _clean_bullet_section(phys_raw) or phys_raw
    tone_block = (s4 or "").strip()
    m, v = _split_tone_block(tone_block) if tone_block else ("", "")
    if not v and tone_block:
        m, v = "", tone_block
    return World(
        sensory_environment="",
        safe_harbor="",
        rules=_clean_bullet_section(s2) if s2 else "",
        physics=n_phys,
        interaction_physics=i_phys,
        visual_pacing="",
        moral_logic=m,
        visual_style=v,
        characters=_parse_character_lines(s1) if s1 else [],
        extra={},
        full_output=full_output,
    )


def _is_sensory_six_format(text: str, sections: dict[int, str]) -> bool:
    t1 = _step1_header_title(text).lower()
    if "sensory" in t1:
        return True
    if not sections:
        return False
    if max(sections) >= 6:
        return True
    if "safe harbor" in t1 or "bibliotherapeutic" in t1:
        return True
    return False


def _parse_llm_to_world(
    text: str, full_output: str, intent: Intent, audience: AudienceExperience
) -> World:
    sections = _parse_numbered_step_bodies(text)
    if not sections:
        w = World(
            extra={"parse_note": "no_step_headers_matched"},
            full_output=full_output,
        )
        return _apply_string_defaults(w, intent, audience)
    if _is_sensory_six_format(text, sections):
        for i in range(1, 7):
            sections.setdefault(i, "")
        w = _build_world_six(sections, full_output)
    else:
        w = _build_world_legacy(sections, full_output)
    return _apply_string_defaults(w, intent, audience)


class WorldAgent(BaseAgentMixin):
    """Builds sensory environments and story worlds from Intent and Audience (Safe Harbor, orienting pacing)."""

    SYSTEM_PROMPT: str = GLOBAL_DIRECTIVE + """

You are a **sensory environment and world** designer for the children’s app *Softbound*. Your job is **not** a one-line
“setting” label, but a **lived, embodied place**: light quality, air, sound, materials, scale, and the **felt speed of
time** in the space. Worlds hold independent page-based stories; they are coherence layers for character, **felt safety**,
**orienting (visual) pacing**, and (when relevant) **digital physics**.

**Orienting response & amygdala load:** Favor a calm, orienting first look—clear focal points, unhurried rhythm, and **stimulation
the child can metabolize**. Avoid whiplash cuts, strobing, or lurid color jumps. For the **3–5 / preschool** band, specify
**longer shot or beat duration**, fewer simultaneous novel objects, and **only low-stakes environmental** friction
(e.g. weather, a crumpled paper boat, a sleepy puddle) — *never* shame, personal threat, chase, or “gotcha” tension.

**Bibliotherapeutic “Safe Harbor”:** The world is a **harbor, not a battlefield**. Anything unfamiliar appears as
**a creature (or person) with a *need*—cold, lost, too loud, lonely** — **never** a **villain** who *wants to hurt* the
child. Repair, comfort, and curiosity; no retribution arcs, no “defeat the bad one.”

**Interaction / “magical thinking” (if touch or motion exists):** When the product is *interactive* (tap, hold, shake),
describe **digital physics** as **Piagetian magical thinking**: a gesture produces an **immediate, *visible*, on-screen**
effect (a puff, a wobble, a gentle sound that matches) — *no* delayed, hidden, or off-surface “magic.” If the experience
is *not* interactive, state **page turn / look-listen only** and that gestures are *not* required.

You do **not** write a story; you only define the world. Do **not** pre-write plots.

Output must be **exactly six** sections, with these line headers, in order. After each header, only that section’s content.
No preamble or closing commentary.

Step 1: Sensory environment
(2–5 short sentences: light, air or wind, **sound** profile, **touch / materials**, **scale** (child-sized or cozy),
and *how time feels* here. Avoid generic “a forest / a room” with no sense data.)

Step 2: Characters
- **1–3 roles max**; prefer *plain* labels (*the child*, *a cat*, *Grandma*, *a rooster*) over a cast of
  cutesy brandable names. At most **one** optional first name if a named hero helps; do **not** list many
  *Pip*/*Tizzy*/*Bop*-style bit players — fewer characters, easier stories.
- Format: [Name or role] ([part in the world]): one short line each.

Step 3: Safe Harbor (bibliotherapeutic)
(How unknown beings / strangers show up: **needs not villainy**; 2–4 short lines or a tight paragraph. Name co-regulation,
comfort, and curiosity. No “evil / monster / get them” language.)

Step 4: World rules
- 2–4 bullets: what is *allowed* and *expected* in this space (prosocial, non-shaming, optional participation).

Step 5: Natural and interactive physics
**Natural / embodied** paragraph: gravity, weather, how objects *feel* to move, slow cause→effect in the environment.

Then a **second paragraph** (or line starting `Interactive / digital:`): if *interactive* per your brief, how **tap, shake, hold,**
or **turn** nudges **one visible, immediate, on-surface** change. If *not* interactive, write `Interactive / digital: not applicable—static or page-only.`

Step 6: Visual pacing, tone, and look
**First paragraph — orienting / visual pacing:** e.g. beat length, one focal point per screen, how often the frame or
composition may change, **especially for 3–5: longer held shots / calmer transitions** and **low-stakes environmental** only.

**Second paragraph —** emotional *tone* and *how* it *looks* (color, line, light, set dressing). **Blank line** between
the two paragraphs.
"""

    USER_PROMPT_TEMPLATE: str = (
        "{context}\n\n"
        "Produce **all six** sections: Step 1 Sensory — Step 2 Characters — Step 3 Safe Harbor — "
        "Step 4 World rules — Step 5 Natural + interactive physics — Step 6 (two paragraphs) pacing, then look & tone. "
        "Use the exact headers from the system message. No other text."
    )

    def create(self, intent: Intent, audience: AudienceExperience) -> World:
        intent_summary = _intent_summary(intent)
        audience_summary = _audience_summary(audience)
        orienting = _sensory_orienting_brief(intent, audience)
        block = f"Intent: {intent_summary}\n\nAudience: {audience_summary}\n\n{orienting}"
        context = (
            block
            if (intent_summary.strip() or audience_summary.strip() or orienting.strip())
            else "Intent: (none given). Audience: (none given). Create a gentle, sensory, harbor-safe, age-appropriate world."
        )
        user_prompt = self.get_user_prompt(context=context)
        if not user_prompt.strip():
            return self._fallback(intent, audience)
        out = self.call_llm(user_prompt, system_content=self.get_system_prompt() or "")
        if not out or not out.strip():
            return self._fallback(intent, audience)
        # Detect echo: some small/local models return the user prompt instead of a real reply
        out_s, up_s = out.strip(), user_prompt.strip()
        if out_s == up_s or (len(out_s) > 80 and out_s in up_s) or (len(out_s) > 50 and up_s.startswith(out_s)):
            print("============= World Agent: LLM echoed the prompt (no real reply); using fallback world =============")
            return self._fallback(intent, audience)
        print("============= World Agent output (LLM response) =============\n" + out.strip() + "\n==========================================")
        return self._parse_llm_response(out, intent, audience)

    def _parse_llm_response(
        self, response: str, intent: Intent, audience: AudienceExperience
    ) -> World:
        """Parse 6-step sensory world or 4-step legacy; keep verbatim in `full_output` and back-fill defaults."""
        text = (response or "").strip()
        if not text:
            return self._fallback(intent, audience)
        return _parse_llm_to_world(text, text, intent, audience)

    def _fallback(self, intent: Intent, audience: AudienceExperience) -> World:
        w = World(
            sensory_environment="Soft, diffused daylight; gentle ambient sound; child-scale furniture and textures; the room and air feel unhurried.",
            safe_harbor="Unfamiliar beings are awkward, lonely, or need warmth — *never* evil or out to get anyone. Co-regulation and small repairs happen in the open.",
            rules="Gentle, forgiving; no shame; no demands to perform; curiosity is always allowed; leave outs are honored.",
            physics="Soft, readable cause→effect: objects move a little, slowly; time does not race.",
            interaction_physics="Page-turn or look-listen unless the product adds touch — then one visible micro-effect per light gesture, optional.",
            visual_pacing="Slow orienting: one clear center of interest per moment; for 3–5, *long* holds, soft transitions, only small environmental hiccups.",
            moral_logic="Curiosity and quiet courage; warmth without moralizing",
            visual_style=intent.artist_style or "soft watercolor, warm paper, breathing edges",
            characters=[],
            full_output="",
        )
        w = replace(w, characters=self.create_characters(audience) or w.characters)
        return _apply_string_defaults(w, intent, audience)

    def create_characters(self, audience: AudienceExperience) -> list[dict]:
        cp = audience.child_profile
        age_range = cp.age_range if cp else ""
        emotional_needs = cp.emotional_needs if cp else ""
        interests = ", ".join(cp.interests) if cp and cp.interests else ""
        audience_summary = _audience_summary(audience)
        par = audience.parent
        user = (
            f"Child: age {age_range or '?'}, needs {emotional_needs or '?'}, interests {interests or 'none'}. "
            f"Parent: age {par.parent_age or '?'}, job {par.parent_job or '?'}. "
            "Suggest 1–2 story characters (name and role). One short line per character."
        )
        if not audience_summary:
            user = "Audience: (unspecified). " + user
        else:
            user = "Audience: " + audience_summary + "\n\n" + user
        out = self.call_llm(user, system_content=GLOBAL_DIRECTIVE + "\n Create a world that forms the foundation for stories.")
        if out:
            return self._parse_characters_response(out)
        return []

    def _parse_characters_response(self, response: str) -> list[dict]:
        return []

    def refine_world(self, world: Any, iteration: int) -> Any:
        """Refine a world session over iterations (orchestrator flow). world must have .name, .rules (list), .characters (list), .moral_logic, .visual_style."""
        if iteration == 1:
            world.rules.append("Animals speak softly and kindly")
            world.characters.append("Rollo the Rooster")
            world.moral_logic = "Helping others brings quiet joy"
            world.visual_style = "soft morning light, grassy meadow"
        elif iteration == 2:
            world.rules.append("Problems are small and solvable")
            world.characters.append("Mabel the Meadow Mouse")
        elif iteration == 3:
            world.rules.append("Every day begins with a gentle crow")
            world.characters.append("Old Willow Tree")
        return world


class StoryAgent(BaseAgentMixin):
    """Narrative engine: non-Aristotelian archetypes, Steve Burns pauses, 5–7 hierarchical goals, Maisy check."""

    STORY_SYSTEM_PROMPT: str = GLOBAL_DIRECTIVE + """
Narrative engine (Softbound) — *non-Aristotelian* shapes, pedagogical pacing, participatory *Steve Burns* pauses, 5–7
**hierarchical goals**, and **Maisy** ethics. Page-turn primary; *no* pasted world block; self-contained story.

**Simplicity (always):** The story should feel **easy to follow**, not clever or busy.
- **Length:** Aim for **4–6 pages** (7 only for older / established ToM if the brief needs it; avoid padding to 8–10).
- **Cast & names:** Prefer **roles and relationships** over proper names: *a child*, *the dog*, *a neighbor*, *the river*.
  Use **at most one** main proper name in the whole story, or **none** if roles alone read clearly. **Do not** pepper
  cutesy, toy-brand-style names (e.g. Pip, Bop, Tizzy, Lala, *Name the Noun*) or introduce a **new** named friend each page.
- **Per page:** One main *moment* or *image*; short lines; one new idea at a time. No subplots, no twist pile-on.
- **Vocabulary & syntax:** Concrete, common words; short sentences. Skip figurative stack-ups and name soup.

**Archetype (one line, first; values: `diminishing` | `diagnostic` | `home_away_home`):** First line: `STRUCTURAL_ARCHE: <one word>`.

* **Diminishing:** taper energy, language, and *visual busyness* toward *rest* / co-regulation — *not* a last-page spike.
* **Diagnostic:** *ritualized* gentle "check" beats; predictable, kind; *no* scary clinic drama.
* **Home–away–home:** *small* away-stretch, then *return* to a familiar *felt* safety; round-trip, not conquest.

**Participatory (Steve Burns pause):** After a real *invitation* to the child (question / imitate / name), add:
`[STEVE-BURNS-PAUSE 5-7s: <label>]` for **5–7s** of processing time in production. **1–3** per full story, not dense.

**5–7 (when the brief fits established ToM / early school):** *Hierarchical* sub-goals: *small* misses, then
*integrative* climax — combine earlier tries. *No* humiliation, no piling on.

**Maisy (internal check):** Pass **(1) representation, (2) freedom, (3) safety, (4) social justice** — *no* stereotyping,
othering, or shaming. Rewrite before sending.

Then: **title**, then **pages**; end in soft *end state*.

**Page layout:** For each page start with a line `Page 1:`, `Page 2:`, etc., then the page’s text (1–2 short
paragraphs). *After* that page’s main text, you may add **at most one** optional line tying something **already on
that page** to a *possible* interaction (only a concrete person, animal, or object the reader can imagine tapping):

`Animation: <who or what on this page> | <trigger: tap, hold, or double_tap> | <one short calm effect>`

Example: `Animation: The rooster | tap | opens one eye, then settles still.`

Omit `Animation:` for a page if nothing there should respond to touch. Do not invent new subjects; the subject must
appear in that page’s main text. Calm, non-gamey motion only; no score, no “win.”

*Still:* discrete pages, one moment each; *no* other-episode memory; *no* fear/gamify hooks.
"""

    STORY_USER_PROMPT_TEMPLATE: str = (
        "{world_context}\n\n"
        "Audience age: {age_range}. Emotional promise: {emotional_promise}.\n"
        "Development: {dev_constraints}\n\n"
        "Engine **structural archetype**: {structural_archetype}.\n"
        "Composition: {archetype_composition}\n"
        "Participatory: {steve_burns}\n"
        "{hierarchical_5_7}\n"
        "Maisy: {maisy}\n\n"
        "Output: first line `STRUCTURAL_ARCHE: …` (one of diminishing | diagnostic | home_away_home), then **title**, "
        "then page-by-page story (about **4–6** pages, 7 at most if age band needs it) with `Page N:` headers. "
        "Keep the cast **small** and the language **plain** (see system simplicity rules). Include `Animation: …` lines as "
        "in system rules where a touchable story subject appears. Full text only — not a summary. Do not paste the world block back."
    )

    SYSTEM_PROMPT: str = ""
    USER_PROMPT_TEMPLATE: str = ""

    def create(
        self,
        world: World,
        intent: Intent,
        audience: AudienceExperience,
    ) -> Story:
        world_context = _world_context_for_story_prompt(world)
        return self._build_story(intent, audience, world_context)

    def _build_story(
        self,
        intent: Intent,
        audience: AudienceExperience,
        world_context: str,
    ) -> Story:
        cp = audience.child_profile
        age_range = (cp.age_range or "") if cp else ""
        arche = select_structural_archetype(intent, audience)
        h_block = (
            "\n" + hierarchical_goals_5_7_block() + "\n"
            if is_established_5_7(audience)
            else "*For the younger band: one soft try and repair is enough; no multi-fail climb.*\n"
        )
        user = self.STORY_USER_PROMPT_TEMPLATE.format(
            world_context=world_context,
            age_range=age_range or "(unspecified)",
            emotional_promise=intent.emotional_promise or "(none)",
            dev_constraints=_story_development_constraints(audience),
            structural_archetype=arche.value,
            archetype_composition=archetype_composition_directive(arche),
            steve_burns=steve_burns_directive_block(),
            hierarchical_5_7=h_block,
            maisy=maisy_content_reminder(),
        )
        out = self.call_llm(user, system_content=self.STORY_SYSTEM_PROMPT)
        if not out or not out.strip():
            raise RuntimeError(
                "Story LLM returned no output; check SOFTBOUND_LLM_BACKEND, GEMINI_API_KEY, or network."
            )
        return self._parse_story_response(out, selected_archetype=arche)

    def _parse_story_response(self, response: str, selected_archetype: StoryArchetype) -> Story:
        text = (response or "").strip()
        if not text:
            raise RuntimeError("Story LLM returned empty content after strip.")
        for_title = _strip_leading_structural_line(text)
        theme = _extract_story_title(for_title)
        from_line = parse_structural_archetype_line(text)
        structural = from_line or selected_archetype.value
        raw_markers, _cues = extract_participatory_cues_from_text(text)
        mresult = validate_maisy_test(text)
        page_animation_hints = parse_page_animation_hints(text)
        extra: dict[str, Any] = {
            "maisy_test": maisy_result_to_dict(mresult),
            "structural_archetype_engine": selected_archetype.value,
            "structural_archetype_parsed": from_line,
        }
        return Story(
            theme=theme,
            emotional_arc=[],
            rhythm=structural,
            genre=structural,
            structural_archetype=structural,
            participatory_cue_markers=raw_markers,
            page_animation_hints=page_animation_hints,
            full_output=text,
            extra=extra,
        )


def _strip_leading_structural_line(text: str) -> str:
    """Remove first `STRUCTURAL_ARCHE: ...` so title extraction works."""
    lines = (text or "").splitlines()
    if lines and re.match(r"^\s*STRUCTURAL_?ARCHE", lines[0], re.IGNORECASE):
        return "\n".join(lines[1:]).lstrip()
    return (text or "").strip()


def _extract_story_title(text: str) -> str:
    """First line, or line after 'Title:' if present."""
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith("title:"):
            return line.split(":", 1)[1].strip()[:400]
        return line[:400]
    return ""
