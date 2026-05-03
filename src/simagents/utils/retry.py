from __future__ import annotations

import time
from typing import Callable, TypeVar


T = TypeVar("T")


def with_retry(fn: Callable[[], T], max_retries: int, backoff_seconds: float) -> T:
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt == max_retries:
                break
            time.sleep(backoff_seconds * attempt)
    raise RuntimeError(f"Operation failed after {max_retries} attempts: {last_error}")
