from simagents.core.models import AgentSpec, WorkflowMode, WorkflowSpec


def test_workflow_mode_linear() -> None:
    wf = WorkflowSpec(mode=WorkflowMode.LINEAR)
    assert wf.mode == WorkflowMode.LINEAR


def test_agent_spec_defaults() -> None:
    a = AgentSpec(name="a", role="r", model="m")
    assert a.temperature == 0.3
