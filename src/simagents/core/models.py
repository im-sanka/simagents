from __future__ import annotations

from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel, Field


class WorkflowMode(str, Enum):
    LINEAR = "linear"
    PARALLEL = "parallel"
    LOOP = "loop"


class AgentSpec(BaseModel):
    name: str
    role: str
    instructions: str = ""
    model: str
    temperature: float = 0.3
    system_prompt: str | None = None


class TaskSpec(BaseModel):
    name: str
    prompt_template: str
    agent_name: str
    depends_on: list[str] = Field(default_factory=list)


class WorkflowSpec(BaseModel):
    mode: WorkflowMode = WorkflowMode.LINEAR
    max_iterations: int = 3
    stop_condition_keyword: str = "APPROVED"


class RunConfig(BaseModel):
    max_retries: int = 3
    retry_backoff_seconds: float = 1.0
    output_dir: str = "runs"
    save_artifacts: bool = True
    debug: bool = False


class Hooks(BaseModel):
    on_step_start: Callable[[str], None] | None = None
    on_step_end: Callable[[str, str], None] | None = None
    on_error: Callable[[str, Exception], None] | None = None

    model_config = {"arbitrary_types_allowed": True}


class AgentResult(BaseModel):
    agent_name: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class OrchestratorResult(BaseModel):
    final_output: str
    step_outputs: dict[str, str]
    decision_log: list[str]
    artifacts_dir: str | None = None
