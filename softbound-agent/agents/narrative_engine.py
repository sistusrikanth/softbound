# Non-Aristotelian story shapes, Steve Burns–style pauses, 5–7 goal hierarchies, Maisy heuristics.
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from core.models import Intent, StoryArchetype, AudienceExperience, TheoryOfMindStatus

# In-show timing target for the “processing delay” after an invitation to respond (TTS / UI, not a Python sleep).
STEVE_BURNS_PAUSE_SECONDS_MIN = 5
STEVE_BURNS_PAUSE_SECONDS_MAX = 7


@dataclass
class ParticipatoryCue:
    """
    A single locus where narration should hold for ~5–7s so a co-viewing child can name, mimic, or answer.
    Product layer maps this to timer / audio space (Steve Burns / Blue’s Clues style).
    """

    pause_seconds_lo: int = STEVE_BURNS_PAUSE_SECONDS_MIN
    pause_seconds_hi: int = STEVE_BURNS_PAUSE_SECONDS_MAX
    after_snippet: str = ""
    purpose: str = "processing delay for child response (open field, not a quiz)"
    # Optional line index in full_output for tooling
    order: int = 0


@dataclass
class MaisyPillarResult:
    label: str
    passed: bool
    note: str


@dataclass
class MaisyTestResult:
    """
    Maisy Test — four pillars (Noggin / Nick Jr. family inclusion frame).
    Heuristic scan only; a human or LLM review should backstop for production.
    """

    gender_representation: MaisyPillarResult
    gender_freedom: MaisyPillarResult
    gender_safety: MaisyPillarResult
    social_justice: MaisyPillarResult
    overall_pass: bool
    method: str = "heuristic_regex"


# --- Archetype selection (deterministic, intent + audience) ---


def select_structural_archetype(intent: Intent, audience: AudienceExperience) -> StoryArchetype:
    t = f"{intent.emotional_promise} {intent.product_philosophy} {intent.creative_boundaries}".lower()
    a = (audience.child_profile.age_range or "") if audience.child_profile else ""
    t2 = t + " " + a.lower()

    dim_kw = (
        "sleep",
        "bed",
        "night",
        "lull",
        "rest",
        "wind down",
        "drowsy",
        "tired",
        "quiet down",
        "yawn",
        "dim",
        "lights out",
    )
    if any(k in t2 for k in dim_kw):
        return StoryArchetype.DIMINISHING

    dx_kw = (
        "doctor",
        "nurse",
        "clinic",
        "teeth",
        "tooth",
        "bath",
        "checkup",
        "ritual",
        "routine",
        "brush",
        "coat",
        "lunch",
        "calendar",
    )
    if any(k in t2 for k in dx_kw):
        return StoryArchetype.DIAGNOSTIC

    hah_kw = ("journey", "adventure", "return", "away from home", "road", "voyage", "visit", "trip", "leaving", "back home")
    if any(k in t2 for k in hah_kw):
        return StoryArchetype.HOME_AWAY_HOME

    return StoryArchetype.HOME_AWAY_HOME


def is_established_5_7(audience: AudienceExperience) -> bool:
    """Hierarchical goal structures and integrative repair fit ~5–7 (established ToM band)."""
    cp = audience.child_profile
    if not cp:
        return False
    if cp.theory_of_mind == TheoryOfMindStatus.ESTABLISHED:
        return True
    ar = (cp.age_range or "").lower()
    if re.search(r"\b(5|6|7)(?:\s*[-–—]?\s*(5|6|7))?\b", ar) or re.search(
        r"\b5\s*[-–—~]\s*7\b|first grade|6\s*[-–]7", ar
    ):
        return True
    return False


# --- Steve Burns / participatory spec ---


def steve_burns_pause_marker_line(purpose: str) -> str:
    """Text token for authors / product to interpret as 5–7s participatory hold."""
    return (
        f"[STEVE-BURNS-PAUSE {STEVE_BURNS_PAUSE_SECONDS_MIN}–{STEVE_BURNS_PAUSE_SECONDS_MAX}s: {purpose}]"
    )


def participatory_pacing_for_prompt() -> str:
    return (
        f"**Participatory cue (Steve Burns style):** After a direct invitation to the child in dialogue "
        f"(a question, “what do you see?”, or a sound to imitate), insert a line *exactly* in this form so production can "
        f"allocate **{STEVE_BURNS_PAUSE_SECONDS_MIN}–{STEVE_BURNS_PAUSE_SECONDS_MAX} seconds** of silence / processing time: "
        f'"{STEVE_BURNS_PAUSE_MARKER_PREFIX} …" (one purpose phrase). Do this **sparingly** (1–3 per short story) — *not* after every line.'
    )


STEVE_BURNS_PAUSE_MARKER_PREFIX = "[STEVE-BURNS-PAUSE 5-7s:"  # allow parser variants


def extract_participatory_cues_from_text(story_text: str) -> tuple[list[str], list[ParticipatoryCue]]:
    """
    Returns (raw marker lines, parsed cues). Markers are left in text for downstream; caller may reformat.
    """
    raw: list[str] = []
    cues: list[ParticipatoryCue] = []
    for i, line in enumerate((story_text or "").splitlines()):
        s = line.strip()
        if re.search(r"STEVE-BURNS-PAUSE|STEVE_BURNS", s, re.I) or re.search(
            r"\[PAUSE\s*[:~]?\s*5", s, re.I
        ):
            raw.append(s)
            purpose = s
            m = re.search(r"PAUSE[^\]]*:(.*?)\]", s, re.I)
            if m:
                purpose = m.group(1).strip(" ]")
            cues.append(ParticipatoryCue(after_snippet=line[:120], purpose=purpose[:200], order=len(cues) + 1))
    return raw, cues


def steve_burns_directive_block() -> str:
    return participatory_pacing_for_prompt() + " Never shame the child for not answering."


# --- Maisy (heuristic) ---


def _p(rep: MaisyPillarResult, fre: MaisyPillarResult, saf: MaisyPillarResult, soc: MaisyPillarResult) -> bool:
    return all(x.passed for x in (rep, fre, saf, soc))


def validate_maisy_test(text: str) -> MaisyTestResult:
    s = (text or "").lower()
    # Red-flag patterns (conservative; not exhaustive)
    rep_fails: list[str] = []
    if re.search(
        r"\b(all girls are|all boys are|girls (?:never|always) (?:\w+ )*(?:at|in)|boys (?:never|always))",
        s,
    ):
        rep_fails.append("broad essentialist gender line")
    if re.search(
        r"\b(princess|pretty) (?:is |who )(only|just|all about)|girls (?:are |become ).{0,30}(dumb|weak|only princes|only pretty)",
        s,
    ):
        rep_fails.append("stereotyped role wiring")

    fre_fails: list[str] = []
    if re.search(r"boys don'?t cry|girls can'?t (climb|run|lead)|real (boy|girl) (?:never|always|must )", s):
        fre_fails.append("shaming non-conformity")
    if re.search(
        r"\b(tomboy|sissy)\b.*\b(laugh|mock|weird|wrong|fix)",
        s,
    ):
        fre_fails.append("derogation of expression")

    saf_fails: list[str] = []
    if re.search(r"boyfriend|girlfriend|sexy|hot (?:for|bodies)", s):
        saf_fails.append("adult/romantic inappropriate tone")
    if re.search(r"bad (?:little )?(girl|boy) for", s) and re.search(
        r"because (he|she) (wore|likes|plays)",
        s,
    ):
        saf_fails.append("body/gendered shaming")

    soc_fails: list[str] = []
    if re.search(
        r"\b(the (?:scary|bad) (?:ghetto|hood|poor) people|thugs from|those people from)\b|ugly (?:is the )?(?:black|white|asian|mexican)",
        s,
    ):
        soc_fails.append("coded dehumanization / othering")
    if re.search(r"good side of town|those kids from that neighborhood", s) and re.search(
        r"\b(dirty|dangerous) (?:kids|people|part)",
        s,
    ):
        soc_fails.append("classism / place prejudice")

    mr = MaisyPillarResult(
        "Gender representation",
        len(rep_fails) == 0,
        "ok (heuristic)" if not rep_fails else "; ".join(rep_fails),
    )
    mf = MaisyPillarResult("Gender freedom", len(fre_fails) == 0, "ok (heuristic)" if not fre_fails else "; ".join(fre_fails))
    ms = MaisyPillarResult("Gender safety", len(saf_fails) == 0, "ok (heuristic)" if not saf_fails else "; ".join(saf_fails))
    mj = MaisyPillarResult("Social justice", len(soc_fails) == 0, "ok (heuristic)" if not soc_fails else "; ".join(soc_fails))

    return MaisyTestResult(
        gender_representation=mr,
        gender_freedom=mf,
        gender_safety=ms,
        social_justice=mj,
        overall_pass=_p(mr, mf, ms, mj),
    )


def maisy_result_to_dict(r: MaisyTestResult) -> dict[str, Any]:
    d = {
        "overall_pass": r.overall_pass,
        "method": r.method,
        "pillars": {
            p.label: {"passed": p.passed, "note": p.note}
            for p in (r.gender_representation, r.gender_freedom, r.gender_safety, r.social_justice)
        },
    }
    return d


# --- First-line arch parse from LLM ---


def archetype_composition_directive(arche: StoryArchetype) -> str:
    if arche == StoryArchetype.DIMINISHING:
        return (
            "Use a **Diminishing arc**: total sensory and narrative energy *tapers* across pages (quieter language, "
            "softer motion, dimmer or cozier light in description). Land in rest, not climax. **No** rising "
            "action that peaks in excitement; **pedagogical pacing** = co-regulation toward sleep or stillness."
        )
    if arche == StoryArchetype.DIAGNOSTIC:
        return (
            "Use a **Diagnostic arc**: small, *ritualized* beats of check-in (body, object, or feeling) with "
            "predictable, gentle repetition. Like a care visit or a familiar routine: each page can “read” a state "
            "and respond without fear. **No** mystery illness drama; keep stakes in the *procedural* comfort zone."
        )
    return (
        "Use a **Home–away–home** structure: *anchor* in a safe familiar, a **small** stretch of novelty or "
        "question (never threat), then **return** to the same kind of safety with a new tiny insight. The emotional "
        "journey is round-trip, not a single Freytag spike."
    )


def hierarchical_goals_5_7_block() -> str:
    return (
        "**5–7 band (Hierarchical goal structures + integrative repair):** The protagonist (or a helper) may "
        "*miss* a sub-goal **two or three** times in small, low-stakes ways — *never* humiliating. Each miss opens "
        "a *different* micro-strategy (ask, look again, try a new tool, invite a friend to think). The **climax** is "
        "resolved with **integrative problem solving** (combining two earlier ideas or tools), *not* luck or a "
        "punchline at someone’s expense. Shame, exclusion, and “loser” language are *forbidden*."
    )


def maisy_content_reminder() -> str:
    return (
        "**Maisy Test (internal, before you finish):** The story’s implied values must *not* betray these four "
        "pillars — (1) **gender representation** — diverse, non-essentialist roles; (2) **gender freedom** — no "
        "shaming a child for playing, dress, or feelings “wrong” for their gender; (3) **gender safety** — *no* "
        "inappropriate or sexualized child framing; (4) **social justice** — *no* coded racism, classism, or othering. "
        "If you cannot keep all four, rewrite until you can."
    )


def parse_structural_archetype_line(story_text: str) -> str | None:
    """If the model followed `STRUCTURAL_ARCHE: ...` return the value, else None."""
    for line in (story_text or "").splitlines()[:20]:
        line = line.strip()
        if re.match(r"^STRUCTURAL_?ARCHE", line, re.I) or re.match(
            r"^STRUCTURAL\s*ARCH", line, re.I
        ):
            if ":" in line:
                v = line.split(":", 1)[1].strip()
                for m in StoryArchetype:
                    if m.value in v.replace(" ", "_") or m.name in v.replace(" ", "_").upper().replace(
                        "-", "_"
                    ):
                        return m.value
                low = v.lower()
                for key, a in (
                    ("diminishing", StoryArchetype.DIMINISHING),
                    ("diagnostic", StoryArchetype.DIAGNOSTIC),
                    ("home", StoryArchetype.HOME_AWAY_HOME),
                ):
                    if key in low:
                        return a.value
    return None
