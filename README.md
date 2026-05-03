# simagents

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Ollama](https://img.shields.io/badge/Ollama-ready-black)
![OpenAI](https://img.shields.io/badge/OpenAI-compatible-green)
![Anthropic](https://img.shields.io/badge/Anthropic-Claude-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

`simagents` is a lightweight Python framework for building multi-agent workflows with:

- 🔁 Linear, parallel, and loop orchestration modes
- 🤖 Agent-level model configuration
- 🧭 Prompt-planning friendly task chaining
- 📝 Safe decision logs (reasoning summaries)
- 💾 Retry/backoff + run artifact persistence
- ⚡ Optional exact-response caching to reduce repeated LLM calls

## Why simagents (vs broader frameworks)

- **Workflow-first** 🔁: orchestration mode is a first-class setting (`linear`, `parallel`, `loop`)
- **Prompt-planning native** 🧭: easy to build research → prompt-plan → execution flows
- **Simple API** ✨: define agents + tasks + workflow, then run
- **Production-lite defaults** 🧰: retries, logs, artifact folders, decision logs, optional cache

## Install

From PyPI:

```bash
pip install simagents
```

For local development from the `simagents/` folder:

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

If you do **not** pass a provider explicitly to `EasyOrchestrator`, `simagents` uses
`OpenAICompatibleProvider()` by default. In that case, set either:

```bash
export SIMAGENTS_API_KEY="your_api_key_here"
export SIMAGENTS_BASE_URL="https://api.openai.com/v1"
```

or set OpenAI's standard key:

```bash
export OPENAI_API_KEY="sk-..."
```

For a one-off command without saving the variables in your shell session:

```bash
OPENAI_API_KEY="sk-..." python examples/research_prompt_plan.py
```

For an OpenAI-compatible provider such as Ollama Cloud:

```bash
SIMAGENTS_API_KEY="your_ollama_key" \
SIMAGENTS_BASE_URL="https://ollama.com/v1" \
python examples/research_prompt_plan.py
```

> Note: the model names in your agents must match the provider you use. The bundled
> `examples/research_prompt_plan.py` uses `gpt-4o-mini`, which is an OpenAI model.
> If you run it against Ollama Cloud, change the example agent models to an Ollama
> Cloud model such as `gpt-oss:120b-cloud`.

Fallback key env var:
- `OPENAI_API_KEY`

Provider-specific common keys:
- `OLLAMA_API_KEY`, `OLLAMA_BASE_URL`
- `OLLAMA_CLOUD_API_KEY`, `OLLAMA_CLOUD_BASE_URL` (defaults to `https://ollama.com/v1`)
- `GROQ_API_KEY`
- `TOGETHER_API_KEY`
- `OPENROUTER_API_KEY`
- `ANTHROPIC_API_KEY`

Web search provider keys:
- `TAVILY_API_KEY`
- `GOOGLE_API_KEY`
- `GOOGLE_CSE_ID`

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

## LLM response caching

`simagents` can cache exact LLM invocations to reduce token/API usage when agents repeat the same work.

Caching is disabled by default so prompt iteration remains fresh and unsurprising. Enable it in `RunConfig`:

```python
run_config = RunConfig(
    output_dir="runs",
    save_artifacts=True,
    cache_enabled=True,
    cache_dir=".simagents_cache",
    cache_ttl_seconds=None,  # optional; set seconds to expire old entries
)
```

Cache keys include:

- provider class name
- provider base URL, when available
- model
- temperature
- full rendered prompt
- internal cache version

This means caching is safe and deterministic for exact repeats. If the prompt, model, temperature, or provider changes, `simagents` treats it as a new call.

When caching is enabled, the decision log notes whether a task stored fresh output or reused cached output.

## Orchestration modes

- `WorkflowMode.LINEAR`: run tasks one by one
- `WorkflowMode.PARALLEL`: run tasks concurrently
- `WorkflowMode.LOOP`: rerun full task chain until stop keyword appears or max iterations reached

In `PARALLEL` mode, `TaskSpec.depends_on` is respected as a dependency graph.

Loop controls:
- `WorkflowSpec.max_iterations`
- `WorkflowSpec.stop_condition_keyword`

## Flagship example: research + prompt planning

From the `simagents/` folder, run:

```bash
python examples/research_prompt_plan.py
```

If you installed `simagents` from the workspace root and want to run the example
directly from this repository, you can also run:

```bash
python simagents/examples/research_prompt_plan.py
```

### Running the example with API keys

OpenAI, using the example as-is (`gpt-4o-mini`):

```bash
OPENAI_API_KEY="sk-..." python simagents/examples/research_prompt_plan.py
```

OpenAI-compatible endpoint:

```bash
SIMAGENTS_API_KEY="your_key" \
SIMAGENTS_BASE_URL="https://api.openai.com/v1" \
python simagents/examples/research_prompt_plan.py
```

Ollama Cloud one-liner:

```bash
SIMAGENTS_API_KEY="your_ollama_key" \
SIMAGENTS_BASE_URL="https://ollama.com/v1" \
python simagents/examples/research_prompt_plan.py
```

For Ollama Cloud, update the example models first, for example:

```python
model="gpt-oss:120b-cloud"
```

You can also export keys once per terminal session:

```bash
export OPENAI_API_KEY="sk-..."
python simagents/examples/research_prompt_plan.py
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

## Web search providers (Tavily, DuckDuckGo, Google CSE)

You can use pluggable search providers:

```python
from simagents import (
    TavilySearchProvider,
    DuckDuckGoSearchProvider,
    GoogleCustomSearchProvider,
    format_search_results,
)

# Tavily
tavily = TavilySearchProvider()  # needs TAVILY_API_KEY
print(format_search_results(tavily.search("AI bioinformatics", max_results=3)))

# DuckDuckGo (instant answer + related topics)
ddg = DuckDuckGoSearchProvider()
print(format_search_results(ddg.search("AI bioinformatics", max_results=3)))

# Google Custom Search JSON API
google = GoogleCustomSearchProvider()  # needs GOOGLE_API_KEY + GOOGLE_CSE_ID
print(format_search_results(google.search("AI bioinformatics", max_results=3)))
```

## Lifecycle hooks

You can attach optional hooks for observability/instrumentation:

- `on_step_start(step_name)`
- `on_step_end(step_name, output)`
- `on_error(step_name, exception)`

## Testing

```bash
pytest -q
```

## License

MIT License. See [`LICENSE`](LICENSE) for details.

---

Built with <3 on a cloudy Sunday.
