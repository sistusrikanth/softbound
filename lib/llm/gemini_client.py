from __future__ import annotations

import httpx

DEFAULT_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite-preview"


class GeminiClient:
    """Google Gemini generateContent client."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_GEMINI_BASE,
        model: str = DEFAULT_GEMINI_MODEL,
        timeout_ms: int = 60_000,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout_ms / 1000

    def _to_gemini_contents(self, messages: list[dict]) -> list[dict]:
        contents = []
        for message in messages:
            if message["role"] == "system":
                continue
            role = "model" if message["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": message["content"]}]})
        return contents

    def _extract_system_instruction(self, messages: list[dict]) -> dict | None:
        system_text = "\n\n".join(
            m["content"] for m in messages if m["role"] == "system"
        )
        if not system_text:
            return None
        return {"parts": [{"text": system_text}]}

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        url = (
            f"{self.base_url}/models/{self.model}:generateContent"
            f"?key={self.api_key}"
        )

        body: dict = {
            "contents": self._to_gemini_contents(messages),
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        system_instruction = self._extract_system_instruction(messages)
        if system_instruction:
            body["systemInstruction"] = system_instruction

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=body)
            data = response.json()

        if not response.is_success:
            message = data.get("error", {}).get("message") or (
                f"Gemini request failed ({response.status_code})"
            )
            raise RuntimeError(message)

        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts if part.get("text"))

        if not text:
            raise RuntimeError("Gemini returned an empty response")

        return text.strip()
