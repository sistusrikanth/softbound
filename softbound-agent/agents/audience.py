# Layer 2: Audience Agent — free-form text for lightweight LLMs
from __future__ import annotations

import re

from core.base_agent import BaseAgentMixin
from core.models import AudienceExperience, ChildProfile
from .prompts_common import GLOBAL_DIRECTIVE

# Line order: child (5) then coplay (2). Optional labels stripped when parsing.
LINE_LABELS = [
    "AGE",
    "EMOTIONAL NEEDS",
    "ATTENTION SPAN",
    "INTERESTS",
    "SENSITIVITIES",
    "PARENT AGE",
    "PARENT JOB",
]


def _normalize_input(input_data: dict) -> dict:
    """Convert flat or nested input into a dict for fallback / hints."""
    if not isinstance(input_data, dict):
        input_data = {}
    cp = input_data.get("child_profile") if isinstance(input_data.get("child_profile"), dict) else {}
    return {
        "child_profile": {
            "age_range": cp.get("age_range") or input_data.get("age_range") or input_data.get("age") or "",
            "emotional_needs": cp.get("emotional_needs") or input_data.get("emotional_needs") or "",
            "attention_span": cp.get("attention_span") or input_data.get("attention_span") or "",
            "interests": cp.get("interests") if isinstance(cp.get("interests"), list) else (input_data.get("interests") if isinstance(input_data.get("interests"), list) else []),
            "sensitivities": cp.get("sensitivities") if isinstance(cp.get("sensitivities"), list) else (input_data.get("sensitivities") if isinstance(input_data.get("sensitivities"), list) else []),
        },
        "parent_age": input_data.get("parent_age") or "",
        "parent_job": input_data.get("parent_job") or "",
        "cultural_context": input_data.get("cultural_context") or input_data.get("culture") or "",
        "coplay_context": input_data.get("coplay_context") or input_data.get("coplay") or "",
        "reading_setting": input_data.get("reading_setting") or "",
    }


def _hints(normalized: dict) -> str:
    cp = normalized.get("child_profile") or {}
    parts = []
    if any(cp.get(k) for k in ("age_range")):
        parts.append("Child age: " + str(cp.get("age_range")))
    if normalized.get("parent_age") or normalized.get("parent_job"):
        parts.append("Co-play: parent_age=%s, parent_job=%s" % (normalized.get("parent_age", ""), normalized.get("parent_job", "")))
    if not parts:
        return "No specific audience given. Invent a fresh child profile and co-play context this time."
    return "Given (use as inspiration; generate new wording): " + " | ".join(parts)


class AudienceAgent(BaseAgentMixin):
    """Builds audience from 7 small lines with < 5 words each: child (age, emotional_needs, attention_span, interests, sensitivities) + coplay (parent_age, parent_job)."""

    SYSTEM_PROMPT = GLOBAL_DIRECTIVE + """
You represent the child and the parent/caregiver. Reply with exactly 7 short lines, one per field. Generate new, varied values each time.

Line 1 – AGE: (e.g. 4-6 or 5)
Line 2 – EMOTIONAL NEEDS: [need1, need2, need3]
Line 3 – ATTENTION SPAN: (e.g. short, medium)
Line 4 – INTERESTS: [interest1, interest2, interest3]
Line 5 – SENSITIVITIES: [sensitivity1, sensitivity2, sensitivity3]
Line 6 – PARENT AGE: (e.g. 35, 30-40)
Line 7 – PARENT JOB: [job1, job2, job3]

Write only these 7 lines. No JSON, no extra formatting. You may start each line with the label (e.g. AGE: 4-6) or just the value."""

    USER_PROMPT_TEMPLATE = "{hints}"

    def create(self, input_data: dict) -> AudienceExperience:
        if not isinstance(input_data, dict):
            input_data = {}
        normalized = _normalize_input(input_data)
        hints = _hints(normalized)

        out = self.maybe_call_llm(hints=hints)

        # print(f"============= Audience Agent output: {out} =============")
        if out:
            parsed = _parse(out)
            if parsed is not None:
                # print("Audience parsed:", out[:200] + "..." if len(out) > 200 else out)
                return parsed
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
    # First 5 → child_profile; next 2 → parent_age, parent_job
    age = ""
    emotional_needs = ""
    attention_span = ""
    interests: list[str] = []
    sensitivities: list[str] = []
    parent_age = ""
    parent_job = ""
    if len(lines) >= 1:
        age = _strip_label(lines[0], "AGE")
    if len(lines) >= 2:
        emotional_needs = _strip_label(lines[1], "EMOTIONAL NEEDS")
    if len(lines) >= 3:
        attention_span = _strip_label(lines[2], "ATTENTION SPAN")
    if len(lines) >= 4:
        interests = [x.strip() for x in _strip_label(lines[3], "INTERESTS").split(",") if x.strip()]
    if len(lines) >= 5:
        sensitivities = [x.strip() for x in _strip_label(lines[4], "SENSITIVITIES").split(",") if x.strip()]
    if len(lines) >= 6:
        parent_age = _strip_label(lines[5], "PARENT AGE")
    if len(lines) >= 7:
        parent_job = _strip_label(lines[6], "PARENT JOB")

    child = ChildProfile(
        age_range=age,
        emotional_needs=emotional_needs,
        attention_span=attention_span,
        interests=interests,
        sensitivities=sensitivities,
    )
    return AudienceExperience(
        child_profile=child,
        parent_age=parent_age,
        parent_job=parent_job,
        cultural_context="",
        coplay_context="",
        reading_setting="",
    )


def _fallback(normalized: dict) -> AudienceExperience:
    cp = normalized.get("child_profile") or {}
    interests = cp.get("interests")
    sensitivities = cp.get("sensitivities")
    if not isinstance(interests, list):
        interests = [str(interests)] if interests else []
    if not isinstance(sensitivities, list):
        sensitivities = [str(sensitivities)] if sensitivities else []
    child = ChildProfile(
        age_range=cp.get("age_range") or "",
        emotional_needs=cp.get("emotional_needs") or "",
        attention_span=cp.get("attention_span") or "",
        interests=interests,
        sensitivities=sensitivities,
    )
    return AudienceExperience(
        child_profile=child,
        parent_age=normalized.get("parent_age") or "",
        parent_job=normalized.get("parent_job") or "",
        cultural_context=normalized.get("cultural_context") or "",
        coplay_context=normalized.get("coplay_context") or "",
        reading_setting=normalized.get("reading_setting") or "",
    )
