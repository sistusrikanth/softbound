from __future__ import annotations

SYSTEM_PROMPT = """You are a visual and narrative style consultant for interactive fiction.
Given a style description and optional story context, you produce an expanded style prompt.
The result should cover tone, visual aesthetics, narrative voice, pacing, and mood.
Be specific and actionable — suitable as a creative brief for writers and artists.
Return only the expanded style prompt — no preamble or meta commentary."""


class WorldStyleAgent:
    def __init__(self, llm):
        self.llm = llm

    async def run(
        self,
        style_description: str,
        text: str = "",
    ) -> dict:
        sections = ["## Style description", style_description]

        if text:
            sections.extend(["", "## Story context", text])

        style_prompt = await self.llm.chat(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": "\n".join(
                        [
                            "Expand the style description below into a detailed style prompt.",
                            "Keep it cohesive and practical for world-building and storytelling.",
                            "",
                            *sections,
                        ]
                    ),
                },
            ],
            temperature=0.7,
        )

        return {"style_prompt": style_prompt}
