"""Замикання (closures) для утримання стану та ін'єкції залежностей (Лабораторна №6, Варіант 3)."""

from __future__ import annotations

from collections.abc import Callable


def make_counter(start: int = 0) -> Callable[[], int]:
    """Створює замикання-лічильник, що зберігає та оновлює стан через nonlocal."""
    value = start

    def inc() -> int:
        nonlocal value
        value += 1
        return value

    return inc


def make_logger(prefix: str, sink: Callable[[str], None] = print) -> Callable[[str], None]:
    """Створює замикання-логер із фіксованим префіксом та ін'єкцією функції виведення."""

    def log(message: str) -> None:
        sink(f"[{prefix}] {message}")

    return log


def make_pricing_policy(
    initial_discount: float = 0.0,
    vat_rate: float = 0.20,
) -> tuple[Callable[[float], float], Callable[[float], None], Callable[[], float]]:
    """Замикання цінової політики каталогу товарів (Варіант 3).

    Утримує поточну знижку (current_discount) у лексичному оточенні через nonlocal.
    Повертає кортеж функцій:
    - calculate_final_price(base_price): обчислює фінальну ціну зі знижкою та ПДВ;
    - update_discount(new_discount): змінює ставку знижки у стані замикання;
    - get_discount(): повертає активну ставку знижки.
    """
    if not 0.0 <= initial_discount < 1.0:
        raise ValueError("Знижка має бути в діапазоні [0.0, 1.0).")
    if vat_rate < 0.0:
        raise ValueError("Ставка податку не може бути від'ємною.")

    current_discount = initial_discount

    def calculate_final_price(base_price: float) -> float:
        if base_price < 0.0:
            raise ValueError("Базова ціна товару не може бути від'ємною.")
        discounted = base_price * (1.0 - current_discount)
        return round(discounted * (1.0 + vat_rate), 2)

    def update_discount(new_discount: float) -> None:
        nonlocal current_discount
        if not 0.0 <= new_discount < 1.0:
            raise ValueError("Знижка має бути в діапазоні [0.0, 1.0).")
        current_discount = new_discount

    def get_discount() -> float:
        return current_discount

    return calculate_final_price, update_discount, get_discount
