"""Тести для замикань make_counter, make_logger та make_pricing_policy."""

from __future__ import annotations

import pytest

from closures import make_counter, make_logger, make_pricing_policy


def test_make_counter_isolated_state() -> None:
    c1 = make_counter(10)
    c2 = make_counter(0)
    assert c1() == 11
    assert c1() == 12
    assert c2() == 1


def test_make_logger() -> None:
    messages: list[str] = []
    log = make_logger("INFO", sink=messages.append)
    log("ready")
    assert messages == ["[INFO] ready"]


def test_make_pricing_policy_nonlocal_state() -> None:
    calc_price, set_discount, get_discount = make_pricing_policy(
        initial_discount=0.10, vat_rate=0.20
    )
    assert get_discount() == 0.10
    assert calc_price(1000.0) == 1080.0

    set_discount(0.25)
    assert get_discount() == 0.25
    assert calc_price(1000.0) == 900.0

    with pytest.raises(ValueError):
        make_pricing_policy(initial_discount=1.2)
    with pytest.raises(ValueError):
        set_discount(-0.1)
    with pytest.raises(ValueError):
        calc_price(-50.0)
