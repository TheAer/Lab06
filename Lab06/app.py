"""Каталог товарів із кешуванням, ціновою політикою та вимірюванням часу (Варіант 3)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import time
from typing import Any

from closures import make_counter, make_logger, make_pricing_policy
from decorators import cached, timed


@dataclass(frozen=True, slots=True)
class ProductRecord:
    """Картка товару в каталозі."""

    product_id: int
    name: str
    base_price: float


class ProductCatalogService:
    """Сервіс каталогу товарів (Варіант 3): цінова політика + @cached(ttl) + @timed."""

    def __init__(
        self,
        products: dict[int, ProductRecord],
        *,
        ttl: float = 30.0,
        initial_discount: float = 0.10,
        vat_rate: float = 0.20,
        time_fn: Callable[[], float] = time.time,
        clock: Callable[[], float] = time.perf_counter,
        logger: Callable[[str], None] = print,
    ) -> None:
        self._products = dict(products)
        self._logger = logger
        self._db_reads = make_counter(0)
        self._calc_price, self._set_discount, self._get_discount = make_pricing_policy(
            initial_discount=initial_discount,
            vat_rate=vat_rate,
        )

        @timed("catalog.get_product", unit="ms", logger=self._logger, clock=clock)
        @cached(ttl=ttl, time_fn=time_fn)
        def _fetch_product(product_id: int) -> dict[str, Any]:
            read_num = self._db_reads()
            if product_id not in self._products:
                raise KeyError(f"Товар із product_id={product_id} не знайдено.")
            item = self._products[product_id]
            return {
                "product_id": item.product_id,
                "name": item.name,
                "base_price": item.base_price,
                "final_price": self._calc_price(item.base_price),
                "discount": self._get_discount(),
                "source_read_seq": read_num,
            }

        self._fetch_product = _fetch_product

    def get_product(self, product_id: int) -> dict[str, Any]:
        """Повертає актуальну картку товару (з кешу або з джерела даних)."""
        return self._fetch_product(product_id)

    def update_base_price(self, product_id: int, new_base_price: float) -> int:
        """Оновлює базову ціну товару та точково інвалідовує кеш за product_id."""
        if new_base_price < 0.0:
            raise ValueError("Базова ціна не може бути від'ємною.")
        if product_id not in self._products:
            raise KeyError(f"Товар із product_id={product_id} не знайдено.")
        old_item = self._products[product_id]
        self._products[product_id] = ProductRecord(
            product_id=old_item.product_id,
            name=old_item.name,
            base_price=new_base_price,
        )
        removed: int = self._fetch_product.cache_invalidate(  # type: ignore[attr-defined]
            lambda args, kwargs: (len(args) > 0 and args[0] == product_id)
            or kwargs.get("product_id") == product_id
        )
        self._logger(
            f"[catalog] Оновлено ціну товару id={product_id} -> {new_base_price:.2f}; "
            f"інвалідовано записів кешу: {removed}"
        )
        return removed

    def update_discount_policy(self, new_discount: float) -> None:
        """Змінює глобальну знижку у замиканні та повністю очищує кеш каталогу."""
        self._set_discount(new_discount)
        self._fetch_product.cache_clear()  # type: ignore[attr-defined]
        self._logger(
            f"[catalog] Оновлено знижку до {new_discount * 100:.0f}%; кеш каталогу очищено."
        )


def run_demo() -> None:
    """Демонстрація роботи кешу каталогу товарів (Варіант 3)."""
    log = make_logger("CATALOG-DEMO")
    initial_items = {
        101: ProductRecord(101, "Механічна клавіатура Akko 5075B", 3200.0),
        102: ProductRecord(102, "Планарні навушники KZ PR2", 1800.0),
    }
    service = ProductCatalogService(
        initial_items,
        ttl=60.0,
        initial_discount=0.10,
        vat_rate=0.20,
        logger=log,
    )

    log("1. Перший запит товару 101 (cache miss -> обчислення):")
    print("   ->", service.get_product(101))

    log("2. Повторний запит товару 101 (cache hit -> миттєво з кешу):")
    print("   ->", service.get_product(101))

    log("3. Запит товару 102 (cache miss):")
    print("   ->", service.get_product(102))

    log("4. Зміна ціни товару 101 -> точкова інвалідація лише для product_id=101:")
    service.update_base_price(101, 2900.0)
    print("   -> Товар 101 (перераховано):", service.get_product(101))
    print("   -> Товар 102 (залишився в кеші, read_seq=2):", service.get_product(102))


if __name__ == "__main__":
    run_demo()
