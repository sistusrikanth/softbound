from __future__ import annotations

import json
import re
from typing import Any

STUDIO_VOICE = """You are a calm co-author for Softbound, a calming, non-stimulating interactive picture book for toddlers ages 1.5-3.
Voice: hushed, present-tense, second person or "we", lowercase, NO exclamation marks, NO emoji, short clauses, slow and gentle.
Headings are lowercase fragments like "the place"."""

ROLES = ["place", "who", "touch"]

PRESET_BIBLES: dict[str, dict] = {
    "meadow": {
        "title": "Rooster meadow",
        "logline": "a meadow that breathes from morning into night, one quiet touch at a time.",
        "paras": [
            {
                "role": "place",
                "heading": "the place",
                "text": "the meadow sits low and warm, the colour of bread. tall grass leans where the wind last passed. a fence, a single tree, a roof in the distance. nothing hurries here. the light is always the light of late afternoon, even when the moon arrives.",
            },
            {
                "role": "who",
                "heading": "who lives here",
                "text": "a rooster keeps the meadow. he is round and unbothered, the warden of small mornings. in the grass a rabbit waits, and after dark the fireflies wake. none of them ask for attention. they are simply here, the way things in a book are here.",
            },
            {
                "role": "touch",
                "heading": "what small hands can do",
                "text": "the sky is the largest thing to touch. one press and the day folds gently into night, then back again. the rooster will crow if a child asks him to. the bush hides a rabbit who peeks, once, and settles. when the meadow goes dark, the fireflies answer a touch with a slow glow.",
            },
        ],
    },
    "lighthouse": {
        "title": "The quiet lighthouse",
        "logline": "a small keeper, a great lamp, and a coast that waits in the fog.",
        "paras": [
            {
                "role": "place",
                "heading": "the place",
                "text": "fog sits on the water like a soft grey blanket. the lighthouse stands at the edge of everything, patient and tall. below it the sea moves slowly, in no hurry to arrive. a gull folds its wings. the air smells of salt and evening.",
            },
            {
                "role": "who",
                "heading": "who lives here",
                "text": "the keeper is small, smaller than the door she opens. she climbs the stairs each evening to wake the lamp. she is not afraid of the dark, only careful with it. a cat keeps her company on the cold steps, and the boats, somewhere out there, are counting on her light.",
            },
            {
                "role": "touch",
                "heading": "what small hands can do",
                "text": "a child wakes the lamp with one touch, and its slow beam reaches into the fog. press the window and a boat finds its way home. press the water and the waves breathe once, then settle. nothing is lost for long here. the light always comes back around.",
            },
        ],
    },
    "river": {
        "title": "A little boat",
        "logline": "a slow drift downriver, past sleeping things, toward a warm harbour.",
        "paras": [
            {
                "role": "place",
                "heading": "the place",
                "text": "the river is brown and gentle and in no hurry. it carries a little boat the way a hand carries a sleeping child. reeds lean in to watch it pass. the banks are soft with moss. somewhere ahead there are lights, but the river will get there when it gets there.",
            },
            {
                "role": "who",
                "heading": "who travels here",
                "text": "the boat carries one small passenger and a folded blanket. along the banks the animals are settling: a heron on one leg, a fox curled in the ferns, ducks tucked into themselves. they stir as the boat drifts by, then sleep again. the boat does not wake them. it only passes through.",
            },
            {
                "role": "touch",
                "heading": "what small hands can do",
                "text": "a touch on the water sends one ring outward, slow and round. press a reed and it bows, then rises. press the fox and it opens one eye, then closes it. at the very end the harbour lights come on, one by one, and the boat comes to rest against the warm wood of home.",
            },
        ],
    },
}

PRESET_CASTS: dict[str, list[dict]] = {
    "meadow": [
        {
            "name": "Rooster",
            "role": "warden of small mornings",
            "tint": "clay",
            "bio": "round and unbothered, he keeps the meadow's hours. he crows only when a child asks him to, then settles back into the grass.",
            "themes": ["morning", "routine", "gentle authority"],
        },
        {
            "name": "Rabbit",
            "role": "the one who waits",
            "tint": "sage",
            "bio": "tucked in the bush, she peeks out once when touched, then is still again. she is the meadow's small, soft surprise.",
            "themes": ["patience", "hiding", "curiosity"],
        },
        {
            "name": "Fireflies",
            "role": "the evening glow",
            "tint": "honey",
            "bio": "they sleep through the day and answer a touch after dark with a slow, warm light. they ask for nothing back.",
            "themes": ["night", "wonder", "settling"],
        },
    ],
    "lighthouse": [
        {
            "name": "The keeper",
            "role": "small, careful with the dark",
            "tint": "clay",
            "bio": "smaller than the door she opens, she climbs each evening to wake the lamp. she is not afraid of the dark, only careful with it.",
            "themes": ["care", "courage", "light"],
        },
        {
            "name": "The cat",
            "role": "company on cold steps",
            "tint": "sky",
            "bio": "keeps the keeper company on the long climb. warm, quiet, easy to have near. it watches the fog with her and says nothing.",
            "themes": ["comfort", "quiet", "warmth"],
        },
    ],
    "river": [
        {
            "name": "The little boat",
            "role": "carries one small passenger",
            "tint": "sky",
            "bio": "drifts down the slow river with a folded blanket aboard. it is in no hurry, and it does not wake the sleeping banks.",
            "themes": ["drifting", "calm", "journey"],
        },
        {
            "name": "The heron",
            "role": "stands on one leg",
            "tint": "sage",
            "bio": "watches the boat pass from the reeds, then tucks its head again. it is the stillest thing on the whole river.",
            "themes": ["stillness", "watching"],
        },
        {
            "name": "The fox",
            "role": "curled in the ferns",
            "tint": "rose",
            "bio": "opens one eye when a child touches it, then closes it. asleep again before the boat has fully drifted by.",
            "themes": ["sleep", "gentleness"],
        },
    ],
}

STORY_SEEDS = [
    {"title": "the first light", "logline": "the world wakes, slowly, and learns it is safe to be touched.", "scenes": 4, "gestures": ["tap", "press"], "beats": ["the world is still, waiting", "a small hand reaches in", "something gently stirs", "it settles, changed a little"]},
    {"title": "the long afternoon", "logline": "one quiet game, repeated, the way small children love repetition.", "scenes": 5, "gestures": ["tap", "swipe"], "beats": ["the world is still, waiting", "a small hand reaches in", "something gently stirs", "it settles, changed a little", "the world is still again"]},
    {"title": "into the evening", "logline": "the light folds toward night; everything settles, one creature at a time.", "scenes": 6, "gestures": ["tap", "long press"], "beats": ["the world is still, waiting", "a small hand reaches in", "something gently stirs", "it settles, changed a little", "the world is still again"]},
]


def parse_json(raw: str) -> Any:
    text = raw.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence_match:
        text = fence_match.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


def title_from_seed(seed: str) -> str:
    s = seed.lower()
    match = re.search(
        r"\b(lighthouse|meadow|forest|river|garden|moon|mountain|harbour|harbor|island|valley|orchard|pond|cottage|hill|sea|snow|desert|cave|nest|burrow|lantern|kite|cloud)\b",
        s,
    )
    if match:
        noun = match.group(1).replace("harbor", "harbour")
        return f"The quiet {noun}"
    return "A small quiet world"


def make_bible(seed: str) -> dict:
    clean = (seed or "").strip()
    subject = clean.rstrip(".") if clean else "a small quiet place"
    return {
        "title": title_from_seed(clean),
        "logline": "a still place that wakes only when small hands ask it to.",
        "paras": [
            {
                "role": "place",
                "heading": "the place",
                "text": f"here is {subject}. it sits in the soft light of late afternoon and does not hurry. the colours are warm and worn, the way a loved page is worn. nothing moves until it is touched, and even then it moves slowly, then settles back into stillness.",
            },
            {
                "role": "who",
                "heading": "who lives here",
                "text": "someone small keeps this place — gentle, unbothered, easy to love. a few quiet companions share it: things that wait in the grass, things that sleep until evening. none of them ask for attention. they are simply here, the way things in a book are here.",
            },
            {
                "role": "touch",
                "heading": "what small hands can do",
                "text": "every touch is answered, once, and then the world goes still again. press the sky and the light changes. press a small thing and it stirs, peeks, settles. there is no score, no next, no hurry. only the quiet pleasure of making one gentle thing happen, and then another.",
            },
        ],
    }


def normalize_bible(data: dict) -> dict:
    paras = []
    for i, p in enumerate(data.get("paras") or [])[:3]:
        paras.append(
            {
                "role": ROLES[i] if i < len(ROLES) else "body",
                "heading": p.get("heading") or ROLES[i],
                "text": p.get("text") or "",
            }
        )
    while len(paras) < 3:
        idx = len(paras)
        fallback = make_bible("")["paras"][idx]
        paras.append(fallback)
    return {
        "title": data.get("title") or "A small quiet world",
        "logline": data.get("logline") or "",
        "paras": paras,
    }


class StudioAgent:
    def __init__(self, llm):
        self.llm = llm

    async def generate_bible(self, seed: str, preset_id: str | None = None) -> dict:
        if preset_id and preset_id in PRESET_BIBLES:
            return PRESET_BIBLES[preset_id]

        try:
            raw = await self.llm.chat(
                messages=[
                    {"role": "system", "content": STUDIO_VOICE},
                    {
                        "role": "user",
                        "content": "\n".join(
                            [
                                f'The author seeds an idea for a new world:\n"{seed}"',
                                'Write a short "world bible". Return ONLY JSON:',
                                '{"title": Sentence-case string, "logline": one short sentence, "paras":[{"heading": lowercase fragment, "text": 40-70 words}]}.',
                                "Exactly three paragraphs: the place, who lives here, what small hands can do.",
                            ]
                        ),
                    },
                ],
                temperature=0.7,
            )
            return normalize_bible(parse_json(raw))
        except Exception:
            return make_bible(seed)

    async def revise_bible(self, bible: dict, note: dict) -> dict:
        note_text = (note.get("text") or "").strip()
        try:
            raw = await self.llm.chat(
                messages=[
                    {"role": "system", "content": STUDIO_VOICE},
                    {
                        "role": "user",
                        "content": "\n".join(
                            [
                                f"Current world bible (JSON):\n{json.dumps(bible)}",
                                f'The author highlighted:\n"{note.get("quote", "")}"',
                                f'and left this note:\n"{note_text}"',
                                "Revise the bible so the note is honoured. Change as little as possible.",
                                'Return ONLY JSON: {"title","logline","paras":[{"heading","text"}],"summary": a 3-6 word lowercase phrase}.',
                            ]
                        ),
                    },
                ],
                temperature=0.6,
            )
            data = parse_json(raw)
            result = normalize_bible(data)
            result["summary"] = (data.get("summary") or "a small change").lower()
            return result
        except Exception:
            return self._revise_bible_local(bible, note)

    def _revise_bible_local(self, bible: dict, note: dict) -> dict:
        note_text = (note.get("text") or "").strip()
        paras = [dict(p) for p in bible.get("paras", [])]
        target_idx = max(0, next((i for i, p in enumerate(paras) if p.get("id") == note.get("para_id")), 0))
        t = paras[target_idx] if paras else {"text": ""}
        woven = f'we hold your note close — "{note_text}" — and let it settle into the page.'
        sep = " " if re.search(r"[.?!]\s*$", t.get("text", "")) else ". "
        t["text"] = t.get("text", "").rstrip() + sep + woven
        summary = " ".join(note_text.split()[:5]).lower() or "a small change"
        return {
            "title": bible.get("title", ""),
            "logline": bible.get("logline", ""),
            "paras": paras,
            "summary": summary,
        }

    async def reweave_bible(self, bible: dict, characters: list[dict]) -> dict:
        cast_desc = "\n".join(
            f'{c.get("name")} — {c.get("role")}: {c.get("bio")} (themes: {", ".join(c.get("themes") or [])})'
            for c in characters
        )
        try:
            raw = await self.llm.chat(
                messages=[
                    {"role": "system", "content": STUDIO_VOICE},
                    {
                        "role": "user",
                        "content": "\n".join(
                            [
                                f"World bible (JSON):\n{json.dumps(bible)}",
                                f"The cast has been refined:\n{cast_desc}",
                                'Rewrite the bible so it reflects this cast — especially "who lives here".',
                                'Return ONLY JSON: {"title","logline","paras":[{"heading","text"}],"summary": a 3-6 word lowercase phrase}.',
                            ]
                        ),
                    },
                ],
                temperature=0.6,
            )
            data = parse_json(raw)
            result = normalize_bible(data)
            result["summary"] = (data.get("summary") or "rewoven with the cast").lower()
            return result
        except Exception:
            return self._reweave_local(bible, characters)

    def _reweave_local(self, bible: dict, characters: list[dict]) -> dict:
        paras = [dict(p) for p in bible.get("paras", [])]
        idx = next((i for i, p in enumerate(paras) if p.get("role") == "who"), min(1, len(paras) - 1))
        names = [c.get("name", "").lower() for c in characters]
        intro = "; ".join(f'{c.get("name", "").lower()}, {c.get("role", "")}' for c in characters)
        cast_line = ", ".join(names[:-1]) + " and " + names[-1] if len(names) > 1 else names[0] if names else "they"
        paras[idx]["text"] = (
            f"{cast_line} share this place — {intro}. none of them ask for attention. "
            "they are simply here, the way things in a book are here, waiting for a small hand to reach out."
        )
        return {"title": bible.get("title", ""), "logline": bible.get("logline", ""), "paras": paras, "summary": "rewoven with the cast"}

    async def seed_characters(self, seed: str, preset_id: str | None = None, count: int = 3) -> list[dict]:
        if preset_id and preset_id in PRESET_CASTS:
            return PRESET_CASTS[preset_id][:count]

        try:
            raw = await self.llm.chat(
                messages=[
                    {"role": "system", "content": STUDIO_VOICE},
                    {
                        "role": "user",
                        "content": "\n".join(
                            [
                                f'The author seeds a new world:\n"{seed}"',
                                f"Invent {count} small characters who live here.",
                                'Return ONLY JSON: {"characters":[{"name","role": short lowercase epithet,"bio": 25-45 words,"themes":[2-3 lowercase motifs]}]}.',
                            ]
                        ),
                    },
                ],
                temperature=0.8,
            )
            data = parse_json(raw)
            chars = data.get("characters") if isinstance(data, dict) else data
            if not isinstance(chars, list):
                raise ValueError("invalid characters response")
            tints = ["clay", "sage", "sky", "honey", "rose"]
            out = []
            for i, c in enumerate(chars[:count]):
                out.append(
                    {
                        "name": c.get("name") or "a small one",
                        "role": c.get("role") or "",
                        "bio": c.get("bio") or "",
                        "themes": (c.get("themes") or [])[:3],
                        "tint": tints[i % len(tints)],
                    }
                )
            return out
        except Exception:
            return self._make_cast(seed)[:count]

    def _make_cast(self, seed: str) -> list[dict]:
        subject = (seed or "").strip() or "this world"
        return [
            {
                "name": "the keeper",
                "role": "the one who tends this place",
                "tint": "clay",
                "bio": f"someone small looks after {subject} — gentle, unhurried, easy to love. they ask for nothing and answer every touch, once, then settle.",
                "themes": ["care", "calm"],
            },
            {
                "name": "a quiet companion",
                "role": "the small surprise",
                "tint": "sage",
                "bio": "waits half-hidden until a child reaches out, then peeks, stirs, and folds back into stillness. easy to miss, lovely to find.",
                "themes": ["patience", "wonder"],
            },
        ]

    async def refine_character(self, character: dict, ask: str) -> dict:
        try:
            raw = await self.llm.chat(
                messages=[
                    {"role": "system", "content": STUDIO_VOICE},
                    {
                        "role": "user",
                        "content": "\n".join(
                            [
                                f"Character (JSON):\n{json.dumps(character)}",
                                f'The author asks for a change:\n"{ask}"',
                                'Return ONLY JSON: {"role": short lowercase epithet,"bio": 25-45 words,"themes":[2-4 lowercase motifs]}.',
                            ]
                        ),
                    },
                ],
                temperature=0.7,
            )
            data = parse_json(raw)
            return {
                **character,
                "role": data.get("role") or character.get("role", ""),
                "bio": data.get("bio") or character.get("bio", ""),
                "themes": (data.get("themes") or character.get("themes") or [])[:4],
            }
        except Exception:
            bio = character.get("bio", "")
            return {**character, "bio": f'{bio.rstrip()}. they carry your note now — "{ask.strip()}".'}

    async def flesh_character(self, character: dict, seed: str) -> dict:
        try:
            raw = await self.llm.chat(
                messages=[
                    {"role": "system", "content": STUDIO_VOICE},
                    {
                        "role": "user",
                        "content": "\n".join(
                            [
                                f'The author adds a new character, seeded as:\n"{seed}"',
                                'Return ONLY JSON: {"name","role": short lowercase epithet,"bio": 25-45 words,"themes":[2-3 lowercase motifs]}.',
                            ]
                        ),
                    },
                ],
                temperature=0.8,
            )
            data = parse_json(raw)
            return {
                **character,
                "name": data.get("name") or character.get("name", ""),
                "role": data.get("role") or "a new presence",
                "bio": data.get("bio") or "",
                "themes": (data.get("themes") or [])[:3],
            }
        except Exception:
            subj = seed.strip()
            return {
                **character,
                "name": " ".join(subj.split()[:2]) or character.get("name", ""),
                "role": "a new presence",
                "bio": f"{subj} joins this world — quiet, unhurried, answering a small hand and then settling back into stillness.",
                "themes": ["calm"],
            }

    async def generate_style_library(self, bible: dict, direction: dict, extra: str = "") -> dict:
        style_desc = f'{direction.get("name")}: {direction.get("blurb", "")}. {extra}'.strip()
        story_text = f'{bible.get("title", "")} — {bible.get("logline", "")}'
        try:
            raw = await self.llm.chat(
                messages=[
                    {"role": "system", "content": STUDIO_VOICE},
                    {
                        "role": "user",
                        "content": "\n".join(
                            [
                                f'Visual direction: "{direction.get("name")}" — {direction.get("blurb", "")}',
                                f"World: {story_text}",
                                f'Author notes: "{extra or "(nothing extra)"}"',
                                "Write a reusable style guide for an image generator.",
                                'Return ONLY JSON: {"medium","materials","palette":[4-6 colour phrases],"lighting","camera","texture","mood": 3-4 words,"negative": comma-separated avoid list,"master": ONE paste-ready prompt paragraph}.',
                            ]
                        ),
                    },
                ],
                temperature=0.7,
            )
            data = parse_json(raw)
            return {
                "name": direction.get("name", ""),
                "direction_id": direction.get("id", ""),
                "tint": direction.get("tint", "clay"),
                "medium": data.get("medium") or direction.get("medium", ""),
                "materials": data.get("materials") or direction.get("materials", ""),
                "palette": data.get("palette") or direction.get("palette", []),
                "lighting": data.get("lighting") or direction.get("lighting", ""),
                "camera": data.get("camera") or direction.get("camera", ""),
                "texture": data.get("texture") or direction.get("texture", ""),
                "mood": data.get("mood") or direction.get("mood", ""),
                "negative": data.get("negative") or "no text, no clutter, no harsh contrast",
                "master": data.get("master") or style_desc,
                "extra": extra or "",
            }
        except Exception:
            subject = bible.get("title", "this world").lower()
            master = (
                f'{direction.get("medium", "")}. {direction.get("materials", "")}. '
                f"Scene: {subject}{', ' + extra.strip() if extra else ''}. "
                f'Palette: {", ".join(direction.get("palette", []))}. '
                f'Lighting: {direction.get("lighting", "")}. {direction.get("camera", "")}. '
                f'Mood: {direction.get("mood", "")}. Calming children\'s picture-book illustration.'
            )
            return {
                "name": direction.get("name", ""),
                "direction_id": direction.get("id", ""),
                "tint": direction.get("tint", "clay"),
                "medium": direction.get("medium", ""),
                "materials": direction.get("materials", ""),
                "palette": direction.get("palette", []),
                "lighting": direction.get("lighting", ""),
                "camera": direction.get("camera", ""),
                "texture": direction.get("texture", ""),
                "mood": direction.get("mood", ""),
                "negative": "no text, no logos, no busy backgrounds, no harsh contrast",
                "master": master,
                "extra": extra or "",
            }

    async def propose_stories(self, bible: dict, existing: list[dict], count: int = 3) -> list[dict]:
        taken = {s.get("title", "").lower() for s in existing}
        try:
            have = ", ".join(s.get("title", "") for s in existing) or "none yet"
            raw = await self.llm.chat(
                messages=[
                    {"role": "system", "content": STUDIO_VOICE},
                    {
                        "role": "user",
                        "content": "\n".join(
                            [
                                f"World bible (JSON): {json.dumps({'title': bible.get('title'), 'logline': bible.get('logline'), 'paras': [p.get('text') for p in bible.get('paras', [])]})}",
                                f"Stories that already exist: {have}.",
                                f"Propose {count} NEW quiet stories. Return ONLY JSON:",
                                '{"stories":[{"title","logline","scenes": 3-6,"gestures":["tap","press"],"beats":[3-5 short scene beats]}]}.',
                            ]
                        ),
                    },
                ],
                temperature=0.8,
            )
            data = parse_json(raw)
            stories = data.get("stories") or []
            out = []
            for s in stories[:count]:
                title = s.get("title") or "a new story"
                if title.lower() in taken:
                    continue
                beats = s.get("beats") or ["the world is still, waiting", "something gently stirs", "it settles again"]
                out.append(
                    {
                        "title": title,
                        "logline": s.get("logline") or "",
                        "scenes": s.get("scenes") or len(beats),
                        "gestures": (s.get("gestures") or ["tap"])[:2],
                        "beats": [{"text": b} for b in beats],
                    }
                )
            if out:
                return out
        except Exception:
            pass

        out = []
        for seed in STORY_SEEDS:
            if seed["title"].lower() in taken:
                continue
            out.append(
                {
                    "title": seed["title"],
                    "logline": seed["logline"],
                    "scenes": seed["scenes"],
                    "gestures": seed["gestures"],
                    "beats": [{"text": b} for b in seed["beats"]],
                }
            )
            if len(out) >= count:
                break
        return out[:count]

    async def revise_story(self, story: dict, ask: str) -> dict:
        try:
            raw = await self.llm.chat(
                messages=[
                    {"role": "system", "content": STUDIO_VOICE},
                    {
                        "role": "user",
                        "content": "\n".join(
                            [
                                f'Story (JSON): {json.dumps({"title": story.get("title"), "logline": story.get("logline"), "beats": [b.get("text") for b in story.get("beats", [])]})}',
                                f'The author asks: "{ask}"',
                                'Return ONLY JSON: {"title","logline","beats":[3-5 short scene beats]}.',
                            ]
                        ),
                    },
                ],
                temperature=0.7,
            )
            data = parse_json(raw)
            beats = data.get("beats") or [b.get("text") for b in story.get("beats", [])]
            return {
                **story,
                "title": data.get("title") or story.get("title", ""),
                "logline": data.get("logline") or story.get("logline", ""),
                "beats": [{"text": b} for b in beats],
                "scenes": len(beats),
            }
        except Exception:
            return {**story, "logline": f'{story.get("logline", "")} {ask.strip()}'.strip()}
