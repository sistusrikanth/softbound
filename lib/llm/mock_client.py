class MockLlmClient:
    """Deterministic mock LLM for local dev without an API key."""

    async def chat(self, messages: list[dict], **_kwargs) -> str:
        prompt = ""
        for message in reversed(messages):
            if message["role"] == "user":
                prompt = message["content"]
                break

        if prompt.startswith("Critique"):
            return "\n".join(
                [
                    "Strengths: clear tone and setting hooks.",
                    "Gaps: character motivations could be sharper.",
                    "Suggestions: tie each character to a faction or tension.",
                ]
            )

        if prompt.startswith("Refine"):
            return "\n".join(
                [
                    "## Refined world",
                    "A layered setting where factions compete over scarce magic.",
                    "Characters anchor the conflict with personal stakes.",
                    "Style notes are woven into atmosphere and naming.",
                ]
            )

        if prompt.startswith("Expand the description"):
            return "\n".join(
                [
                    "A sprawling city rises from the ribcage of a fallen titan,",
                    "its streets winding through bone arches and marrow-lit alleys.",
                    "Scavengers and pilgrims alike pick through relics of divine power,",
                    "while the air hums with the last whispers of a dead god's dreams.",
                ]
            )

        if prompt.startswith("Suggest"):
            return """[
  {"name": "Mira Ashford", "description": "A sharp-eyed scavenger who maps the god-bone tunnels and trades secrets for survival."},
  {"name": "Brother Cael", "description": "A weary priest who believes the dead god can still be awakened — if the city pays the price."},
  {"name": "Vex Thorn", "description": "A smuggler running contraband relics through the marrow markets, loyal only to the highest bidder."}
]"""

        if prompt.startswith("Expand the style description"):
            return "\n".join(
                [
                    "Dark fantasy with a melancholic, elegiac tone.",
                    "Visual palette: bone-white architecture, amber marrow-glow, deep shadow.",
                    "Narrative voice: lyrical but restrained, with moments of grim humor.",
                    "Pacing: slow-burn atmosphere punctuated by sudden violence.",
                    "Mood: awe at scale, grief for what was lost, dread of what stirs below.",
                ]
            )

        return "\n".join(
            [
                "## World draft",
                "An evocative setting built from the seed text.",
                "Characters are placed into factions with opposing goals.",
                "The world_style guides tone, visuals, and narrative voice.",
            ]
        )
