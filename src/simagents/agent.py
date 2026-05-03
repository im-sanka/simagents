from __future__ import annotations

from simagents.core.models import AgentResult, AgentSpec
from simagents.llm.provider import LLMProvider
from simagents.utils.cache import LLMResponseCache
from simagents.utils.retry import with_retry


class EasyAgent:
    def __init__(self, spec: AgentSpec, provider: LLMProvider, cache: LLMResponseCache | None = None) -> None:
        self.spec = spec
        self.provider = provider
        self.cache = cache

    def run(self, prompt: str, *, max_retries: int, backoff_seconds: float) -> AgentResult:
        system = self.spec.system_prompt or f"You are {self.spec.role}. {self.spec.instructions}".strip()
        full_prompt = f"{system}\n\nTask:\n{prompt}"
        provider_name = self.provider.__class__.__name__
        provider_base_url = getattr(self.provider, "base_url", None)

        cache_key = None
        if self.cache:
            cache_key = self.cache.build_key(
                provider_name=provider_name,
                provider_base_url=provider_base_url,
                model=self.spec.model,
                temperature=self.spec.temperature,
                prompt=full_prompt,
            )
            cached_content = self.cache.get(cache_key)
            if cached_content is not None:
                return AgentResult(
                    agent_name=self.spec.name,
                    content=cached_content,
                    metadata={"cache_hit": True, "cache_key": cache_key},
                )

        content = with_retry(
            lambda: self.provider.invoke(
                model=self.spec.model,
                temperature=self.spec.temperature,
                prompt=full_prompt,
            ),
            max_retries=max_retries,
            backoff_seconds=backoff_seconds,
        )

        if self.cache and cache_key:
            self.cache.set(
                cache_key,
                content,
                metadata={
                    "agent_name": self.spec.name,
                    "provider_name": provider_name,
                    "provider_base_url": provider_base_url,
                    "model": self.spec.model,
                    "temperature": self.spec.temperature,
                },
            )

        metadata = {"cache_hit": False, "cache_key": cache_key} if self.cache else {}
        return AgentResult(agent_name=self.spec.name, content=content, metadata=metadata)
