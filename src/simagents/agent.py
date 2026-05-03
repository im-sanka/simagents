from __future__ import annotations

from simagents.core.models import AgentResult, AgentSpec
from simagents.llm.provider import LLMProvider
from simagents.utils.retry import with_retry


class EasyAgent:
    def __init__(self, spec: AgentSpec, provider: LLMProvider) -> None:
        self.spec = spec
        self.provider = provider

    def run(self, prompt: str, *, max_retries: int, backoff_seconds: float) -> AgentResult:
        system = self.spec.system_prompt or f"You are {self.spec.role}. {self.spec.instructions}".strip()
        full_prompt = f"{system}\n\nTask:\n{prompt}"

        content = with_retry(
            lambda: self.provider.invoke(
                model=self.spec.model,
                temperature=self.spec.temperature,
                prompt=full_prompt,
            ),
            max_retries=max_retries,
            backoff_seconds=backoff_seconds,
        )

        return AgentResult(agent_name=self.spec.name, content=content)
