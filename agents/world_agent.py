from __future__ import annotations

import json
from typing import Any

SYSTEM_PROMPT = """You are a world-building expert for interactive fiction.
Given seed text, characters, and a style guide, you produce rich, coherent worlds.
Stay consistent with provided characters. Honor the world_style for tone and aesthetics.
Output clear markdown sections when helpful."""


def format_characters(characters: list[Any]) -> str:
    if not characters:
        return "(none provided)"

    lines = []
    for index, entry in enumerate(characters):
        if isinstance(entry, str):
            lines.append(f"{index + 1}. {entry}")
        elif isinstance(entry, dict):
            name = entry.get("name") or entry.get("id") or f"Character {index + 1}"
            details = (
                entry.get("description")
                or entry.get("role")
                or json.dumps(entry)
            )
            lines.append(f"{index + 1}. {name}: {details}")
        else:
            lines.append(f"{index + 1}. {entry}")
    return "\n".join(lines)


def build_context_block(text: str, characters: list[Any], world_style: str) -> str:
    return "\n".join(
        [
            "## Seed text",
            text,
            "",
            "## Characters",
            format_characters(characters),
            "",
            "## World style",
            world_style,
        ]
    )


class WorldAgent:
    def __init__(self, llm, max_iterations: int = 3):
        self.llm = llm
        self.max_iterations = max_iterations

    async def run_standalone(
        self, text: str, characters: list[Any], world_style: str
    ) -> dict:
        context = build_context_block(text, characters, world_style)
        world = await self.llm.chat(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": "\n".join(
                        [
                            "Create a complete world description from this input.",
                            "Include: setting, factions/conflicts, how characters fit, and style-aligned tone.",
                            "",
                            context,
                        ]
                    ),
                },
            ],
            temperature=0.7,
        )

        return {
            "mode": "standalone",
            "iterations": 1,
            "world": world,
            "trace": [{"step": "generate", "world": world}],
        }

    async def run_agentic(
        self,
        text: str,
        characters: list[Any],
        world_style: str,
        max_iterations: int | None = None,
    ) -> dict:
        limit = max_iterations if max_iterations is not None else self.max_iterations
        context = build_context_block(text, characters, world_style)
        trace = []

        world = await self.llm.chat(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": "\n".join(
                        [
                            "Draft an initial world from this input.",
                            "Keep it concise but concrete.",
                            "",
                            context,
                        ]
                    ),
                },
            ],
            temperature=0.8,
        )
        trace.append({"step": "draft", "world": world})

        for i in range(limit):
            previous_world = world

            critique = await self.llm.chat(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": "\n".join(
                            [
                                "Critique the world draft below against the original input.",
                                "List strengths, gaps, and concrete improvements.",
                                "",
                                context,
                                "",
                                "## Current draft",
                                world,
                            ]
                        ),
                    },
                ],
                temperature=0.4,
            )
            trace.append({"step": f"critique_{i + 1}", "critique": critique})

            world = await self.llm.chat(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": "\n".join(
                            [
                                "Refine the world using the critique and original input.",
                                "Produce an improved full world description.",
                                "",
                                context,
                                "",
                                "## Previous draft",
                                previous_world,
                                "",
                                "## Critique",
                                critique,
                            ]
                        ),
                    },
                ],
                temperature=0.6,
            )
            trace.append({"step": f"refine_{i + 1}", "world": world})

        return {
            "mode": "agentic",
            "iterations": 1 + limit * 2,
            "world": world,
            "trace": trace,
        }

    async def run(
        self,
        text: str,
        characters: list[Any],
        world_style: str,
        mode: str = "standalone",
        max_iterations: int | None = None,
    ) -> dict:
        if mode == "agentic":
            return await self.run_agentic(
                text, characters, world_style, max_iterations
            )
        return await self.run_standalone(text, characters, world_style)
