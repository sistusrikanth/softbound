"""
Data models for the Softbound agentic framework.
Intent uses a Pydantic schema; other types are dataclasses.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, computed_field, Field


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


class ChildProfile(BaseModel):
    """
    Child audience profile (0–7): legacy flat hints plus inferred developmental dimensions.
    Dimensions guide story structure, language, pacing, emotion, and interaction.
    """
    age_range: str = ""
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


class AudienceExperience(BaseModel):
    """Layer 2: Audience (child profile + co-play: parent age/job). Free-form for lightweight LLMs."""
    child_profile: ChildProfile = Field(default_factory=ChildProfile)
    parent_age: str = ""
    parent_job: str = ""
    # Kept for backward compatibility; can leave empty
    cultural_context: str = ""
    coplay_context: str = ""
    reading_setting: str = ""


@dataclass
class World:
    """Layer 3: Story world (rules, physics, style, characters)."""
    rules: str = ""
    physics: str = ""
    moral_logic: str = ""
    visual_style: str = ""
    characters: list[dict[str, Any]] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)
    #: Verbatim LLM world response (always set when produced by WorldAgent from the model).
    full_output: str = ""


@dataclass
class Story:
    """Layer 4: Story (theme, arc, rhythm, genre)."""
    theme: str = ""
    emotional_arc: list[str] = field(default_factory=list)
    rhythm: str = ""
    genre: str = ""
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
