import json
from urllib.parse import parse_qs, urlparse

import pytest

from simagents.web_search.provider import (
    DuckDuckGoSearchProvider,
    GoogleCustomSearchProvider,
    SearchItem,
    TavilySearchProvider,
    format_search_results,
)


def test_format_search_results() -> None:
    text = format_search_results([SearchItem(title="A", content="B", url="https://x")])
    assert "**A**" in text
    assert "URL: https://x" in text


def test_tavily_missing_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        TavilySearchProvider()


def test_google_missing_config_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_CSE_ID", raising=False)
    with pytest.raises(RuntimeError):
        GoogleCustomSearchProvider()


def test_duckduckgo_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    from simagents.web_search import provider as provider_mod

    def fake_http_json(url: str, **kwargs) -> dict:
        _ = kwargs
        assert "api.duckduckgo.com" in url
        return {
            "Heading": "Bioinformatics",
            "AbstractText": "AI + Bio workflows",
            "AbstractURL": "https://example.com/abstract",
            "RelatedTopics": [
                {"Text": "Topic 1", "FirstURL": "https://example.com/1"},
                {"Topics": [{"Text": "Topic 2", "FirstURL": "https://example.com/2"}]},
            ],
        }

    monkeypatch.setattr(provider_mod, "_http_json", fake_http_json)

    provider = DuckDuckGoSearchProvider()
    items = provider.search("ai bioinformatics", max_results=2)
    assert len(items) == 2
    assert items[0].title == "Bioinformatics"


def test_google_query_params(monkeypatch: pytest.MonkeyPatch) -> None:
    from simagents.web_search import provider as provider_mod

    captured = {"url": ""}

    def fake_http_json(url: str, **kwargs) -> dict:
        _ = kwargs
        captured["url"] = url
        return {"items": [{"title": "T", "snippet": "S", "link": "https://g"}]}

    monkeypatch.setattr(provider_mod, "_http_json", fake_http_json)

    provider = GoogleCustomSearchProvider(api_key="k", search_engine_id="cx")
    items = provider.search("hello", max_results=7)
    assert len(items) == 1
    parsed = urlparse(captured["url"])
    query = parse_qs(parsed.query)
    assert query["key"][0] == "k"
    assert query["cx"][0] == "cx"
    assert query["q"][0] == "hello"


def test_tavily_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    from simagents.web_search import provider as provider_mod

    captured = {"payload": {}}

    def fake_http_json(url: str, **kwargs) -> dict:
        captured["payload"] = kwargs.get("payload", {})
        assert url == "https://api.tavily.com/search"
        return {"results": [{"title": "R", "content": "C", "url": "https://t"}]}

    monkeypatch.setattr(provider_mod, "_http_json", fake_http_json)

    provider = TavilySearchProvider(api_key="tk")
    items = provider.search("q", max_results=3)
    assert len(items) == 1
    assert captured["payload"]["api_key"] == "tk"
    assert captured["payload"]["max_results"] == 3
