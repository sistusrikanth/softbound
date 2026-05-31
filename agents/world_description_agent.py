from __future__ import annotations

from typing import Any

from agents.world_agent import format_characters

SYSTEM_PROMPT = """You are a creative writing assistant for children's story books.
Given a short description, you expand it into vivid, concrete prose.
Preserve all facts and intent from the original text; do not introduce major new plot twists.
Honor any provided style or character context for tone and consistency.
Return only the expanded description — no preamble or meta commentary."""


class WorldDescriptionAgent:
    def __init__(self, llm):
        self.llm = llm

    async def run(
        self,
        description: str,
        world_style: str = "",
        characters: list[Any] | None = None,
    ) -> dict:
        sections = ["## Description to expand", description]

        if world_style:
            sections.extend(["", "## Style context", world_style])

        if characters:
            sections.extend(["", "## Characters (for context)", format_characters(characters)])

        expanded = await self.llm.chat(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": "\n".join(
                        [
                            "Expand the description below into richer, more evocative prose.",
                            "Keep the same scope — make it more vivid and detailed, not longer in plot.",
                            "",
                            *sections,
                        ]
                    ),
                },
            ],
            temperature=0.7,
        )

        return {"description": expanded}
