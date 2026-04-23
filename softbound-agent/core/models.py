"""
Data models for the Softbound agentic framework.
Intent uses a Pydantic schema; other types are dataclasses.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from typing import Any

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator


# --- Developmental / caregiving (ages 1–7 narrative) ---


class TheoryOfMindStatus(str, Enum):
    """Mental state reasoning capacity for social narrative (age bands are typical, not hard limits)."""

    PRE_TOM = "pre_tom"  # ~1–3: pre–false-belief
    EMERGENT = "emergent"  # ~3–5: first-order false belief emerging
    ESTABLISHED = "established"  # ~5–7: more stable first-order, richer perspective language


class CaregivingUtility(str, Enum):
    """Necessity–guilt / utility framing for *why* media is in the room."""

    TANTRUM_MITIGATION = "tantrum_mitigation"
    ACTIVE_MEDIATION = "active_mediation"  # co-viewing, talk-through
    UNSPECIFIED = "unspecified"


def _tom_cognitive_load_cap(tom: TheoryOfMindStatus) -> float:
    """Upper band for acceptable L (same units as ChildProfile.cognitive_load_index)."""
    if tom == TheoryOfMindStatus.PRE_TOM:
        return 1.25
    if tom == TheoryOfMindStatus.EMERGENT:
        return 1.7
    return 2.2


# --- Intent schema (Pydantic) ---

class Intent(BaseModel):
    """
    Layer 1: Show-bible style creative intent (four blocks, free text).
    product_philosophy — Why: mission archetype, parent necessity/guilt, Maisy Test ethics.
    artist_style — Mood & aesthetic: stimulation profile, visual style, audio/participatory cues.
    emotional_promise — How: structural archetype, narrative engine, failure cycle / mastery.
    creative_boundaries — Safety: non-goals, home/cuddle return, curriculum matrix (table ok).
    """
    artist_style: str = ""
    product_philosophy: str = ""
    emotional_promise: str = ""
    creative_boundaries: str = ""

    # @computed_field
    # @property
    # def summary(self) -> str:
    #     parts = []
    #     if self.artist_style:
    #         parts.append(f"Artistic identity: {self.artist_style}.")
    #     if self.product_philosophy:
    #         parts.append(f"Product philosophy: {self.product_philosophy}.")
    #     if self.emotional_promise:
    #         parts.append(f"Emotional promise: {self.emotional_promise}.")
    #     if self.creative_boundaries:
    #         parts.append(f"Creative boundaries: {self.creative_boundaries}.")
    #     return "\n".join(parts).strip() or ""


# --- Audience schema (Pydantic) ---


class ProfileDimension(BaseModel):
    """One inferred developmental dimension: short label + one supporting sentence."""
    label: str = ""
    explanation: str = ""


_COGNITIVE_EPS = 0.05


class ChildProfile(BaseModel):
    """
    Child audience profile (1–7): flat hints, inferred developmental dimensions, and milestone-aware fields.
    Cognitive load: L_cognitive ≈ D_info / S_proc + E_emotional (0–1 normalized inputs, same scale for comparison).
    """
    age_range: str = ""  # weak prior; use milestone_notes + ToM for structure
    emotional_needs: str = ""
    attention_span: str = ""
    interests: list[str] = Field(default_factory=list)
    sensitivities: list[str] = Field(default_factory=list)
    narrative_cognition: ProfileDimension = Field(default_factory=ProfileDimension)
    language_capacity: ProfileDimension = Field(default_factory=ProfileDimension)
    attention_profile: ProfileDimension = Field(default_factory=ProfileDimension)
    emotional_processing: ProfileDimension = Field(default_factory=ProfileDimension)
    interaction_style: ProfileDimension = Field(default_factory=ProfileDimension)
    imagination_mode: ProfileDimension = Field(default_factory=ProfileDimension)
    familiarity_anchors: ProfileDimension = Field(default_factory=ProfileDimension)
    engagement_drivers: ProfileDimension = Field(default_factory=ProfileDimension)
    profile_confidence: str = ""
    key_assumptions: str = ""
    # Developmental (neurology / social-cognitive, not only calendar age)
    milestone_notes: str = ""
    theory_of_mind: TheoryOfMindStatus = TheoryOfMindStatus.EMERGENT
    explicit_action_consequence_bridging: bool = True
    # Model inputs (0 = none/minimal, 1 = high); S_proc = relative processing *speed* (higher = faster, lowers load)
    info_density: float = Field(0.4, ge=0.0, le=1.0, description="D_info: narrative propositions / screen density")
    processing_speed: float = Field(0.5, ge=0.05, le=1.0, description="S_proc: demographically typical processing (higher = more headroom)")
    emotional_salience: float = Field(0.3, ge=0.0, le=1.0, description="E_emotional: arousal / affect weight")

    @computed_field
    @property
    def cognitive_load_index(self) -> float:
        """L_cognitive ≈ D_info / S_proc + E_emotional (guarded division)."""
        s = self.processing_speed if isfinite(self.processing_speed) else 0.5
        s = max(float(s), _COGNITIVE_EPS)
        d = self.info_density if isfinite(self.info_density) else 0.0
        e = self.emotional_salience if isfinite(self.emotional_salience) else 0.0
        return (max(d, 0.0) / s) + max(e, 0.0)

    @computed_field
    @property
    def cognitive_load_exceeds_demographic(self) -> bool:
        """True when L exceeds a typical ceiling for the current ToM band."""
        return self.cognitive_load_index > _tom_cognitive_load_cap(self.theory_of_mind)

    @model_validator(mode="after")
    def _enforce_pre_tom_causal_and_bridging(self) -> ChildProfile:
        # Pre-ToM: explicit action–consequence bridging is mandatory in narrative
        if self.theory_of_mind == TheoryOfMindStatus.PRE_TOM and not self.explicit_action_consequence_bridging:
            return self.model_copy(update={"explicit_action_consequence_bridging": True})
        return self

    @field_validator("theory_of_mind", mode="before")
    @classmethod
    def _coerce_tom(cls, v: Any) -> Any:
        if v is None or v == "":
            return TheoryOfMindStatus.EMERGENT
        if isinstance(v, TheoryOfMindStatus):
            return v
        s = str(v).strip().lower()
        m = {
            "pre_tom": TheoryOfMindStatus.PRE_TOM,
            "pre-tom": TheoryOfMindStatus.PRE_TOM,
            "pre": TheoryOfMindStatus.PRE_TOM,
            "emergent": TheoryOfMindStatus.EMERGENT,
            "established": TheoryOfMindStatus.ESTABLISHED,
        }
        if s in m:
            return m[s]
        for member in TheoryOfMindStatus:
            if member.value == s or member.name.lower() == s:
                return member
        return TheoryOfMindStatus.EMERGENT


class ParentExperience(BaseModel):
    """Parent / co-players: context for necessity–guilt framing and co-viewing."""

    parent_age: str = ""
    parent_job: str = ""
    caregiving_utility: CaregivingUtility = CaregivingUtility.UNSPECIFIED
    necessity_guilt_cycle_note: str = ""  # e.g. relief vs mediation intent

    @field_validator("caregiving_utility", mode="before")
    @classmethod
    def _coerce_utility(cls, v: Any) -> Any:
        if v is None or v == "":
            return CaregivingUtility.UNSPECIFIED
        if isinstance(v, CaregivingUtility):
            return v
        s = str(v).strip().lower().replace(" ", "_").replace("-", "_")
        alias = {
            "tantrum_mitigation": CaregivingUtility.TANTRUM_MITIGATION,
            "tantrum": CaregivingUtility.TANTRUM_MITIGATION,
            "mitigation": CaregivingUtility.TANTRUM_MITIGATION,
            "active_mediation": CaregivingUtility.ACTIVE_MEDIATION,
            "co_viewing": CaregivingUtility.ACTIVE_MEDIATION,
            "coplay": CaregivingUtility.ACTIVE_MEDIATION,
        }
        if s in alias:
            return alias[s]
        for member in CaregivingUtility:
            if member.value == s or member.name.lower() == s:
                return member
        return CaregivingUtility.UNSPECIFIED


class AudienceExperience(BaseModel):
    """Layer 2: child profile, parent / caregiving context, co-play hints."""

    child_profile: ChildProfile = Field(default_factory=ChildProfile)
    parent: ParentExperience = Field(default_factory=ParentExperience)
    # Kept for backward compatibility; can leave empty
    cultural_context: str = ""
    coplay_context: str = ""
    reading_setting: str = ""

    @computed_field
    @property
    def parent_age(self) -> str:
        return self.parent.parent_age

    @computed_field
    @property
    def parent_job(self) -> str:
        return self.parent.parent_job

    @model_validator(mode="before")
    @classmethod
    def _audience_parent_compat(cls, data: Any) -> Any:
        """Accept legacy top-level parent_age / parent_job (and related) and fold into `parent`."""
        if not isinstance(data, dict):
            return data
        d = dict(data)
        p0 = d.get("parent")
        pdict: dict[str, Any] = dict(p0) if isinstance(p0, dict) else {}
        for key in ("parent_age", "parent_job", "caregiving_utility", "necessity_guilt_cycle_note"):
            if key in d:
                pdict.setdefault(key, d.pop(key))
        if pdict:
            d["parent"] = pdict
        return d


@dataclass
class World:
    """Layer 3: Experiential / sensory world + rules, physics, and optional interaction design."""

    #: Embodied place: light, air, sound, materials, scale, and felt time (not a one-line "setting" label).
    sensory_environment: str = ""
    #: Safe Harbor (bibliotherapeutic): unknowns as "creatures with needs," not villain arcs.
    safe_harbor: str = ""
    rules: str = ""
    physics: str = ""
    #: Magical thinking / digital physics: tap, shake, etc. → immediate visible effect (empty if static only).
    interaction_physics: str = ""
    #: Orienting response: hold duration, cut rate, low-stakes environmental conflict; calms overstimulation.
    visual_pacing: str = ""
    moral_logic: str = ""
    visual_style: str = ""
    characters: list[dict[str, Any]] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)
    #: Verbatim LLM world response (always set when produced by WorldAgent from the model).
    full_output: str = ""


@dataclass
class PageAnimationHint:
    """Ties a story person/object on a page to a possible interaction (from `Animation: …` lines in the story)."""

    page_index: int
    subject: str
    trigger: str
    effect: str


class StoryArchetype(str, Enum):
    """
    Non-Aristotelian / pedagogical shapes (not classical rise–fall only).
    """

    #: Energy and stimulus taper toward rest / sleep, co-regulation.
    DIMINISHING = "diminishing"
    #: Ritualized, gentle check-in / body care / “how we do this” beats.
    DIAGNOSTIC = "diagnostic"
    #: Familiar -> stretch -> return home, emotional landing.
    HOME_AWAY_HOME = "home_away_home"


@dataclass
class Story:
    """Layer 4: Story (theme, non-classical structure, optional pause grammar, Maisy)."""
    theme: str = ""
    emotional_arc: list[str] = field(default_factory=list)
    rhythm: str = ""
    genre: str = ""
    #: Chosen or inferred structural archetype (pedagogical pacing, not only Aristotelian Freytag).
    structural_archetype: str = ""  # StoryArchetype value, e.g. "diminishing"
    #: Lines or product markers for Steve Burns style participatory delay (5–7s processing).
    participatory_cue_markers: list[str] = field(default_factory=list)
    #: Parsed from per-page `Animation: subject | trigger | effect` lines in `full_output`.
    page_animation_hints: list[PageAnimationHint] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)
    #: Verbatim LLM story response (always set when produced by StoryAgent from the model).
    full_output: str = ""


@dataclass
class Scene:
    """Layer 5: Single scene (goal, emotions, environment, dialogue, tone)."""
    goal: str = ""
    emotions: list[str] = field(default_factory=list)
    environment: str = ""
    dialogue_style: str = ""
    sensory_tone: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class StoryPackage:
    """Final output: story plus scenes and variants."""
    story: Story
    scenes: list[Scene]
    variants: dict[str, Any] = field(default_factory=dict)
    evaluation: dict[str, Any] = field(default_factory=dict)
