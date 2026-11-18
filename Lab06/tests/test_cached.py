"""Тести для декоратора @cached з TTL, cache_clear та cache_invalidate."""

from __future__ import annotations

import pytest

from decorators import cached


def test_cached_ttl_and_invalidation() -> None:
    now = 1000.0
    computations = 0

    @cached(ttl=5.0, time_fn=lambda: now)
    def compute(x: int) -> int:
        """Подвоює аргумент."""
        nonlocal computations
        computations += 1
        return x * 2

    assert compute.__name__ == "compute"
    assert compute.__doc__ == "Подвоює аргумент."
    assert hasattr(compute, "__wrapped__")

    assert compute(10) == 20
    assert compute(10) == 20
    assert computations == 1

    # Протухання TTL (минуло 6 секунд > 5.0)
    now += 6.0
    assert compute(10) == 20
    assert computations == 2

    # Точкова інвалідація за предикатом
    compute(20)
    assert computations == 3
    removed = compute.cache_invalidate(lambda args, kwargs: args == (10,))  # type: ignore[attr-defined]
    assert removed == 1
    assert compute(10) == 20
    assert compute(20) == 40
    assert computations == 4

    # Повне очищення кешу
    compute.cache_clear()  # type: ignore[attr-defined]
    assert compute(20) == 40
    assert computations == 5


def test_cached_invalid_ttl_raises() -> None:
    with pytest.raises(ValueError):
        cached(ttl=0.0)
