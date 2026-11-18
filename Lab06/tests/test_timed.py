"""Тести для декоратора @timed з ін'єкцією clock та logger."""

from __future__ import annotations

import pytest

from decorators import timed


def test_timed_uses_clock_and_preserves_metadata() -> None:
    ticks = [0.0, 0.012345]
    logs: list[str] = []

    @timed("work", unit="ms", logger=logs.append, clock=lambda: ticks.pop(0))
    def work(x: int) -> int:
        """Обчислює квадрат числа."""
        return x * x

    assert work.__name__ == "work"
    assert work.__doc__ == "Обчислює квадрат числа."
    assert hasattr(work, "__wrapped__")

    assert work(5) == 25
    assert any("work took 12.345 ms" in line for line in logs)


def test_timed_logs_on_exception() -> None:
    ticks = [1.0, 1.5]
    logs: list[str] = []

    @timed("failing", unit="s", logger=logs.append, clock=lambda: ticks.pop(0))
    def boom() -> None:
        raise RuntimeError("error")

    with pytest.raises(RuntimeError):
        boom()
    assert any("failing took 0.500 s" in line for line in logs)
