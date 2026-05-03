from simagents.agent import EasyAgent
from simagents.core.models import AgentSpec, RunConfig, TaskSpec, WorkflowMode, WorkflowSpec
from simagents.orchestration.orchestrator import EasyOrchestrator
from simagents.utils.cache import LLMResponseCache


class CountingProvider:
    def __init__(self) -> None:
        self.calls = 0
        self.base_url = "https://example.test/v1"

    def invoke(self, *, model: str, temperature: float, prompt: str) -> str:
        self.calls += 1
        return f"response-{self.calls}:{model}:{temperature}:{prompt}"


def test_llm_response_cache_reuses_exact_invocation(tmp_path) -> None:
    provider = CountingProvider()
    cache = LLMResponseCache(cache_dir=str(tmp_path))
    agent = EasyAgent(AgentSpec(name="a", role="assistant", model="m1"), provider, cache=cache)

    first = agent.run("Do the task", max_retries=1, backoff_seconds=0)
    second = agent.run("Do the task", max_retries=1, backoff_seconds=0)

    assert provider.calls == 1
    assert second.content == first.content
    assert first.metadata["cache_hit"] is False
    assert second.metadata["cache_hit"] is True


def test_cache_key_changes_with_model(tmp_path) -> None:
    provider = CountingProvider()
    cache = LLMResponseCache(cache_dir=str(tmp_path))
    agent_one = EasyAgent(AgentSpec(name="a", role="assistant", model="m1"), provider, cache=cache)
    agent_two = EasyAgent(AgentSpec(name="a", role="assistant", model="m2"), provider, cache=cache)

    agent_one.run("Do the task", max_retries=1, backoff_seconds=0)
    agent_two.run("Do the task", max_retries=1, backoff_seconds=0)

    assert provider.calls == 2


def test_orchestrator_cache_can_be_enabled(tmp_path) -> None:
    provider = CountingProvider()
    agents = [AgentSpec(name="a", role="assistant", model="m1")]
    tasks = [TaskSpec(name="t", agent_name="a", prompt_template="Do {input}")]
    run_config = RunConfig(save_artifacts=False, cache_enabled=True, cache_dir=str(tmp_path))

    first = EasyOrchestrator(
        agents=agents,
        tasks=tasks,
        workflow=WorkflowSpec(mode=WorkflowMode.LINEAR),
        run_config=run_config,
        provider=provider,
    ).run(input_text="x")
    second = EasyOrchestrator(
        agents=agents,
        tasks=tasks,
        workflow=WorkflowSpec(mode=WorkflowMode.LINEAR),
        run_config=run_config,
        provider=provider,
    ).run(input_text="x")

    assert provider.calls == 1
    assert second.final_output == first.final_output
    assert any("cached output" in item for item in second.decision_log)


def test_orchestrator_cache_is_disabled_by_default(tmp_path) -> None:
    provider = CountingProvider()
    agents = [AgentSpec(name="a", role="assistant", model="m1")]
    tasks = [TaskSpec(name="t", agent_name="a", prompt_template="Do {input}")]
    run_config = RunConfig(save_artifacts=False, cache_dir=str(tmp_path))

    orch = EasyOrchestrator(
        agents=agents,
        tasks=tasks,
        workflow=WorkflowSpec(mode=WorkflowMode.LINEAR),
        run_config=run_config,
        provider=provider,
    )

    orch.run(input_text="x")
    orch.run(input_text="x")

    assert provider.calls == 2