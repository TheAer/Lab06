"""Параметризовані декоратори (HOF): @timed, @retries, @cached з інвалідацією (Лабораторна №6)."""

from __future__ import annotations

from collections.abc import Callable, Hashable
import functools
import random
import threading
import time
from typing import Any, Literal, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def timed(
    label: str | None = None,
    *,
    unit: Literal["s", "ms", "us"] = "ms",
    logger: Callable[[str], None] = print,
    clock: Callable[[], float] = time.perf_counter,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Параметризований декоратор вимірювання часу виконання з ін'єкцією clock та logger."""
    factors: dict[Literal["s", "ms", "us"], float] = {"s": 1.0, "ms": 1e3, "us": 1e6}
    factor = factors[unit]

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        display_name = label or func.__name__

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            t0 = clock()
            try:
                return func(*args, **kwargs)
            finally:
                dt = (clock() - t0) * factor
                logger(f"[timed] {display_name} took {dt:.3f} {unit}")

        return wrapper

    return decorator


def retries(
    attempts: int = 3,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
    delay: float = 0.0,
    backoff: float = 1.0,
    jitter: float = 0.0,
    *,
    sleep: Callable[[float], None] = time.sleep,
    logger: Callable[[str], None] = lambda _: None,
    rand_fn: Callable[[], float] = random.random,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Параметризований декоратор повторних викликів з експоненційним бекофом та джиттером."""
    if attempts < 1:
        raise ValueError("Кількість спроб attempts має бути >= 1.")
    if delay < 0.0 or backoff < 1.0 or jitter < 0.0:
        raise ValueError("Некоректні параметри затримки (delay/backoff/jitter).")

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            last_exc: BaseException | None = None
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == attempts:
                        logger(f"[retries] fail after {attempt} attempts: {exc!r}")
                        break
                    jitter_add = rand_fn() * jitter if jitter > 0.0 else 0.0
                    wait = delay * (backoff ** (attempt - 1)) + jitter_add
                    logger(
                        f"[retries] attempt {attempt} failed: {exc!r}; sleeping {wait:.3f}s"
                    )
                    sleep(wait)
            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator


def make_cache_key(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Hashable:
    """Формує детермінований хешований ключ із позиційних та іменованих аргументів."""
    return (args, tuple(sorted(kwargs.items())))


def cached(
    *,
    ttl: float | None = None,
    time_fn: Callable[[], float] = time.time,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Параметризований декоратор кешування з TTL та методами cache_clear/cache_invalidate."""
    if ttl is not None and ttl <= 0.0:
        raise ValueError("Час життя кешу ttl має бути додатним числом або None.")

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        cache: dict[Hashable, tuple[float | None, R]] = {}
        lock = threading.Lock()

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            key = make_cache_key(args, kwargs)
            now = time_fn()
            with lock:
                if key in cache:
                    expires_at, cached_val = cache[key]
                    if expires_at is None or now < expires_at:
                        return cached_val
                    del cache[key]

            result = func(*args, **kwargs)
            with lock:
                expiry = None if ttl is None else time_fn() + ttl
                cache[key] = (expiry, result)
            return result

        def cache_clear() -> None:
            with lock:
                cache.clear()

        def cache_invalidate(
            predicate: Callable[[tuple[Any, ...], dict[str, Any]], bool],
        ) -> int:
            removed = 0
            with lock:
                for k in list(cache.keys()):
                    args_k, kwargs_pairs = k  # type: ignore[misc]
                    if predicate(args_k, dict(kwargs_pairs)):
                        del cache[k]
                        removed += 1
            return removed

        wrapper.cache_clear = cache_clear  # type: ignore[attr-defined]
        wrapper.cache_invalidate = cache_invalidate  # type: ignore[attr-defined]
        return wrapper

    return decorator
