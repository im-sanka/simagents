from __future__ import annotations

import os
from typing import Protocol

from openai import OpenAI


class LLMProvider(Protocol):
    def invoke(self, *, model: str, temperature: float, prompt: str) -> str:
        ...


class OpenAICompatibleProvider:
    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self.base_url = base_url or os.getenv("SIMAGENTS_BASE_URL", "https://api.openai.com/v1")
        self.api_key = api_key or os.getenv("SIMAGENTS_API_KEY") or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise RuntimeError("Missing API key. Set SIMAGENTS_API_KEY or OPENAI_API_KEY.")

    def invoke(self, *, model: str, temperature: float, prompt: str) -> str:
        client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )
        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""


class OpenAIProvider(OpenAICompatibleProvider):
    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(base_url="https://api.openai.com/v1", api_key=api_key or os.getenv("OPENAI_API_KEY"))


class OllamaProvider(OpenAICompatibleProvider):
    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        super().__init__(
            base_url=base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            api_key=api_key or os.getenv("OLLAMA_API_KEY") or "ollama",
        )


class GroqProvider(OpenAICompatibleProvider):
    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(base_url="https://api.groq.com/openai/v1", api_key=api_key or os.getenv("GROQ_API_KEY"))


class TogetherProvider(OpenAICompatibleProvider):
    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(
            base_url="https://api.together.xyz/v1",
            api_key=api_key or os.getenv("TOGETHER_API_KEY"),
        )


class OpenRouterProvider(OpenAICompatibleProvider):
    def __init__(self, api_key: str | None = None) -> None:
        super().__init__(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key or os.getenv("OPENROUTER_API_KEY"),
        )


class AnthropicProvider:
    def __init__(self, api_key: str | None = None) -> None:
        try:
            from anthropic import Anthropic  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "anthropic package is not installed. Run: pip install anthropic"
            ) from exc

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise RuntimeError("Missing API key. Set ANTHROPIC_API_KEY.")
        self.client = Anthropic(api_key=self.api_key)

    def invoke(self, *, model: str, temperature: float, prompt: str) -> str:
        response = self.client.messages.create(
            model=model,
            max_tokens=2048,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        chunks = []
        for block in response.content:
            if getattr(block, "type", None) == "text":
                chunks.append(block.text)
        return "\n".join(chunks).strip()
