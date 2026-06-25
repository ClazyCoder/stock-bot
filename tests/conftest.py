from datetime import date, timedelta

import pytest

from schemas.llm import StockPriceLLMContext


def make_ohlcv_records(
    n: int,
    start_price: float = 100.0,
    start_date: str = "2024-01-01",
) -> list[StockPriceLLMContext]:
    """Return n StockPriceLLMContext objects with linearly increasing close prices."""
    base = date.fromisoformat(start_date)
    records = []
    for i in range(n):
        price = round(start_price + i, 2)
        records.append(
            StockPriceLLMContext.model_validate(
                {
                    "trade_date": (base + timedelta(days=i)).isoformat(),
                    "close_price": price,
                    "open_price": round(price - 0.5, 2),
                    "high_price": round(price + 1.0, 2),
                    "low_price": round(price - 1.0, 2),
                    "volume": 1_000_000 + i * 1000,
                }
            )
        )
    return records


@pytest.fixture
def ohlcv_30():
    return make_ohlcv_records(30)


@pytest.fixture
def ohlcv_250():
    return make_ohlcv_records(250, start_price=100.0)
