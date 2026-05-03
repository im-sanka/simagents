from simagents.core.models import AgentSpec, Hooks, RunConfig, TaskSpec, WorkflowMode, WorkflowSpec
from simagents.orchestration.orchestrator import EasyOrchestrator


class DummyProvider:
    def invoke(self, *, model: str, temperature: float, prompt: str) -> str:
        if "Quality checklist" in prompt:
            return "Prompt plan created"
        return f"OUTPUT::{model}::{prompt[:30]}"


def test_linear_orchestration_runs() -> None:
    agents = [
        AgentSpec(name="researcher", role="r", model="m1"),
        AgentSpec(name="planner", role="p", model="m2"),
    ]
    tasks = [
        TaskSpec(name="research", agent_name="researcher", prompt_template="Research {input}"),
        TaskSpec(name="plan", agent_name="planner", prompt_template="Make plan using {research}"),
    ]

    orch = EasyOrchestrator(
        agents=agents,
        tasks=tasks,
        workflow=WorkflowSpec(mode=WorkflowMode.LINEAR),
        run_config=RunConfig(save_artifacts=False),
        provider=DummyProvider(),
    )

    result = orch.run(input_text="bioinformatics")
    assert "plan" in result.step_outputs
    assert len(result.decision_log) >= 2


def test_parallel_respects_dependencies() -> None:
    agents = [
        AgentSpec(name="a", role="r", model="m1"),
        AgentSpec(name="b", role="r", model="m2"),
        AgentSpec(name="c", role="r", model="m3"),
    ]
    tasks = [
        TaskSpec(name="t1", agent_name="a", prompt_template="A {input}"),
        TaskSpec(name="t2", agent_name="b", prompt_template="B {t1}", depends_on=["t1"]),
        TaskSpec(name="t3", agent_name="c", prompt_template="C {t2}", depends_on=["t2"]),
    ]

    orch = EasyOrchestrator(
        agents=agents,
        tasks=tasks,
        workflow=WorkflowSpec(mode=WorkflowMode.PARALLEL),
        run_config=RunConfig(save_artifacts=False),
        provider=DummyProvider(),
    )
    result = orch.run(input_text="x")
    assert set(result.step_outputs.keys()) == {"t1", "t2", "t3"}


def test_hooks_are_called() -> None:
    events: list[str] = []

    hooks = Hooks(
        on_step_start=lambda name: events.append(f"start:{name}"),
        on_step_end=lambda name, _: events.append(f"end:{name}"),
    )

    orch = EasyOrchestrator(
        agents=[AgentSpec(name="a", role="r", model="m1")],
        tasks=[TaskSpec(name="t1", agent_name="a", prompt_template="Do {input}")],
        workflow=WorkflowSpec(mode=WorkflowMode.LINEAR),
        run_config=RunConfig(save_artifacts=False),
        provider=DummyProvider(),
        hooks=hooks,
    )
    orch.run(input_text="x")
    assert events == ["start:t1", "end:t1"]
