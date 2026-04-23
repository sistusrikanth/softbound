# Parse per-page `Animation: …` lines from story text (produced by StoryAgent).
from __future__ import annotations

import re

from core.models import PageAnimationHint

_PAGE_RE = re.compile(r"^Page\s*(\d+)", re.IGNORECASE)


def parse_page_animation_hints(story_text: str) -> list[PageAnimationHint]:
    """
    Walk the story: track current page from 'Page N' lines; collect 'Animation: a | b | c' (or em-dash).
    """
    out: list[PageAnimationHint] = []
    page_index = 0
    for raw in (story_text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        pm = _PAGE_RE.match(line)
        if pm:
            page_index = int(pm.group(1))
            continue
        if not line.lower().startswith("animation:"):
            continue
        rest = line.split(":", 1)[1].strip()
        parts: list[str] = []
        if "|" in rest:
            parts = [p.strip() for p in rest.split("|", 2)]
        elif "—" in rest or "–" in rest:
            parts = [p.strip() for p in re.split(r"\s*[—–]\s*", rest, maxsplit=2)]
        else:
            # single blob — skip
            continue
        if len(parts) != 3 or not all(parts):
            continue
        out.append(
            PageAnimationHint(
                page_index=page_index,
                subject=parts[0],
                trigger=parts[1],
                effect=parts[2],
            )
        )
    return out
