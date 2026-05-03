# Changelog

## 0.2.1

- Added opt-in exact LLM response caching to reduce repeated token/API usage
- Added cache configuration fields to `RunConfig`
- Added file-backed `LLMResponseCache`
- Added cache hit/miss decision log entries
- Added cache tests
- Refreshed README with badges, caching docs, MIT footer, and project note

## 0.2.0

- Updated `OllamaCloudProvider` default base URL to `https://ollama.com/v1`
- Added pluggable web search providers under `simagents.web_search`:
  - `TavilySearchProvider` (`TAVILY_API_KEY`)
  - `DuckDuckGoSearchProvider` (no API key required)
  - `GoogleCustomSearchProvider` (`GOOGLE_API_KEY`, `GOOGLE_CSE_ID`)
- Added `SearchItem` model and `format_search_results(...)` helper
- Exported web search providers from top-level `simagents` package

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
