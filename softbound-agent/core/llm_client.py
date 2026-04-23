"""
LLM client: Gemini (default: Gemini 2.0 Flash-Lite), OpenRouter, or local 1B on Mac.

API keys (pick one backend via SOFTBOUND_LLM_BACKEND or env auto-detection):

- Gemini (default when GEMINI_API_KEY is set): Google AI Gemini API.
  Put your key in `.env` next to this package (see `env.example`) or export:
    GEMINI_API_KEY   — from https://aistudio.google.com/apikey
    (alias: GOOGLE_API_KEY is also read)
  Optional: GEMINI_MODEL (default: gemini-2.0-flash-lite).

- OpenRouter: OPENROUTER_API_KEY, optional OPENROUTER_MODEL.

- Local: SOFTBOUND_LLM_BACKEND=local; optional SOFTBOUND_LOCAL_MODEL.

Auto order when SOFTBOUND_LLM_BACKEND is unset: gemini (if key) → openrouter (if key) → local.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:
    requests = None  # type: ignore

try:
    from dotenv import load_dotenv

    _env_path = Path(__file__).resolve().parent.parent / ".env"
    if _env_path.is_file():
        load_dotenv(_env_path)
except ImportError:
    pass

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "meta-llama/llama-3.2-3b-instruct:free"

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite-preview" # Works [gemini-3-flash-preview, gemini-2.5-flash, gemini-3.1-flash-lite-preview, gemma3-1b-it]


def _backend() -> str:
    return os.environ.get("SOFTBOUND_LLM_BACKEND", "").strip().lower()


def _get_gemini_key() -> str:
    return (
        os.environ.get("GEMINI_API_KEY", "").strip()
        or os.environ.get("GOOGLE_API_KEY", "").strip()
    )


def _get_gemini_model() -> str:
    return os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL


def _get_openrouter_key() -> str:
    return os.environ.get("OPENROUTER_API_KEY", "").strip()


def _get_openrouter_model() -> str:
    return os.environ.get("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL)


def _complete_gemini_api(
    user_content: str,
    *,
    system_content: str = "",
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    if requests is None:
        raise RuntimeError("Install 'requests' to use the API backend: pip install requests")
    key = _get_gemini_key()
    if not key:
        raise RuntimeError(
            "Set GEMINI_API_KEY (or GOOGLE_API_KEY) for Gemini — see env.example or "
            "https://aistudio.google.com/apikey"
        )
    model_id = (model or _get_gemini_model()).strip()
    url = f"{GEMINI_BASE}/models/{model_id}:generateContent"
    body: dict[str, Any] = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_content}],
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }
    if system_content:
        body["systemInstruction"] = {"parts": [{"text": system_content}]}
    try:
        resp = requests.post(
            url,
            params={"key": key},
            json=body,
            headers={"Content-Type": "application/json"},
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        raise RuntimeError(f"Gemini API request failed: {e}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Gemini API response parse error: {e}") from e

    candidates = data.get("candidates") or []
    if not candidates:
        err = data.get("error") or {}
        msg = err.get("message") if isinstance(err, dict) else None
        if msg:
            raise RuntimeError(f"Gemini API: {msg}")
        raise RuntimeError("Gemini API returned no candidates")

    parts = (candidates[0].get("content") or {}).get("parts") or []
    texts: list[str] = []
    for p in parts:
        if isinstance(p, dict) and p.get("text"):
            texts.append(str(p["text"]))
    return "".join(texts).strip()


def _complete_api(
    user_content: str,
    *,
    system_content: str = "",
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    if requests is None:
        raise RuntimeError("Install 'requests' to use the API backend: pip install requests")
    key = _get_openrouter_key()
    if not key:
        raise RuntimeError(
            "Set OPENROUTER_API_KEY to use OpenRouter (get a key at https://openrouter.ai/keys)"
        )
    url = f"{OPENROUTER_BASE}/chat/completions"
    model_id = model or _get_openrouter_model()
    messages: list[dict[str, str]] = []
    if system_content:
        messages.append({"role": "system", "content": system_content})
    messages.append({"role": "user", "content": user_content})
    payload: dict[str, Any] = {
        "model": model_id,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices") or []
        if choices:
            msg = choices[0].get("message") or {}
            return (msg.get("content") or "").strip()
        return ""
    except requests.RequestException as e:
        raise RuntimeError(f"LLM API request failed: {e}") from e
    except (KeyError, TypeError, json.JSONDecodeError) as e:
        raise RuntimeError(f"LLM API response parse error: {e}") from e


def complete(
    user_content: str,
    *,
    system_content: str = "",
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 2048,
) -> str:
    b = _backend()
    print(f"============= LLM Client backend: {b} =============")
    if b == "local":
        from .local_llm import complete as _complete_local

        return _complete_local(
            user_content,
            system_content=system_content,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    if b == "openrouter":
        return _complete_api(
            user_content,
            system_content=system_content,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    if b == "gemini" or b == "google":
        return _complete_gemini_api(
            user_content,
            system_content=system_content,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if _get_gemini_key():
        return _complete_gemini_api(
            user_content,
            system_content=system_content,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    if _get_openrouter_key():
        return _complete_api(
            user_content,
            system_content=system_content,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    from .local_llm import complete as _complete_local, is_available as _local_available

    if _local_available():
        return _complete_local(
            user_content,
            system_content=system_content,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    raise RuntimeError(
        "No LLM backend available. Set GEMINI_API_KEY (Gemini 2.0 Flash-Lite), or OPENROUTER_API_KEY, "
        "or use SOFTBOUND_LLM_BACKEND=local."
    )


def is_available() -> bool:
    b = _backend()
    if b == "local":
        from .local_llm import is_available as _local_available

        return _local_available()
    if b == "openrouter":
        return requests is not None and bool(_get_openrouter_key())
    if b == "gemini" or b == "google":
        return requests is not None and bool(_get_gemini_key())
    if _get_gemini_key():
        return requests is not None
    if _get_openrouter_key():
        return requests is not None
    from .local_llm import is_available as _local_available

    return _local_available()
