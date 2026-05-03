from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any


class LLMResponseCache:
    """Small file-backed cache for exact LLM invocations."""

    def __init__(self, cache_dir: str = ".simagents_cache", ttl_seconds: int | None = None) -> None:
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def build_key(
        self,
        *,
        provider_name: str,
        model: str,
        temperature: float,
        prompt: str,
        provider_base_url: str | None = None,
    ) -> str:
        payload = {
            "version": 1,
            "provider_name": provider_name,
            "provider_base_url": provider_base_url,
            "model": model,
            "temperature": temperature,
            "prompt": prompt,
        }
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str) -> str | None:
        path = self._path_for_key(key)
        if not path.exists():
            return None

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

        created_at = data.get("created_at")
        if self.ttl_seconds is not None and isinstance(created_at, int | float):
            if time.time() - created_at > self.ttl_seconds:
                return None

        content = data.get("content")
        return content if isinstance(content, str) else None

    def set(self, key: str, content: str, metadata: dict[str, Any] | None = None) -> None:
        path = self._path_for_key(key)
        payload = {
            "created_at": time.time(),
            "content": content,
            "metadata": metadata or {},
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def _path_for_key(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"