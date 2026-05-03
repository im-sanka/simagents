from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from simagents.agent import EasyAgent
from simagents.core.models import Hooks, OrchestratorResult, RunConfig, TaskSpec, WorkflowMode, WorkflowSpec
from simagents.llm.provider import LLMProvider, OpenAICompatibleProvider
from simagents.utils.artifacts import create_run_dir, save_text
from simagents.utils.logging_utils import setup_logging


logger = logging.getLogger(__name__)


class EasyOrchestrator:
    def __init__(
        self,
        *,
        agents,
        tasks: list[TaskSpec],
        workflow: WorkflowSpec,
        run_config: RunConfig | None = None,
        provider: LLMProvider | None = None,
        hooks: Hooks | None = None,
    ) -> None:
        self.workflow = workflow
        self.run_config = run_config or RunConfig()
        self.provider = provider or OpenAICompatibleProvider()
        self.agents = {a.name: EasyAgent(a, self.provider) for a in agents}
        self.tasks = tasks
        self.hooks = hooks or Hooks()

    def run(self, *, input_text: str) -> OrchestratorResult:
        setup_logging(self.run_config.debug)
        run_dir = create_run_dir(self.run_config.output_dir) if self.run_config.save_artifacts else None
        decision_log: list[str] = []

        if self.workflow.mode == WorkflowMode.LINEAR:
            outputs = self._run_linear(input_text, decision_log)
        elif self.workflow.mode == WorkflowMode.PARALLEL:
            outputs = self._run_parallel(input_text, decision_log)
        else:
            outputs = self._run_loop(input_text, decision_log)

        final_output = outputs[self.tasks[-1].name] if self.tasks else ""
        if run_dir:
            save_text(run_dir, "decision_log.md", "\n".join(f"- {x}" for x in decision_log))
            save_text(run_dir, "final_output.md", final_output)
            for key, value in outputs.items():
                save_text(run_dir, f"{key}.md", value)

        return OrchestratorResult(
            final_output=final_output,
            step_outputs=outputs,
            decision_log=decision_log,
            artifacts_dir=str(run_dir) if run_dir else None,
        )

    def _render_prompt(self, task: TaskSpec, input_text: str, outputs: dict[str, str]) -> str:
        context = {"input": input_text, **outputs}
        return task.prompt_template.format(**context)

    def _run_one(self, task: TaskSpec, input_text: str, outputs: dict[str, str], decision_log: list[str]) -> str:
        agent = self.agents[task.agent_name]
        prompt = self._render_prompt(task, input_text, outputs)
        decision_log.append(f"Task '{task.name}' executed by '{task.agent_name}'")
        if self.hooks.on_step_start:
            self.hooks.on_step_start(task.name)
        try:
            result = agent.run(
                prompt,
                max_retries=self.run_config.max_retries,
                backoff_seconds=self.run_config.retry_backoff_seconds,
            )
            if self.hooks.on_step_end:
                self.hooks.on_step_end(task.name, result.content)
            return result.content
        except Exception as exc:  # noqa: BLE001
            if self.hooks.on_error:
                self.hooks.on_error(task.name, exc)
            raise

    def _run_linear(self, input_text: str, decision_log: list[str]) -> dict[str, str]:
        outputs: dict[str, str] = {}
        for task in self.tasks:
            outputs[task.name] = self._run_one(task, input_text, outputs, decision_log)
        return outputs

    def _run_parallel(self, input_text: str, decision_log: list[str]) -> dict[str, str]:
        outputs: dict[str, str] = {}

        pending = {task.name: task for task in self.tasks}
        completed: set[str] = set()

        with ThreadPoolExecutor(max_workers=max(1, len(self.tasks))) as ex:
            while pending:
                ready = [t for t in pending.values() if all(dep in completed for dep in t.depends_on)]
                if not ready:
                    unresolved = ", ".join(pending.keys())
                    raise RuntimeError(f"No runnable tasks. Check depends_on graph: {unresolved}")

                futures = {
                    task.name: ex.submit(self._run_one, task, input_text, outputs.copy(), decision_log)
                    for task in ready
                }
                for name, future in futures.items():
                    outputs[name] = future.result()
                    completed.add(name)
                    pending.pop(name, None)
        return outputs

    def _run_loop(self, input_text: str, decision_log: list[str]) -> dict[str, str]:
        outputs: dict[str, str] = {}
        for idx in range(1, self.workflow.max_iterations + 1):
            decision_log.append(f"Loop iteration {idx}")
            for task in self.tasks:
                outputs[task.name] = self._run_one(task, input_text, outputs, decision_log)
            last = outputs[self.tasks[-1].name] if self.tasks else ""
            if self.workflow.stop_condition_keyword.lower() in last.lower():
                decision_log.append(f"Stop condition met at iteration {idx}")
                break
        return outputs
