"""Save/load intent, audience, and world to a local JSON file (skip LLM layers 1–3 on load)."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .models import Intent, AudienceExperience, World

SESSION_VERSION = 1


def session_to_dict(intent: Intent, audience: AudienceExperience, world: World) -> dict[str, Any]:
    return {
        "version": SESSION_VERSION,
        "intent": intent.model_dump(),
        "audience": audience.model_dump(),
        "world": asdict(world),
    }


def session_from_dict(data: dict[str, Any]) -> tuple[Intent, AudienceExperience, World]:
    v = data.get("version", 1)
    if v != SESSION_VERSION:
        raise ValueError(f"Unsupported session version {v!r} (expected {SESSION_VERSION})")
    intent = Intent.model_validate(data["intent"])
    audience = AudienceExperience.model_validate(data["audience"])
    w = data["world"]
    world = World(
        rules=w.get("rules") or "",
        physics=w.get("physics") or "",
        moral_logic=w.get("moral_logic") or "",
        visual_style=w.get("visual_style") or "",
        characters=list(w.get("characters") or []),
        extra=dict(w.get("extra") or {}),
        full_output=w.get("full_output") or "",
    )
    return intent, audience, world


def save_session(path: Path, intent: Intent, audience: AudienceExperience, world: World) -> None:
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(session_to_dict(intent, audience, world), indent=2), encoding="utf-8")


def load_session(path: Path) -> tuple[Intent, AudienceExperience, World]:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Session file not found: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return session_from_dict(raw)
