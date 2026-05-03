# simagents

`simagents` is a lightweight Python framework for building multi-agent workflows with:

- Linear, parallel, and loop orchestration modes
- Agent-level model configuration
- Prompt-planning friendly task chaining
- Safe decision logs (reasoning summaries)
- Retry/backoff + run artifact persistence

## Why simagents (vs broader frameworks)

- **Workflow-first**: orchestration mode is a first-class setting (`linear`, `parallel`, `loop`)
- **Prompt-planning native**: easy to build research → prompt-plan → execution flows
- **Simple API**: define agents + tasks + workflow, then run
- **Production-lite defaults**: retries, logs, artifact folders, decision logs

## Install (local)

From the `simagents/` folder:

```bash
pip install -e .
```

For tests/dev:

```bash
pip install -e ".[dev]"
```

## Environment variables

`simagents` supports multiple provider adapters via the OpenAI SDK-compatible interface:

- `OpenAIProvider`
- `OllamaProvider`
- `OllamaCloudProvider`
- `GroqProvider`
- `TogetherProvider`
- `OpenRouterProvider`
- `AnthropicProvider` (Claude)
- `OpenAICompatibleProvider` (custom base URL)

Base env vars:

```env
SIMAGENTS_API_KEY=your_key
SIMAGENTS_BASE_URL=https://api.openai.com/v1
```

Fallback key env var:
- `OPENAI_API_KEY`

Provider-specific common keys:
- `OLLAMA_API_KEY`, `OLLAMA_BASE_URL`
- `OLLAMA_CLOUD_API_KEY`, `OLLAMA_CLOUD_BASE_URL` (defaults to `https://ollama.com/`)
- `GROQ_API_KEY`
- `TOGETHER_API_KEY`
- `OPENROUTER_API_KEY`
- `ANTHROPIC_API_KEY`

Claude model examples:
- `claude-4-6-sonnet-latest`
- `claude-4-7-opus-latest`

## Quickstart

```python
from simagents import AgentSpec, EasyOrchestrator, RunConfig, TaskSpec, WorkflowSpec
from simagents.core.models import WorkflowMode
from simagents.llm import AnthropicProvider, OpenAIProvider

agents = [
    AgentSpec(name="researcher", role="Research specialist", model="gpt-4o-mini"),
    AgentSpec(name="writer", role="Technical writer", model="gpt-4o-mini"),
]

tasks = [
    TaskSpec(name="research", agent_name="researcher", prompt_template="Research: {input}"),
    TaskSpec(name="final", agent_name="writer", prompt_template="Write post using: {research}"),
]

workflow = WorkflowSpec(mode=WorkflowMode.LINEAR)
run_config = RunConfig(output_dir="runs", save_artifacts=True)

orch = EasyOrchestrator(
    agents=agents,
    tasks=tasks,
    workflow=workflow,
    run_config=run_config,
    provider=OpenAIProvider(),
)
result = orch.run(input_text="How AI is changing bioinformatics")
print(result.final_output)
print(result.decision_log)

# Claude usage (swap provider)
# orch = EasyOrchestrator(
#     agents=agents,
#     tasks=tasks,
#     workflow=workflow,
#     run_config=run_config,
#     provider=AnthropicProvider(),
# )
```

## Orchestration modes

- `WorkflowMode.LINEAR`: run tasks one by one
- `WorkflowMode.PARALLEL`: run tasks concurrently
- `WorkflowMode.LOOP`: rerun full task chain until stop keyword appears or max iterations reached

In `PARALLEL` mode, `TaskSpec.depends_on` is respected as a dependency graph.

Loop controls:
- `WorkflowSpec.max_iterations`
- `WorkflowSpec.stop_condition_keyword`

## Flagship example: research + prompt planning

Run:

```bash
python examples/research_prompt_plan.py
```

This example demonstrates:
1. Research agent gathers structured topic context
2. Planner agent turns research into a high-quality prompt blueprint
3. Writer agent executes using that prompt plan

## Output artifacts

When `save_artifacts=True`, each run creates:

- `runs/run-<timestamp>/decision_log.md`
- `runs/run-<timestamp>/final_output.md`
- one markdown file per task name

## Lifecycle hooks

You can attach optional hooks for observability/instrumentation:

- `on_step_start(step_name)`
- `on_step_end(step_name, output)`
- `on_error(step_name, exception)`

## Testing

```bash
pytest -q
```
