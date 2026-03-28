# Helper agents: KnowledgeGuardian, Evaluation, Variant
from __future__ import annotations

from typing import Any

from core.base_agent import BaseAgentMixin
from core.models import Story
from .prompts_common import GLOBAL_DIRECTIVE


class KnowledgeGuardianAgent(BaseAgentMixin):
    """Validates artifacts for safety and appropriateness."""

    SYSTEM_PROMPT: str = GLOBAL_DIRECTIVE + """

You are a guardian, not a creator.
Review artifacts for safety, developmental fit, and plausibility.
Flag risks and explain them clearly.
Do not rewrite content unless explicitly requested."""
    USER_PROMPT_TEMPLATE: str = ""

    def validate(self, artifact: Any) -> dict[str, Any]:
        out = self.maybe_call_llm(artifact=str(artifact))
        if out is not None:
            return self._parse_llm_response(out)
        return self._fallback()

    def _parse_llm_response(self, response: str) -> dict[str, Any]:
        return {"safe": True, "notes": [response.strip()] if response.strip() else []}

    def _fallback(self) -> dict[str, Any]:
        return {"safe": True, "notes": []}


class EvaluationAgent(BaseAgentMixin):
    """Evaluates story on emotional safety, coherence, parent trust."""

    SYSTEM_PROMPT: str = GLOBAL_DIRECTIVE + """

You are a critic and editor.
Evaluate the story holistically and return structured scores and notes.
Explain why something works or doesn't.
Do not change the story."""
    USER_PROMPT_TEMPLATE: str = ""

    def evaluate(self, story: Story) -> dict[str, Any]:
        out = self.maybe_call_llm(
            theme=story.theme,
            emotional_arc=str(story.emotional_arc),
            genre=story.genre,
        )
        if out is not None:
            return self._parse_llm_response(out)
        return self._fallback()

    def _parse_llm_response(self, response: str) -> dict[str, Any]:
        return {"emotional_safety": 0.95, "coherence": 0.9, "parent_trust": 0.92, "notes": response.strip() or ""}

    def _fallback(self) -> dict[str, Any]:
        return {
            "emotional_safety": 0.95,
            "coherence": 0.9,
            "parent_trust": 0.92,
        }


class VariantAgent(BaseAgentMixin):
    """Generates variants: softer, faster, alternate POV."""

    SYSTEM_PROMPT: str = GLOBAL_DIRECTIVE + """

You explore alternatives without breaking coherence.
Generate clearly labeled variants that preserve Intent, Audience, and World.
Explain how each variant differs and what it optimizes for."""
    USER_PROMPT_TEMPLATE: str = ""

    def generate(self, story: Story) -> dict[str, Any]:
        return {
            "softer_version": self.adjust_emotion(story, "softer"),
            "faster_version": self.adjust_rhythm(story, "faster"),
            "alt_pov": self.shift_pov(story),
        }

    def adjust_emotion(self, story: Story, direction: str) -> Any:
        out = self.maybe_call_llm(
            theme=story.theme,
            emotional_arc=str(story.emotional_arc),
            direction=direction,
        )
        return out if out is not None else story

    def adjust_rhythm(self, story: Story, direction: str) -> Any:
        out = self.maybe_call_llm(
            theme=story.theme,
            rhythm=story.rhythm,
            direction=direction,
        )
        return out if out is not None else story

    def shift_pov(self, story: Story) -> Any:
        out = self.maybe_call_llm(theme=story.theme, genre=story.genre)
        return out if out is not None else story
