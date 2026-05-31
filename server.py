from __future__ import annotations

import os
from typing import Any, List, Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.world_agent import WorldAgent
from agents.world_characters_agent import WorldCharactersAgent
from agents.world_description_agent import WorldDescriptionAgent
from agents.world_style_agent import WorldStyleAgent
from lib.llm.create_client import create_llm_client, resolve_provider

port = int(os.getenv("PORT", "3000"))

app = FastAPI(title="Softbound Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    llm = create_llm_client()
    world_agent = WorldAgent(
        llm=llm,
        max_iterations=int(os.getenv("WORLD_AGENT_MAX_ITERATIONS", "3")),
    )
    world_description_agent = WorldDescriptionAgent(llm=llm)
    world_characters_agent = WorldCharactersAgent(llm=llm)
    world_style_agent = WorldStyleAgent(llm=llm)
except ValueError as error:
    raise SystemExit(f"Failed to initialize agents: {error}") from error


@app.on_event("startup")
async def startup():
    print(f"LLM provider: {resolve_provider()}")


class WorldRequest(BaseModel):
    text: str
    characters: List[Any]
    world_style: str
    mode: Literal["standalone", "agentic"] = "standalone"
    max_iterations: Optional[int] = None
    include_trace: bool = False


class ExpandDescriptionRequest(BaseModel):
    description: str
    world_style: str = ""
    characters: List[Any] = []


class SuggestCharactersRequest(BaseModel):
    text: str
    expanded_description: str = ""
    existing_characters: List[Any] = []
    world_style: str = ""
    count: int = 3


class GenerateStyleRequest(BaseModel):
    style_description: str
    text: str = ""


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/api/world")
async def generate_world(body: WorldRequest):
    try:
        result = await world_agent.run(
            text=body.text,
            characters=body.characters,
            world_style=body.world_style,
            mode=body.mode,
            max_iterations=body.max_iterations,
        )
    except Exception as error:
        print(f"World generation failed: {error}")
        raise HTTPException(
            status_code=500,
            detail={"error": "World generation failed", "detail": str(error)},
        ) from error

    payload = {
        "message": "World generated",
        "mode": result["mode"],
        "iterations": result["iterations"],
        "world": result["world"],
    }
    if body.include_trace:
        payload["trace"] = result["trace"]
    return payload


@app.post("/api/expand-description")
async def expand_description(body: ExpandDescriptionRequest):
    try:
        result = await world_description_agent.run(
            description=body.description,
            world_style=body.world_style,
            characters=body.characters,
        )
    except Exception as error:
        print(f"Description expansion failed: {error}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Description expansion failed", "detail": str(error)},
        ) from error

    return {
        "message": "Description expanded",
        "description": result["description"],
    }


@app.post("/api/suggest-characters")
async def suggest_characters(body: SuggestCharactersRequest):
    try:
        result = await world_characters_agent.run(
            text=body.text,
            expanded_description=body.expanded_description,
            existing_characters=body.existing_characters,
            world_style=body.world_style,
            count=body.count,
        )
    except Exception as error:
        print(f"Character suggestion failed: {error}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Character suggestion failed", "detail": str(error)},
        ) from error

    return {
        "message": "Characters suggested",
        "characters": result["characters"],
    }


@app.post("/api/generate-style-prompt")
async def generate_style_prompt(body: GenerateStyleRequest):
    try:
        result = await world_style_agent.run(
            style_description=body.style_description,
            text=body.text,
        )
    except Exception as error:
        print(f"Style prompt generation failed: {error}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Style prompt generation failed", "detail": str(error)},
        ) from error

    return {
        "message": "Style prompt generated",
        "style_prompt": result["style_prompt"],
    }


if __name__ == "__main__":
    import uvicorn

    print(f"Backend listening on http://localhost:{port}")
    print(f"LLM provider: {resolve_provider()}")
    uvicorn.run(app, host="0.0.0.0", port=port)
