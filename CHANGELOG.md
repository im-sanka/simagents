# Changelog

## 0.1.0

- Initial release of `simagents`
- Multi-agent orchestration modes: linear, parallel, loop
- Task dependency support in parallel mode (`depends_on`)
- Safe decision logs and run artifacts
- Retry/backoff utilities
- Provider adapters:
  - OpenAI
  - OpenAI-compatible
  - Ollama
  - Groq
  - Together
  - OpenRouter
  - Anthropic (Claude)
- Lifecycle hooks (`on_step_start`, `on_step_end`, `on_error`)
- Research → prompt-planning flagship example
