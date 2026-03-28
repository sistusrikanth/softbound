"""
Base behavior for agents: optional LLM call when prompts are set.
Each agent defines SYSTEM_PROMPT and USER_PROMPT_TEMPLATE (empty by default).
"""
from __future__ import annotations

from .llm_client import complete


class BaseAgentMixin:
    SYSTEM_PROMPT: str = ""
    USER_PROMPT_TEMPLATE: str = ""

    def get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT

    def get_user_prompt(self, **context: str | dict) -> str:
        template = self.USER_PROMPT_TEMPLATE
        if not template:
            return ""
        try:
            return template.format(**{k: (v if isinstance(v, str) else str(v)) for k, v in context.items()})
        except KeyError:
            return template

    def call_llm(self, user_content: str, system_content: str | None = None, **kwargs) -> str:
        system = system_content if system_content is not None else self.get_system_prompt()
        return complete(user_content, system_content=system, **kwargs)

    def maybe_call_llm(self, **context: str | dict) -> str | None:
        """Call LLM only when we have a real user prompt; otherwise return None and use fallback."""
        system = self.get_system_prompt()

        # print(f"System: {system}")
        user = self.get_user_prompt(**context)
        # print(f"User: {user}")
        if not user:
            return None  # No task to send — use fallback logic (avoids sending "(no user prompt)" to the model)
        return self.call_llm(user, system_content=system or "")
