# Layer 2: Audience — inferred child profile (1–7) for story adaptation
from __future__ import annotations

import re

from core.base_agent import BaseAgentMixin
from core.models import (
    AudienceExperience,
    CaregivingUtility,
    ChildProfile,
    ParentExperience,
    ProfileDimension,
    TheoryOfMindStatus,
)
from .prompts_common import GLOBAL_DIRECTIVE

_CHILD_KEYS = (
    "age_range",
    "emotional_needs",
    "attention_span",
    "interests",
    "sensitivities",
    "milestone_notes",
    "theory_of_mind",
    "explicit_action_consequence_bridging",
    "info_density",
    "processing_speed",
    "emotional_salence",
    "emotional_salience",
)
_COG_LINE_RE = re.compile(
    r"^\s*COG(?:\s*INPUTS)?\s*:\s*D\s*=\s*([0-9.]+)\s*[,;]?\s*S\s*=\s*([0-9.]+)\s*[,;]?\s*E\s*=\s*([0-9.]+)",
    re.I,
)


def _parse_float_01(s: str) -> float | None:
    t = (s or "").strip()
    if not t:
        return None
    try:
        x = float(t)
    except ValueError:
        return None
    if x < 0.0 or x > 1.0:
        return min(1.0, max(0.0, x))
    return x


def _parse_tom(s: str) -> TheoryOfMindStatus | None:
    if not s:
        return None
    t = s.strip().lower()
    m = {
        "pre_tom": TheoryOfMindStatus.PRE_TOM,
        "pre-tom": TheoryOfMindStatus.PRE_TOM,
    }
    if t in m:
        return m[t]
    for tok in t.replace("|", " ").replace(",", " ").split():
        tok = tok.strip().lower()
        if tok in ("pre_tom", "pre", "1-3", "1—3", "1–3"):
            return TheoryOfMindStatus.PRE_TOM
        if tok in ("emergent", "3-5", "3—5", "3–5", "3_5"):
            return TheoryOfMindStatus.EMERGENT
        if tok in ("established", "5-7", "5—7", "5–7", "5_7"):
            return TheoryOfMindStatus.ESTABLISHED
    for member in TheoryOfMindStatus:
        if member.name.lower() in t or member.value in t:
            return member
    return None


def _parse_bridging(s: str) -> bool | None:
    t = (s or "").strip().lower()
    if t in ("yes", "y", "true", "1", "required", "on"):
        return True
    if t in ("no", "n", "false", "0", "off"):
        return False
    if "yes" in t or "true" in t or "require" in t or "must" in t:
        return True
    if "no" in t and "not" in t and "not required" in t:
        return False
    return None


def _parse_caregiving(s: str) -> CaregivingUtility | None:
    t = (s or "").strip().lower()
    if not t:
        return None
    if "tantrum" in t or "mitigat" in t:
        return CaregivingUtility.TANTRUM_MITIGATION
    if "mediat" in t or "active" in t or "co—view" in t or "co-view" in t or "coplay" in t or "co-view" in t:
        return CaregivingUtility.ACTIVE_MEDIATION
    if "unspec" in t or "unknown" in t or "n/a" in t:
        return CaregivingUtility.UNSPECIFIED
    for member in CaregivingUtility:
        if member.value in t or member.name.lower() in t:
            return member
    return None


def _cog_from_line(line: str) -> tuple[float | None, float | None, float | None]:
    m = _COG_LINE_RE.match((line or "").strip())
    if m:
        return _parse_float_01(m.group(1)), _parse_float_01(m.group(2)), _parse_float_01(m.group(3))
    # Fallback: D=, S=, E= anywhere on the line
    t = (line or "").lower()
    d, s, e = None, None, None
    m2 = re.search(r"d\s*=\s*([0-9.]+)", t)
    m3 = re.search(r"s\s*=\s*([0-9.]+)", t)
    m4 = re.search(r"e\s*=\s*([0-9.]+)", t)
    if m2:
        d = _parse_float_01(m2.group(1))
    if m3:
        s = _parse_float_01(m3.group(1))
    if m4:
        e = _parse_float_01(m4.group(1))
    if d is not None or s is not None or e is not None:
        return d, s, e
    return None, None, None


def _infer_tom_from_age(age: str) -> TheoryOfMindStatus:
    t = re.sub(r"\s+", " ", (age or "").lower()).strip()
    if not t:
        return TheoryOfMindStatus.EMERGENT
    if re.search(
        r"\b(toddler|infant|baby|pre-?k|0\s*[-–—~]\s*2|0\s*[-–—~]\s*3)\b", t, re.I
    ):
        return TheoryOfMindStatus.PRE_TOM
    m = re.search(r"\b([0-7])\s*[-–—~]\s*([0-7])\b", t)
    if m:
        hi = max(int(m.group(1)), int(m.group(2)))
        if hi <= 3:
            return TheoryOfMindStatus.PRE_TOM
        if hi <= 5:
            return TheoryOfMindStatus.EMERGENT
        return TheoryOfMindStatus.ESTABLISHED
    m2 = re.search(r"(?:age|years?|yr)\s*[:#]?\s*([0-7])\b", t) or re.search(
        r"\b^([0-7])\b", t
    ) or re.search(r"\b([0-7])\b", t)
    if m2:
        a = int(m2.group(1))
        if a <= 3:
            return TheoryOfMindStatus.PRE_TOM
        if a <= 5:
            return TheoryOfMindStatus.EMERGENT
        return TheoryOfMindStatus.ESTABLISHED
    if re.search(r"\b(preschool|3\s*[-–—~]\s*5|kinder)\b", t):
        return TheoryOfMindStatus.EMERGENT
    if re.search(r"\b(5\s*[-–—~]\s*7|kindergarten|5|6|7|grade)\b", t):
        return TheoryOfMindStatus.ESTABLISHED
    return TheoryOfMindStatus.EMERGENT


def _normalize_input(input_data: dict) -> dict:
    if not isinstance(input_data, dict):
        input_data = {}
    cp = input_data.get("child_profile") if isinstance(input_data.get("child_profile"), dict) else {}
    child_flat: dict = {}
    for k in _CHILD_KEYS:
        if k == "emotional_salence" and "emotional_salience" in (cp, input_data):
            continue
        v = cp.get(k) if k in cp else input_data.get(k)
        if k in ("interests", "sensitivities"):
            if isinstance(v, list):
                child_flat[k] = v
            else:
                child_flat[k] = []
        else:
            child_flat[k] = v if v is not None else ""
    # Normalize duplicate typo key
    if (not child_flat.get("emotional_salience")) and cp.get("emotional_salence"):
        child_flat["emotional_salience"] = cp.get("emotional_salence")
    parent_utility = input_data.get("caregiving_utility", "")
    parent_necessity = input_data.get("necessity_guilt_cycle_note", "") or input_data.get("necessity_note", "")
    return {
        "child_profile": child_flat,
        "parent": {
            "parent_age": str(input_data.get("parent_age") or ""),
            "parent_job": str(input_data.get("parent_job") or ""),
            "caregiving_utility": parent_utility,
            "necessity_guilt_cycle_note": str(parent_necessity) if parent_necessity is not None else "",
        },
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
    pe = (normalized.get("parent") or {}) if isinstance(normalized.get("parent"), dict) else {}
    parts: list[str] = []
    if cp.get("age_range"):
        parts.append("age≈" + str(cp["age_range"]))
    if cp.get("milestone_notes"):
        parts.append("milestones: " + str(cp["milestone_notes"]))
    if cp.get("theory_of_mind"):
        parts.append("ToM hint: " + str(cp["theory_of_mind"]))
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
    p_age = (pe or {}).get("parent_age", "")
    p_job = (pe or {}).get("parent_job", "")
    if p_age or p_job:
        parts.append("parent %s / %s" % (p_age, p_job))
    cg = (pe or {}).get("caregiving_utility", "")
    nnote = (pe or {}).get("necessity_guilt_cycle_note", "")
    if cg or nnote:
        parts.append("caregiving: %s %s" % (cg, nnote).strip())
    if not parts:
        return (
            "No audience signals. Infer 1–7 profile; default to simple story, short attention, repetition, "
            "emotional safety; pre-ToM: explicit action–consequence links."
        )
    return "Signals (infer milestones; age is a weak prior): " + " | ".join(parts)


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
        narrative_cognition=_d("Simple sequential", "Concrete beats; every action tied to a visible result."),
        language_capacity=_d("Simple + repetition", "Short sentences; small vocabulary."),
        attention_profile=_d("Limited", "Slow pacing; few beats per page."),
        emotional_processing=_d("Sensitive", "Low stakes; quick resolution; clear safety."),
        interaction_style=_d("Guided", "Optional prompts; not open-ended demand."),
        imagination_mode=_d("Sensory-led", "Tangible detail before abstraction."),
        familiarity_anchors=_d("Home routines", "Bedtime, meals, caretakers."),
        engagement_drivers=_d("Repetition", "Refrain + small novelty."),
        profile_confidence="low",
        key_assumptions="Minimal input; early-childhood (1–7) defaults: lower cognitive load; bridging on.",
        milestone_notes="Inferred: attention + language burst; not calendar-only.",
        theory_of_mind=TheoryOfMindStatus.EMERGENT,
        explicit_action_consequence_bridging=True,
        info_density=0.35,
        processing_speed=0.45,
        emotional_salience=0.35,
    )


class AudienceAgent(BaseAgentMixin):
    SYSTEM_PROMPT = GLOBAL_DIRECTIVE + """
Infer a developmental profile for storytelling (child 1–7 in typical bands: pre-ToM ~1–3, emergent ToM ~3–5, established first-order ToM ~5–7). Age is a weak prior—infer from behavior, milestones, and context; if unsure, use simpler, lower-load defaults.

Cognitive model (for story pacing): L_cognitive ≈ D_info / S_proc + E_emotional, with D/S/E in [0,1] (D = information density, S = relative processing speed, E = emotional salience). If pre-ToM, explicit action–consequence *bridging* in the narrative is mandatory (no implied causality off-page).

Output exactly 17 lines, in order; each dimension line: DIMENSION: ShortLabel — one short sentence.
1 NARRATIVE COGNITION: …
2 LANGUAGE CAPACITY: …
3 ATTENTION PROFILE: …
4 EMOTIONAL PROCESSING: …
5 INTERACTION STYLE: …
6 IMAGINATION MODE: …
7 FAMILIARITY ANCHORS: …
8 ENGAGEMENT DRIVERS: …
9 OVERALL CONFIDENCE: low | medium | high
10 KEY ASSUMPTIONS: one short line (or "none")
11 THEORY OF MIND: pre_tom | emergent | established
12 EXPLICIT ACTION-CONSEQUENCE BRIDGING: yes | no (if pre_tom, must be yes)
13 MILESTONE NOTES: neurological/developmental signals (e.g. language pattern, self-other separation), not age alone
14 COG INPUTS: D=0.0-1.0, S=0.0-1.0, E=0.0-1.0
15 PARENT AGE: …
16 PARENT JOB: …
17 CAREGIVING UTILITY: tantrum_mitigation | active_mediation | unspecified

No JSON or markdown in your reply."""

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
    u = (line or "").upper()
    lu = label.upper()
    if u.startswith(lu) and len(line) > len(lu) and line[len(lu) : len(lu) + 1] in (":", " "):
        rest = line[len(lu) :].strip()
        if rest.startswith(":"):
            return rest[1:].strip()
    return line.strip()


def _find_labeled(
    lines: list[str], prefix: str, alts: tuple[str, ...] = ()
) -> str:
    candidates = (prefix,) + alts
    for ln in lines:
        t = (ln or "").strip()
        low = t.lower()
        for c in candidates:
            c2 = c.lower() + ("" if c.endswith(":") else ":")
            c3 = c.lower() + (":" if c.endswith(":") else ":")
            if low.startswith(c2) or low.startswith(c3) or t.upper().startswith(c.upper()):
                return _strip_label(t, c.split(":", 1)[0] if ":" in c else c)
    return ""


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
    tom_line = ""
    bridge_line = ""
    milestone_line = ""
    cog_line = ""
    parent_age = ""
    parent_job = ""
    caregiving_line = ""

    if len(lines) >= 9:
        confidence = _normalize_confidence(
            _strip_label(lines[8], "OVERALL CONFIDENCE")
            or _find_labeled(lines, "OVERALL CONFIDENCE")
        )
    if len(lines) >= 10:
        assumptions = _strip_label(lines[9], "KEY ASSUMPTIONS") or _find_labeled(lines, "KEY ASSUMPTIONS")
    if len(lines) >= 11:
        tom_line = _strip_label(lines[10], "THEORY OF MIND")
    if len(lines) >= 12:
        bridge_line = _strip_label(
            lines[11], "EXPLICIT ACTION-CONSEQUENCE BRIDGING"
        ) or _find_labeled(lines, "EXPLICIT")
    if len(lines) >= 13:
        milestone_line = _strip_label(lines[12], "MILESTONE NOTES")
    if len(lines) >= 14:
        cog_line = _strip_label(lines[13], "COG")
    if len(lines) >= 15:
        parent_age = _strip_label(lines[14], "PARENT AGE")
    if len(lines) >= 16:
        parent_job = _strip_label(lines[15], "PARENT JOB")
    if len(lines) >= 17:
        caregiving_line = _strip_label(lines[16], "CAREGIVING")

    if not tom_line:
        tom_line = _find_labeled(
            lines,
            "THEORY OF MIND",
            ("TOM",),
        )
    if not bridge_line:
        bridge_line = _find_labeled(lines, "EXPLICIT ACTION-CONSEQUENCE BRIDGING", ("BRIDGING", "ACTION-CONSEQUENCE"))
    if not milestone_line:
        milestone_line = _find_labeled(lines, "MILESTONE NOTES", ("MILESTONES",))
    if not cog_line:
        for i, ln in enumerate(lines):
            if re.match(r"^COG", ln, re.I):
                cog_line = _strip_label(ln, "COG INPUTS") or ln
                break
    if not parent_age:
        parent_age = _find_labeled(lines, "PARENT AGE")
    if not parent_job:
        parent_job = _find_labeled(lines, "PARENT JOB")
    if not caregiving_line:
        caregiving_line = _find_labeled(lines, "CAREGIVING", ("CAREGIVING UTILITY",))

    tom = _parse_tom(tom_line) or TheoryOfMindStatus.EMERGENT
    bridging = _parse_bridging(bridge_line)
    if tom == TheoryOfMindStatus.PRE_TOM:
        bridging = True
    elif bridging is None:
        bridging = True
    d_f, s_f, e_f = _cog_from_line(cog_line) if cog_line else (None, None, None)
    d_f, s_f, e_f = _cog_from_line(" ".join(lines)) if d_f is None and s_f is None and e_f is None else (d_f, s_f, e_f)

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

    cprof = {
        "age_range": "",
        "emotional_needs": emo_txt,
        "attention_span": attention_span,
        "interests": interests,
        "sensitivities": sensitivities,
        "narrative_cognition": dims[0],
        "language_capacity": dims[1],
        "attention_profile": dims[2],
        "emotional_processing": dims[3],
        "interaction_style": dims[4],
        "imagination_mode": dims[5],
        "familiarity_anchors": dims[6],
        "engagement_drivers": dims[7],
        "profile_confidence": confidence,
        "key_assumptions": assumptions,
        "milestone_notes": (milestone_line or "").strip(),
        "theory_of_mind": tom,
        "explicit_action_consequence_bridging": bridging,
    }
    if d_f is not None:
        cprof["info_density"] = d_f
    if s_f is not None:
        cprof["processing_speed"] = max(0.05, min(1.0, s_f))
    if e_f is not None:
        cprof["emotional_salience"] = e_f

    child = ChildProfile(**cprof)
    cg = _parse_caregiving(caregiving_line) or CaregivingUtility.UNSPECIFIED
    parent = ParentExperience(
        parent_age=parent_age.strip(),
        parent_job=parent_job.strip(),
        caregiving_utility=cg,
        necessity_guilt_cycle_note="",
    )
    return AudienceExperience(child_profile=child, parent=parent)


def _coerce_from_child_dict(
    d: dict, parent_d: dict | None = None
) -> tuple[TheoryOfMindStatus, bool, float, float, float, str, str, CaregivingUtility]:
    parent_d = parent_d or {}
    age = (d.get("age_range") or "").strip()
    mnotes = (d.get("milestone_notes") or "").strip()
    t_raw = d.get("theory_of_mind")
    if isinstance(t_raw, TheoryOfMindStatus):
        tom_v = t_raw
    elif t_raw is not None and t_raw != "":
        tom_v = _parse_tom(str(t_raw)) or (TheoryOfMindStatus.EMERGENT)
    else:
        tom_v = _infer_tom_from_age(age) if age else TheoryOfMindStatus.EMERGENT
    b = d.get("explicit_action_consequence_bridging")
    if b is None or b == "":
        bridge = tom_v == TheoryOfMindStatus.PRE_TOM
    else:
        bridge = str(b).lower() in ("1", "true", "yes", "y", "on")
    if tom_v == TheoryOfMindStatus.PRE_TOM:
        bridge = True
    d_i, s_p = d.get("info_density"), d.get("processing_speed")
    e_m = d.get("emotional_salience", d.get("emotional_salence"))
    try:
        f_d = float(d_i) if d_i is not None and d_i != "" else 0.4
    except (TypeError, ValueError):
        f_d = 0.4
    try:
        f_s = float(s_p) if s_p is not None and s_p != "" else 0.5
    except (TypeError, ValueError):
        f_s = 0.5
    try:
        f_e = float(e_m) if e_m is not None and e_m != "" else 0.3
    except (TypeError, ValueError):
        f_e = 0.3
    f_d, f_s, f_e = max(0.0, min(1.0, f_d)), max(0.05, min(1.0, f_s)), max(0.0, min(1.0, f_e))
    raw_cg = d.get("caregiving_utility") or parent_d.get("caregiving_utility")
    pu = _parse_caregiving(str(raw_cg or "")) or CaregivingUtility.UNSPECIFIED
    nnote = (
        (d.get("necessity_guilt_cycle_note") or d.get("necessity_note") or parent_d.get("necessity_guilt_cycle_note") or "")
        or ""
    ).strip()
    return tom_v, bridge, f_d, f_s, f_e, mnotes, nnote, pu


def _merge_with_fallback(parsed: AudienceExperience, normalized: dict) -> AudienceExperience:
    cp = parsed.child_profile
    src = normalized.get("child_profile") or {}
    p_norm = (normalized.get("parent") or {}) if isinstance(normalized.get("parent"), dict) else {}
    age = (src.get("age_range") or "").strip()
    en = (src.get("emotional_needs") or "").strip()
    att = (src.get("attention_span") or "").strip()
    _, _, fd, fs, fe, mnotes, nnote, cgu = _coerce_from_child_dict(src, p_norm)
    raw_tom = src.get("theory_of_mind")
    t_user = _parse_tom(str(raw_tom or "").strip()) if raw_tom is not None and str(raw_tom).strip() != "" else None
    if t_user is not None:
        tom_f = t_user
    elif (src.get("age_range") or "").strip() != "":
        tom_f = _infer_tom_from_age(age)
    else:
        tom_f = cp.theory_of_mind
    bridge = cp.explicit_action_consequence_bridging
    if src.get("explicit_action_consequence_bridging") is not None:
        b = src.get("explicit_action_consequence_bridging")
        bridge = b if isinstance(b, bool) else str(b).lower() in ("1", "true", "yes", "y", "on")
    if tom_f == TheoryOfMindStatus.PRE_TOM:
        bridge = True
    merged = cp.model_copy(
        update={
            "age_range": age or cp.age_range,
            "emotional_needs": en or cp.emotional_needs,
            "attention_span": att or cp.attention_span,
            "interests": src.get("interests") if src.get("interests") else cp.interests,
            "sensitivities": src.get("sensitivities") if src.get("sensitivities") else cp.sensitivities,
            "milestone_notes": mnotes or cp.milestone_notes,
            "theory_of_mind": tom_f,
            "explicit_action_consequence_bridging": bridge,
        }
    )
    if src.get("info_density") is not None or src.get("processing_speed") is not None or src.get(
        "emotional_salience", src.get("emotional_salence")
    ) is not None:
        merged = merged.model_copy(update={"info_density": fd, "processing_speed": fs, "emotional_salience": fe})

    pp = parsed.parent
    pa = p_norm.get("parent_age", "") or pp.parent_age
    pj = p_norm.get("parent_job", "") or pp.parent_job
    pparse = _parse_caregiving(str(p_norm.get("caregiving_utility", "") or ""))
    if pparse and pparse != CaregivingUtility.UNSPECIFIED:
        cgu_f = pparse
    elif cgu != CaregivingUtility.UNSPECIFIED:
        cgu_f = cgu
    else:
        cgu_f = pp.caregiving_utility
    nmerge = (p_norm.get("necessity_guilt_cycle_note") or nnote or pp.necessity_guilt_cycle_note) or ""
    nmerge = str(nmerge or "").strip()

    return AudienceExperience(
        child_profile=merged,
        parent=ParentExperience(
            parent_age=str(pa or "")[:400],
            parent_job=str(pj or "")[:400],
            caregiving_utility=cgu_f,
            necessity_guilt_cycle_note=(nmerge or pp.necessity_guilt_cycle_note)[:2000],
        ),
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
    p_norm = (normalized.get("parent") or {}) if isinstance(normalized.get("parent"), dict) else {}
    base = _fail_safe_profile()
    tom, bridge, fd, fs, fe, _mn, nnote, cgu = _coerce_from_child_dict({**cp, "parent": p_norm})
    child = base.model_copy(
        update={
            "age_range": cp.get("age_range") or "",
            "emotional_needs": cp.get("emotional_needs") or base.emotional_needs,
            "attention_span": cp.get("attention_span") or base.attention_span,
            "interests": interests or base.interests,
            "sensitivities": sensitivities or base.sensitivities,
            "theory_of_mind": tom,
            "explicit_action_consequence_bridging": bridge
            or (True if tom == TheoryOfMindStatus.PRE_TOM else base.explicit_action_consequence_bridging),
            "info_density": fd,
            "processing_speed": fs,
            "emotional_salience": fe,
            "milestone_notes": (cp.get("milestone_notes") or "").strip() or base.milestone_notes,
        }
    )
    if tom == TheoryOfMindStatus.PRE_TOM:
        child = child.model_copy(update={"explicit_action_consequence_bridging": True})
    cgu2 = cgu
    ppu = p_norm.get("caregiving_utility")
    if ppu is not None and str(ppu).strip():
        cgu2 = _parse_caregiving(str(ppu)) or cgu2
    return AudienceExperience(
        child_profile=child,
        parent=ParentExperience(
            parent_age=p_norm.get("parent_age", "") or "",
            parent_job=p_norm.get("parent_job", "") or "",
            caregiving_utility=cgu2,
            necessity_guilt_cycle_note=(p_norm.get("necessity_guilt_cycle_note", "") or str(nnote or ""))[:2000],
        ),
        cultural_context=normalized.get("cultural_context") or "",
        coplay_context=normalized.get("coplay_context") or "",
        reading_setting=normalized.get("reading_setting") or "",
    )
