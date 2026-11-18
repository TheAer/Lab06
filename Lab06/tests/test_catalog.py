"""Тести для ProductCatalogService (Варіант 3: кеш каталогу товарів)."""

from __future__ import annotations

import pytest

from app import ProductCatalogService, ProductRecord


def test_catalog_cache_hit_miss_and_invalidation_by_product_id() -> None:
    now = 500.0
    perf = [0.0, 0.002, 0.010, 0.0101, 0.020, 0.023, 0.030, 0.0301, 0.040, 0.045]
    logs: list[str] = []

    service = ProductCatalogService(
        {
            1: ProductRecord(1, "Laptop", 1000.0),
            2: ProductRecord(2, "Mouse", 100.0),
        },
        ttl=10.0,
        initial_discount=0.10,
        vat_rate=0.20,
        time_fn=lambda: now,
        clock=lambda: perf.pop(0),
        logger=logs.append,
    )

    # Перший запит -> cache miss
    p1 = service.get_product(1)
    assert p1["final_price"] == 1080.0
    assert p1["source_read_seq"] == 1

    # Другий запит -> cache hit
    p1_cached = service.get_product(1)
    assert p1_cached["source_read_seq"] == 1

    # Запит другого товару -> cache miss
    p2 = service.get_product(2)
    assert p2["final_price"] == 108.0
    assert p2["source_read_seq"] == 2

    # Зміна ціни товару 1 -> інвалідує лише product_id=1, не зачіпаючи product_id=2
    removed = service.update_base_price(1, 2000.0)
    assert removed == 1

    p1_updated = service.get_product(1)
    assert p1_updated["final_price"] == 2160.0
    assert p1_updated["source_read_seq"] == 3

    p2_still_cached = service.get_product(2)
    assert p2_still_cached["source_read_seq"] == 2


def test_catalog_ttl_expiration_with_fake_clock() -> None:
    now = 100.0
    perf = [0.0, 0.001, 0.010, 0.012, 0.020, 0.025]
    service = ProductCatalogService(
        {10: ProductRecord(10, "Keyboard", 500.0)},
        ttl=5.0,
        initial_discount=0.0,
        vat_rate=0.20,
        time_fn=lambda: now,
        clock=lambda: perf.pop(0),
        logger=lambda _: None,
    )

    assert service.get_product(10)["source_read_seq"] == 1
    now += 4.9  # ще в межах TTL
    assert service.get_product(10)["source_read_seq"] == 1
    now += 0.2  # TTL=5.0 вичерпано
    assert service.get_product(10)["source_read_seq"] == 2

    with pytest.raises(KeyError):
        service.get_product(999)
