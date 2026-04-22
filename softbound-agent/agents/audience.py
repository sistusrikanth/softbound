# Layer 2: Audience — inferred child profile (0–7) for story adaptation
from __future__ import annotations

import re

from core.base_agent import BaseAgentMixin
from core.models import AudienceExperience, ChildProfile, ProfileDimension
from .prompts_common import GLOBAL_DIRECTIVE

_CHILD_KEYS = ("age_range", "emotional_needs", "attention_span", "interests", "sensitivities")


def _normalize_input(input_data: dict) -> dict:
    if not isinstance(input_data, dict):
        input_data = {}
    cp = input_data.get("child_profile") if isinstance(input_data.get("child_profile"), dict) else {}
    child_flat: dict = {}
    for k in _CHILD_KEYS:
        v = cp.get(k) if k in cp else input_data.get(k)
        if k in ("interests", "sensitivities"):
            if isinstance(v, list):
                child_flat[k] = v
            else:
                child_flat[k] = []
        else:
            child_flat[k] = v if v is not None else ""
    return {
        "child_profile": child_flat,
        "parent_age": input_data.get("parent_age") or "",
        "parent_job": input_data.get("parent_job") or "",
        "cultural_context": input_data.get("cultural_context") or input_data.get("culture") or "",
        "coplay_context": input_data.get("coplay_context") or input_data.get("coplay") or "",
        "reading_setting": input_data.get("reading_setting") or "",
        "behavior": cp.get("behavior") or input_data.get("behavior") or "",
        "preferences": cp.get("preferences") or input_data.get("preferences") or "",
        "interactions": cp.get("interactions") or input_data.get("interactions") or "",
        "notes": cp.get("notes") or input_data.get("notes") or "",
    }


def _hints(normalized: dict) -> str:
    cp = normalized.get("child_profile") or {}
    parts: list[str] = []
    if cp.get("age_range"):
        parts.append("age≈" + str(cp["age_range"]))
    if cp.get("emotional_needs"):
        parts.append("needs: " + str(cp["emotional_needs"]))
    if cp.get("attention_span"):
        parts.append("attention: " + str(cp["attention_span"]))
    if cp.get("interests"):
        parts.append("interests: " + ", ".join(cp["interests"]))
    if cp.get("sensitivities"):
        parts.append("sensitivities: " + ", ".join(cp["sensitivities"]))
    for key, prefix in (
        ("behavior", "behavior"),
        ("preferences", "prefs"),
        ("interactions", "interactions"),
        ("cultural_context", "culture"),
        ("coplay_context", "coplay"),
        ("reading_setting", "setting"),
        ("notes", "notes"),
    ):
        if normalized.get(key):
            parts.append(prefix + ": " + str(normalized[key]))
    if normalized.get("parent_age") or normalized.get("parent_job"):
        parts.append("parent %s / %s" % (normalized.get("parent_age", ""), normalized.get("parent_job", "")))
    if not parts:
        return "No audience signals. Infer 0–7 profile; default to simple story, short attention, repetition, emotional safety."
    return "Signals (infer latent traits; age is weak): " + " | ".join(parts)


def _split_label_explanation(body: str) -> tuple[str, str]:
    body = (body or "").strip()
    if not body:
        return "", ""
    for sep in (" — ", " – ", " - "):
        if sep in body:
            a, b = body.split(sep, 1)
            if b.strip():
                return a.strip(), b.strip()
    return "", body


def _normalize_confidence(raw: str) -> str:
    s = (raw or "").strip().lower()
    for w in ("low", "medium", "high"):
        if w == s or re.search(r"\b" + re.escape(w) + r"\b", s):
            return w
    return ""


def _parse_dimension_line(line: str, label: str) -> ProfileDimension:
    body = _strip_label(line, label)
    short_label, explanation = _split_label_explanation(body)
    return ProfileDimension(label=short_label, explanation=explanation)


def _d(label: str, explanation: str) -> ProfileDimension:
    return ProfileDimension(label=label, explanation=explanation)


def _fail_safe_profile() -> ChildProfile:
    return ChildProfile(
        age_range="",
        emotional_needs="Safety and reassurance; predictable beats.",
        attention_span="short",
        interests=[],
        sensitivities=[],
        narrative_cognition=_d("Simple sequential", "Concrete beats; minimal causal chains."),
        language_capacity=_d("Simple + repetition", "Short sentences; small vocabulary."),
        attention_profile=_d("Limited", "Slow pacing; few beats per page."),
        emotional_processing=_d("Sensitive", "Low stakes; quick resolution; clear safety."),
        interaction_style=_d("Guided", "Optional prompts; not open-ended demand."),
        imagination_mode=_d("Sensory-led", "Tangible detail before abstraction."),
        familiarity_anchors=_d("Home routines", "Bedtime, meals, caretakers."),
        engagement_drivers=_d("Repetition", "Refrain + small novelty."),
        profile_confidence="low",
        key_assumptions="Minimal input; early-childhood defaults.",
    )


class AudienceAgent(BaseAgentMixin):
    SYSTEM_PROMPT = GLOBAL_DIRECTIVE + """
Infer a developmental profile for storytelling (child 0–7). Age is a weak prior—infer from behavior/context; if unsure, assume simpler development.

Output exactly 12 lines, in order:
NARRATIVE COGNITION … LANGUAGE CAPACITY … ATTENTION PROFILE … EMOTIONAL PROCESSING …
INTERACTION STYLE … IMAGINATION MODE … FAMILIARITY ANCHORS … ENGAGEMENT DRIVERS …
OVERALL CONFIDENCE: low | medium | high
KEY ASSUMPTIONS: one short line (or "none")
PARENT AGE: …
PARENT JOB: …

Lines 1–8: DIMENSION: ShortLabel — one short sentence.
No JSON or markdown."""

    USER_PROMPT_TEMPLATE = "{hints}"

    def create(self, input_data: dict) -> AudienceExperience:
        if not isinstance(input_data, dict):
            input_data = {}
        normalized = _normalize_input(input_data)
        hints = _hints(normalized)

        out = self.maybe_call_llm(hints=hints)

        if out:
            parsed = _parse(out)
            if parsed is not None:
                return _merge_with_fallback(parsed, normalized)
        return _fallback(normalized)


def _strip_label(line: str, label: str) -> str:
    m = re.match(re.escape(label) + r"\s*:?\s*", line, re.IGNORECASE)
    if m:
        return line[m.end() :].strip()
    return line.strip()


def _parse(response: str) -> AudienceExperience | None:
    raw = (response or "").strip()
    if not raw:
        return None
    lines = [ln.strip() for ln in re.sub(r"\r\n", "\n", raw).split("\n") if ln.strip()]
    if len(lines) < 8:
        return None

    dims = [
        _parse_dimension_line(lines[0], "NARRATIVE COGNITION"),
        _parse_dimension_line(lines[1], "LANGUAGE CAPACITY"),
        _parse_dimension_line(lines[2], "ATTENTION PROFILE"),
        _parse_dimension_line(lines[3], "EMOTIONAL PROCESSING"),
        _parse_dimension_line(lines[4], "INTERACTION STYLE"),
        _parse_dimension_line(lines[5], "IMAGINATION MODE"),
        _parse_dimension_line(lines[6], "FAMILIARITY ANCHORS"),
        _parse_dimension_line(lines[7], "ENGAGEMENT DRIVERS"),
    ]

    confidence = ""
    assumptions = ""
    parent_age = ""
    parent_job = ""

    if len(lines) >= 9:
        confidence = _normalize_confidence(_strip_label(lines[8], "OVERALL CONFIDENCE"))
    if len(lines) >= 10:
        assumptions = _strip_label(lines[9], "KEY ASSUMPTIONS")
    if len(lines) >= 11:
        parent_age = _strip_label(lines[10], "PARENT AGE")
    if len(lines) >= 12:
        parent_job = _strip_label(lines[11], "PARENT JOB")

    emo, att, eng = dims[3], dims[2], dims[7]
    emo_txt = "; ".join(x for x in (emo.label, emo.explanation) if x)
    att_txt = (att.label + " " + att.explanation).lower()
    attention_span = (
        "short" if any(w in att_txt for w in ("short", "brief", "limited"))
        else "long"
        if "long" in att_txt or "extended" in att_txt
        else ("medium" if (att.label or att.explanation) else "")
    )
    interests = [eng.label] if eng.label else []
    sens_txt = emo_txt.lower()
    sensitivities = (
        ["intense emotion"] if any(w in sens_txt for w in ("sensitiv", "anxious", "fear", "overwhelm")) else []
    )

    child = ChildProfile(
        age_range="",
        emotional_needs=emo_txt,
        attention_span=attention_span,
        interests=interests,
        sensitivities=sensitivities,
        narrative_cognition=dims[0],
        language_capacity=dims[1],
        attention_profile=dims[2],
        emotional_processing=dims[3],
        interaction_style=dims[4],
        imagination_mode=dims[5],
        familiarity_anchors=dims[6],
        engagement_drivers=dims[7],
        profile_confidence=confidence,
        key_assumptions=assumptions,
    )
    return AudienceExperience(
        child_profile=child,
        parent_age=parent_age,
        parent_job=parent_job,
        cultural_context="",
        coplay_context="",
        reading_setting="",
    )


def _merge_with_fallback(parsed: AudienceExperience, normalized: dict) -> AudienceExperience:
    cp = parsed.child_profile
    src = normalized.get("child_profile") or {}
    age = (src.get("age_range") or "").strip()
    en = (src.get("emotional_needs") or "").strip()
    att = (src.get("attention_span") or "").strip()
    merged = cp.model_copy(
        update={
            "age_range": age or cp.age_range,
            "emotional_needs": en or cp.emotional_needs,
            "attention_span": att or cp.attention_span,
            "interests": src.get("interests") if src.get("interests") else cp.interests,
            "sensitivities": src.get("sensitivities") if src.get("sensitivities") else cp.sensitivities,
        }
    )
    return AudienceExperience(
        child_profile=merged,
        parent_age=parsed.parent_age or normalized.get("parent_age") or "",
        parent_job=parsed.parent_job or normalized.get("parent_job") or "",
        cultural_context=normalized.get("cultural_context") or "",
        coplay_context=normalized.get("coplay_context") or "",
        reading_setting=normalized.get("reading_setting") or "",
    )


def _fallback(normalized: dict) -> AudienceExperience:
    cp = normalized.get("child_profile") or {}
    interests = cp.get("interests")
    sensitivities = cp.get("sensitivities")
    if not isinstance(interests, list):
        interests = [str(interests)] if interests else []
    if not isinstance(sensitivities, list):
        sensitivities = [str(sensitivities)] if sensitivities else []

    base = _fail_safe_profile()
    child = base.model_copy(
        update={
            "age_range": cp.get("age_range") or "",
            "emotional_needs": cp.get("emotional_needs") or base.emotional_needs,
            "attention_span": cp.get("attention_span") or base.attention_span,
            "interests": interests or base.interests,
            "sensitivities": sensitivities or base.sensitivities,
        }
    )
    return AudienceExperience(
        child_profile=child,
        parent_age=normalized.get("parent_age") or "",
        parent_job=normalized.get("parent_job") or "",
        cultural_context=normalized.get("cultural_context") or "",
        coplay_context=normalized.get("coplay_context") or "",
        reading_setting=normalized.get("reading_setting") or "",
    )

