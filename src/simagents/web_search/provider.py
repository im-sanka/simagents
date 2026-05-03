from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass
class SearchItem:
    title: str
    content: str
    url: str


class WebSearchProvider(Protocol):
    def search(self, query: str, max_results: int = 5) -> list[SearchItem]:
        ...


def _http_json(url: str, *, method: str = "GET", headers: dict[str, str] | None = None, payload: dict | None = None) -> dict:
    body = None
    req_headers = headers or {}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        req_headers = {"Content-Type": "application/json", **req_headers}

    req = Request(url=url, data=body, headers=req_headers, method=method)
    with urlopen(req, timeout=30) as response:  # nosec B310
        raw = response.read().decode("utf-8")
    return json.loads(raw)


def format_search_results(items: list[SearchItem]) -> str:
    if not items:
        return "No search results found."
    lines: list[str] = []
    for item in items:
        lines.append(f"**{item.title}**\n{item.content}\nURL: {item.url}")
    return "\n\n---\n\n".join(lines)


class TavilySearchProvider:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.tavily.com/search") -> None:
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.base_url = base_url
        if not self.api_key:
            raise RuntimeError("Missing API key. Set TAVILY_API_KEY.")

    def search(self, query: str, max_results: int = 5) -> list[SearchItem]:
        data = _http_json(
            self.base_url,
            method="POST",
            payload={
                "api_key": self.api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "advanced",
            },
        )
        results = data.get("results", [])
        return [
            SearchItem(
                title=item.get("title", "No title"),
                content=item.get("content", ""),
                url=item.get("url", ""),
            )
            for item in results
        ]


class DuckDuckGoSearchProvider:
    def __init__(self, base_url: str = "https://api.duckduckgo.com/") -> None:
        self.base_url = base_url

    def search(self, query: str, max_results: int = 5) -> list[SearchItem]:
        params = urlencode({"q": query, "format": "json", "no_html": 1, "no_redirect": 1})
        data = _http_json(f"{self.base_url}?{params}")

        items: list[SearchItem] = []
        heading = data.get("Heading")
        abstract = data.get("AbstractText")
        abstract_url = data.get("AbstractURL")
        if heading or abstract:
            items.append(
                SearchItem(
                    title=heading or "DuckDuckGo Instant Answer",
                    content=abstract or "",
                    url=abstract_url or "",
                )
            )

        for topic in data.get("RelatedTopics", []):
            if isinstance(topic, dict) and "Text" in topic:
                items.append(
                    SearchItem(
                        title=topic.get("FirstURL", "DuckDuckGo Result"),
                        content=topic.get("Text", ""),
                        url=topic.get("FirstURL", ""),
                    )
                )
            elif isinstance(topic, dict) and "Topics" in topic:
                for nested in topic.get("Topics", []):
                    items.append(
                        SearchItem(
                            title=nested.get("FirstURL", "DuckDuckGo Result"),
                            content=nested.get("Text", ""),
                            url=nested.get("FirstURL", ""),
                        )
                    )

        return items[:max_results]


class GoogleCustomSearchProvider:
    def __init__(
        self,
        api_key: str | None = None,
        search_engine_id: str | None = None,
        base_url: str = "https://www.googleapis.com/customsearch/v1",
    ) -> None:
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.search_engine_id = search_engine_id or os.getenv("GOOGLE_CSE_ID")
        self.base_url = base_url

        if not self.api_key:
            raise RuntimeError("Missing API key. Set GOOGLE_API_KEY.")
        if not self.search_engine_id:
            raise RuntimeError("Missing CSE id. Set GOOGLE_CSE_ID.")

    def search(self, query: str, max_results: int = 5) -> list[SearchItem]:
        params = urlencode(
            {
                "key": self.api_key,
                "cx": self.search_engine_id,
                "q": query,
                "num": max(1, min(max_results, 10)),
            }
        )
        data = _http_json(f"{self.base_url}?{params}")
        return [
            SearchItem(
                title=item.get("title", "No title"),
                content=item.get("snippet", ""),
                url=item.get("link", ""),
            )
            for item in data.get("items", [])
        ]
