import os

from lib.llm.gemini_client import (
    DEFAULT_GEMINI_BASE,
    DEFAULT_GEMINI_MODEL,
    GeminiClient,
)
from lib.llm.mock_client import MockLlmClient


def resolve_provider() -> str:
    if os.getenv("LLM_PROVIDER"):
        return os.environ["LLM_PROVIDER"].lower()
    if os.getenv("GEMINI_API_KEY"):
        return "gemini"
    return "mock"


def create_llm_client():
    provider = resolve_provider()

    if provider == "mock":
        return MockLlmClient()

    if provider != "gemini":
        raise ValueError(
            f'Unknown LLM_PROVIDER "{provider}". Use "mock" or "gemini".'
        )

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")

    return GeminiClient(
        api_key=api_key,
        base_url=os.getenv("GEMINI_BASE_URL", DEFAULT_GEMINI_BASE),
        model=os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
        timeout_ms=int(os.getenv("LLM_TIMEOUT_MS", "60000")),
    )
