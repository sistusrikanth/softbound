from __future__ import annotations

import json
import re
from typing import Any

from agents.world_agent import format_characters

SYSTEM_PROMPT = """You are a character designer for interactive fiction.
Given story context, you suggest compelling characters that fit the setting and tone.
Avoid duplicating existing characters. Each character needs a distinct role and voice.
Reply with a JSON array only — no markdown fences or extra text.
Each object must have: "name" (string), "description" (string, 1-2 sentences)."""


def parse_characters_json(raw: str) -> list[dict]:
    text = raw.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        text = fence_match.group(1).strip()

    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]

    parsed = json.loads(text)
    if not isinstance(parsed, list):
        raise ValueError("Expected a JSON array of characters")

    characters = []
    for entry in parsed:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        description = entry.get("description")
        if not name or not description:
            continue
        characters.append({"name": str(name), "description": str(description)})

    if not characters:
        raise ValueError("No valid characters in LLM response")

    return characters


class WorldCharactersAgent:
    def __init__(self, llm):
        self.llm = llm

    async def run(
        self,
        text: str,
        existing_characters: list[Any] | None = None,
        world_style: str = "",
        count: int = 3,
        expanded_description: str = "",
    ) -> dict:
        story_context = expanded_description.strip() or text
        sections = ["## Story / world context", story_context]

        if world_style:
            sections.extend(["", "## Style", world_style])

        if existing_characters:
            sections.extend(
                ["", "## Existing characters (do not duplicate)", format_characters(existing_characters)]
            )

        raw = await self.llm.chat(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": "\n".join(
                        [
                            f"Suggest {count} new characters for this story.",
                            "Make them varied in role, personality, and motivation.",
                            "",
                            *sections,
                        ]
                    ),
                },
            ],
            temperature=0.8,
        )

        characters = parse_characters_json(raw)
        return {"characters": characters[:count]}
