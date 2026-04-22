# Layers 3–4: World, Story
from __future__ import annotations

import re
from typing import Any

from core.base_agent import BaseAgentMixin
from core.models import Intent, AudienceExperience, ProfileDimension, World, Story
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
    if dim_strs and (cp.interests or cp.sensitivities):
        if cp.interests:
            parts.append("also interests: " + ", ".join(cp.interests))
        if cp.sensitivities:
            parts.append("also sensitivities: " + ", ".join(cp.sensitivities))
    if audience.parent_age:
        parts.append("parent " + audience.parent_age)
    if audience.parent_job:
        parts.append(audience.parent_job)
    return ". ".join(parts) if parts else ""


def _world_context_structured(world: World) -> str:
    """Compact world summary from parsed fields (no full_output)."""
    parts: list[str] = []
    if world.rules:
        parts.append(f"World rules: {world.rules}")
    if world.physics:
        parts.append(f"Physics: {world.physics}")
    if world.moral_logic:
        parts.append(f"Moral tone: {world.moral_logic}")
    if world.visual_style:
        parts.append(f"Visual style: {world.visual_style}")
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


_STEP_HEADER_RE = re.compile(
    r"(?im)^\s*\*{0,2}\s*Step\s*([1-4])\s*:\s*"
    r"(?:Characters|World rules|Physics|Tone and visual style)\s*\*{0,2}\s*$"
)


def _parse_world_step_sections(text: str) -> dict[int, str]:
    """Split LLM world output into Step 1–4 bodies (content after each header)."""
    matches = list(_STEP_HEADER_RE.finditer(text))
    if not matches:
        return {}
    out: dict[int, str] = {}
    for i, m in enumerate(matches):
        step = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[step] = text[start:end].strip()
    return out


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
    """First sentence → moral_logic; remainder → visual_style (Step 4)."""
    block = block.strip()
    if not block:
        return "", ""
    parts = re.split(r"(?<=[.!?])\s+", block, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return "", block


class WorldAgent(BaseAgentMixin):
    """Builds the story world (rules, physics, style, characters) from Intent and Audience."""

    SYSTEM_PROMPT: str = GLOBAL_DIRECTIVE + """

You are a Story Creator for Children app called Softbound which  presents worlds with rich stories

World design: 
A world contains a collection of independent interactive stories that share characters, setting, tone, and style. A world functions as a coherence layer. It provides a shared setting, recurring characters, a consistent emotional tone, and a recognizable visual and interaction style.
The world should never pressure the child to act.

Tone and product theme:
The tone of Softbound should feel calm, safe, curious, warm, and unhurried. Avoid urgency, pressure, high stimulation, rewards, gamification, fear, danger, failure, or explicit moral lessons. Silence, pauses, and stillness are welcome. A child should be able to watch, listen, turn pages slowly, or stop at any point without consequence.
The primary goal is to create stories that feel like turning pages in a quiet room, visiting a familiar place in a new way, and experiencing a moment worth returning to. Softbound stories are page-based, experiential moments within a shared world. They are not games, episodes, or lessons.

You define the world in which stories may occur: rules, characters, and logic. You do NOT write the story or plot.
Your output must be exactly four sections with these headers. Write only the section content after each header; no chat, no preamble.

Format your reply like this:

Step 1: Characters
- [Name] ([role]): one-line description.
- Repeat for each character (1–5 characters).

Step 2: World rules
- 2–4 short rules (what is allowed, expected, or how things work in this world).

Step 3: Physics
- How the world works physically in 1–3 sentences (gravity, time, nature, cause and effect). Keep it simple and child-appropriate.

Step 4: Tone and visual style
- One short paragraph: emotional tone of the world, then how it looks (light, colors, setting)."""

    USER_PROMPT_TEMPLATE: str = (
        "{context}\n\n"
        "Produce the four sections now: Step 1 (Characters), Step 2 (World rules), Step 3 (Physics), Step 4 (Tone and visual style). "
        "Use the exact section headers above. Write only the world design, no other commentary."
    )

    def create(self, intent: Intent, audience: AudienceExperience) -> World:
        intent_summary = _intent_summary(intent)
        audience_summary = _audience_summary(audience)
        context = (
            f"Intent: {intent_summary}\n\nAudience: {audience_summary}"
            if (intent_summary.strip() or audience_summary.strip())
            else "Intent: (none given). Audience: (none given). Create a gentle, age-appropriate story world."
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
        """Parse Step 1–4 sections; always keep verbatim text in `full_output`."""
        text = (response or "").strip()
        if not text:
            return self._fallback(intent, audience)
        full_output = text
        sections = _parse_world_step_sections(text)
        if sections:
            characters = _parse_character_lines(sections.get(1, ""))
            rules = _clean_bullet_section(sections.get(2, ""))
            physics = _clean_bullet_section(sections.get(3, ""))
            tone_block = sections.get(4, "").strip()
            moral_logic, visual_style = _split_tone_block(tone_block)
            if not visual_style and tone_block:
                moral_logic, visual_style = "", tone_block
            return World(
                rules=rules,
                physics=physics,
                moral_logic=moral_logic,
                visual_style=visual_style,
                characters=characters,
                full_output=full_output,
                extra={},
            )
        return World(
            rules="",
            physics="",
            moral_logic="",
            visual_style="",
            characters=[],
            full_output=full_output,
            extra={"parse_note": "no_step_headers_matched"},
        )

    def _fallback(self, intent: Intent, audience: AudienceExperience) -> World:
        world = World(
            rules="gentle, forgiving",
            physics="soft-realism",
            moral_logic="curiosity rewarded",
            visual_style=intent.artist_style or "sketch",
            full_output="",
        )
        world.characters = self.create_characters(audience)
        return world

    def create_characters(self, audience: AudienceExperience) -> list[dict]:
        cp = audience.child_profile
        age_range = cp.age_range if cp else ""
        emotional_needs = cp.emotional_needs if cp else ""
        interests = ", ".join(cp.interests) if cp and cp.interests else ""
        audience_summary = _audience_summary(audience)
        user = (
            f"Child: age {age_range or '?'}, needs {emotional_needs or '?'}, interests {interests or 'none'}. "
            f"Parent: age {audience.parent_age or '?'}, job {audience.parent_job or '?'}. "
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
    """Builds story (theme, arc) from WorldAgent output."""

    STORY_SYSTEM_PROMPT: str = GLOBAL_DIRECTIVE + """

Tone and product theme:
The tone of Softbound should feel calm, safe, curious, warm, and unhurried. Avoid urgency, pressure, high stimulation, rewards, gamification, fear, danger, failure, or explicit moral lessons. Silence, pauses, and stillness are welcome. A child should be able to watch, listen, turn pages slowly, or stop at any point without consequence.
The primary goal is to create stories that feel like turning pages in a quiet room, visiting a familiar place in a new way, and experiencing a moment worth returning to. Softbound stories are page-based, experiential moments within a shared world. They are not games, episodes, or lessons.


Stories: 
Stories are experienced page by page using a calm, deliberate page-turn interaction.The primary interaction is the page turn. Additional interactions such as tapping, waiting, or gentle choices may be included, but they must always be optional, non-blocking, and subtle. If no interaction occurs, the page should remain as it is, holding the moment without demanding attention.
A story, is a fully self-contained unit. It is entered fresh, complete on its own, and does not depend on any other story. Stories do not require narrative continuity. However, multiple stories may explore similar themes, times, or situations, creating a sense of familiarity through variation rather than sequence. Stories may feel like echoes or parallel moments within the same world. For example, titles like “Rooster at Night,” “Another Night in Rooster Meadow,” and “Rooster Wakes Too Early” are thematically connected but not sequential. You must never reference events from other stories, assume memory, or create timelines or dependencies across stories.
All stories progress through discrete pages. Each page represents a single moment, a single emotional beat, and a single visual state. A page turn moves the story forward and may trigger an animation, motion, or transition, or simply reveal a new static image with text. Assume that one page equals one screen, and that page turns are calm and intentional. Nothing happens between pages unless explicitly described. Stories must not rely on continuous scrolling, real-time gameplay, or rapid interaction loops. Always think in terms of intentional, self-contained pages.
You are expected to automatically adapt stories to the developmental stage of the intended age group. This includes adjusting the number of pages, language complexity, emotional depth, pacing, and interaction density. The story must never exceed what is appropriate for the specified age.
Each story should begin in a clear and gentle state, introduce a small change, feeling, or curiosity, and then progress naturally page by page before settling into a soft resting state. Avoid hard endings or strong signals of completion. A story may pause, loop emotionally, or end in quiet observation.
When using recurring characters, maintain their core traits while allowing variation in situations. Do not reference previous stories. Characters should feel familiar, safe, and fully present in the current moment, rather than continuous across time.
Unless instructed otherwise, stories must follow a structured output format. Begin with a story title. Do not repeat or paste the full world description from the user message (that text is already provided to you as reference only). At most one short line of scene-setting if needed, then list characters if helpful. The story should unfold across pages, where each page includes a visual or moment description and short, age-appropriate text. Optional interaction notes may be included if a page turn or tap triggers a change. Finally, describe the end state, focusing on how the story settles and how it can be revisited.
Before finalizing, internally ensure that each page is simple yet meaningful, that the story works independently, that it aligns with the emotional tone of the world, that it respects the intended age group, and that it invites calm attention rather than stimulation.
.
Inputs:
You may receive inputs such as a world description, character details, visual inspiration like images or videos, an age group, interaction or page constraints, and optional thematic guidance such as “night,” “waiting,” or “quiet.” These inputs should be treated as both constraints and inspiration, not rigid instructions.

"""

    STORY_USER_PROMPT_TEMPLATE: str = (
        "{world_context}\n\n"
        "Audience age: {age_range}. Emotional promise: {emotional_promise}.\n\n"
        "Write the complete story in the structured format required in your instructions "
        "(title, then page-by-page pages with moment + text, then end state). "
        "Use up to 10 pages. Output the full story text — not a summary only. "
        "Do not duplicate the world background section in your answer."
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
        age_range = cp.age_range if cp else ""
        user = self.STORY_USER_PROMPT_TEMPLATE.format(
            world_context=world_context,
            age_range=age_range,
            emotional_promise=intent.emotional_promise or "(none)",
        )
        out = self.call_llm(user, system_content=self.STORY_SYSTEM_PROMPT)
        if not out or not out.strip():
            raise RuntimeError(
                "Story LLM returned no output; check SOFTBOUND_LLM_BACKEND, GEMINI_API_KEY, or network."
            )
        return self._parse_story_response(out)

    def _parse_story_response(self, response: str) -> Story:
        text = response.strip()
        if not text:
            raise RuntimeError("Story LLM returned empty content after strip.")
        theme = _extract_story_title(text)
        return Story(
            theme=theme,
            emotional_arc=[],
            rhythm="",
            genre="",
            full_output=text,
            extra={},
        )


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
