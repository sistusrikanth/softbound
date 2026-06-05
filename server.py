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
from agents.studio_agent import StudioAgent
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
    studio_agent = StudioAgent(llm=llm)
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


class StudioBibleGenerateRequest(BaseModel):
    seed: str
    preset_id: Optional[str] = None


class StudioBibleReviseRequest(BaseModel):
    bible: Any
    note: Any


class StudioBibleReweaveRequest(BaseModel):
    bible: Any
    characters: List[Any]


class StudioCastSeedRequest(BaseModel):
    seed: str
    preset_id: Optional[str] = None
    count: int = 3


class StudioCharacterRefineRequest(BaseModel):
    character: Any
    ask: str


class StudioCharacterFleshRequest(BaseModel):
    character: Any
    seed: str


class StudioStyleGenerateRequest(BaseModel):
    bible: Any
    direction: Any
    extra: str = ""


class StudioStoriesProposeRequest(BaseModel):
    bible: Any
    existing: List[Any] = []
    count: int = 3


class StudioStoryReviseRequest(BaseModel):
    story: Any
    ask: str


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


@app.post("/api/studio/bible/generate")
async def studio_bible_generate(body: StudioBibleGenerateRequest):
    try:
        bible = await studio_agent.generate_bible(body.seed, body.preset_id)
    except Exception as error:
        raise HTTPException(status_code=500, detail={"error": "Bible generation failed", "detail": str(error)}) from error
    return {"message": "Bible generated", "bible": bible}


@app.post("/api/studio/bible/revise")
async def studio_bible_revise(body: StudioBibleReviseRequest):
    try:
        result = await studio_agent.revise_bible(body.bible, body.note)
    except Exception as error:
        raise HTTPException(status_code=500, detail={"error": "Bible revision failed", "detail": str(error)}) from error
    return {"message": "Bible revised", **result}


@app.post("/api/studio/bible/reweave")
async def studio_bible_reweave(body: StudioBibleReweaveRequest):
    try:
        result = await studio_agent.reweave_bible(body.bible, body.characters)
    except Exception as error:
        raise HTTPException(status_code=500, detail={"error": "Bible reweave failed", "detail": str(error)}) from error
    return {"message": "Bible rewoven", **result}


@app.post("/api/studio/cast/seed")
async def studio_cast_seed(body: StudioCastSeedRequest):
    try:
        characters = await studio_agent.seed_characters(body.seed, body.preset_id, body.count)
    except Exception as error:
        raise HTTPException(status_code=500, detail={"error": "Cast seed failed", "detail": str(error)}) from error
    return {"message": "Cast seeded", "characters": characters}


@app.post("/api/studio/characters/refine")
async def studio_character_refine(body: StudioCharacterRefineRequest):
    try:
        character = await studio_agent.refine_character(body.character, body.ask)
    except Exception as error:
        raise HTTPException(status_code=500, detail={"error": "Character refine failed", "detail": str(error)}) from error
    return {"message": "Character refined", "character": character}


@app.post("/api/studio/characters/flesh")
async def studio_character_flesh(body: StudioCharacterFleshRequest):
    try:
        character = await studio_agent.flesh_character(body.character, body.seed)
    except Exception as error:
        raise HTTPException(status_code=500, detail={"error": "Character flesh failed", "detail": str(error)}) from error
    return {"message": "Character fleshed", "character": character}


@app.post("/api/studio/style/generate")
async def studio_style_generate(body: StudioStyleGenerateRequest):
    try:
        style = await studio_agent.generate_style_library(body.bible, body.direction, body.extra)
    except Exception as error:
        raise HTTPException(status_code=500, detail={"error": "Style generation failed", "detail": str(error)}) from error
    return {"message": "Style library generated", "style": style}


@app.post("/api/studio/stories/propose")
async def studio_stories_propose(body: StudioStoriesProposeRequest):
    try:
        stories = await studio_agent.propose_stories(body.bible, body.existing, body.count)
    except Exception as error:
        raise HTTPException(status_code=500, detail={"error": "Story proposal failed", "detail": str(error)}) from error
    return {"message": "Stories proposed", "stories": stories}


@app.post("/api/studio/stories/revise")
async def studio_story_revise(body: StudioStoryReviseRequest):
    try:
        story = await studio_agent.revise_story(body.story, body.ask)
    except Exception as error:
        raise HTTPException(status_code=500, detail={"error": "Story revision failed", "detail": str(error)}) from error
    return {"message": "Story revised", "story": story}


if __name__ == "__main__":
    import uvicorn

    print(f"Backend listening on http://localhost:{port}")
    print(f"LLM provider: {resolve_provider()}")
    uvicorn.run(app, host="0.0.0.0", port=port)
