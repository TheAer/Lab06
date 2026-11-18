"""Тести для декоратора @retries без реальних затримок sleep."""

from __future__ import annotations

import pytest

from decorators import retries


def test_retries_backoff_and_metadata() -> None:
    calls = 0
    slept: list[float] = []

    @retries(
        attempts=3,
        exceptions=(RuntimeError,),
        delay=0.5,
        backoff=2.0,
        sleep=slept.append,
    )
    def flaky() -> str:
        """Нестабільна операція."""
        nonlocal calls
        calls += 1
        if calls < 3:
            raise RuntimeError("boom")
        return "ok"

    assert flaky.__name__ == "flaky"
    assert flaky.__doc__ == "Нестабільна операція."
    assert hasattr(flaky, "__wrapped__")

    assert flaky() == "ok"
    assert calls == 3
    assert slept == [0.5, 1.0]


def test_retries_exhausted_raises() -> None:
    @retries(attempts=2, exceptions=(ValueError,), delay=0.0, sleep=lambda _: None)
    def always_bad() -> None:
        raise ValueError("invalid")

    with pytest.raises(ValueError, match="invalid"):
        always_bad()
