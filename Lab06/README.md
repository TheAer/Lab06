# Лабораторна робота №6. Замикання та декоратори як HOF

**Варіант 3:** Кеш каталогу товарів (closure для цінової політики, `@cached(ttl)`, `@timed`).

## Структура проєкту
- `closures.py` — замикання `make_counter`, `make_logger` та `make_pricing_policy` (утримання знижки через `nonlocal`).
- `decorators.py` — параметризовані декоратори `@timed`, `@retries` та `@cached` (з `TTL`, `cache_clear()` і `cache_invalidate()`), типізовані через `ParamSpec`/`TypeVar` і захищені `@functools.wraps`.
- `app.py` / `main.py` — сервіс каталогу товарів `ProductCatalogService` з точковою інвалідацією кешу при зміні ціни товару.
- `tests/` — детерміновані тести `pytest` з ін'єкцією `clock`, `time_fn`, `sleep` і `logger`.

## Запуск та перевірка

```bash
python main.py
python -m pytest -v
mypy --strict closures.py decorators.py app.py main.py tests
ruff check .
black --check .
