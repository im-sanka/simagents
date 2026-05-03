import pytest

from simagents.utils.retry import with_retry


def test_retry_succeeds_after_two_failures() -> None:
    state = {"n": 0}

    def flaky() -> str:
        state["n"] += 1
        if state["n"] < 3:
            raise ValueError("temp")
        return "ok"

    assert with_retry(flaky, max_retries=3, backoff_seconds=0) == "ok"


def test_retry_raises_runtime_error() -> None:
    with pytest.raises(RuntimeError):
        with_retry(lambda: (_ for _ in ()).throw(ValueError("nope")), max_retries=2, backoff_seconds=0)
