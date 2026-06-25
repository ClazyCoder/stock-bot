from datetime import date, datetime

import pandas as pd
import pytest
from pydantic import ValidationError

from conftest import make_ohlcv_records
from schemas.llm import (
    StockPriceLLMContext,
    StockReportCreate,
    _pct_from_ratio,
    _safe_float,
    _safe_int,
    build_market_summary,
    classify_vs_ma,
    compute_rsi,
)


def test_safe_float_converts_int():
    assert _safe_float(42) == 42.0


def test_safe_float_none_returns_none():
    assert _safe_float(None) is None


def test_safe_float_nonnumeric_returns_none():
    assert _safe_float("abc") is None


def test_safe_int_converts_float():
    assert _safe_int(42.7) == 42


def test_safe_int_none_returns_none():
    assert _safe_int(None) is None


def test_pct_from_ratio_multiplies_by_100():
    assert _pct_from_ratio(0.71068) == pytest.approx(71.068)


def test_pct_from_ratio_none_returns_none():
    assert _pct_from_ratio(None) is None


def test_classify_vs_ma_above():
    assert classify_vs_ma(110.0, 100.0) == "above"


def test_classify_vs_ma_below():
    assert classify_vs_ma(89.0, 100.0) == "below"


def test_classify_vs_ma_near():
    assert classify_vs_ma(100.5, 100.0) == "near"


def test_classify_vs_ma_none_ma():
    assert classify_vs_ma(100.0, None) == "unknown"


def test_compute_rsi_all_gains_high_rsi():
    series = pd.Series(range(1, 31))
    result = compute_rsi(series)

    assert result.dropna().iloc[-1] > 70


def test_compute_rsi_all_losses_low_rsi():
    series = pd.Series(range(30, 0, -1))
    result = compute_rsi(series)

    assert result.dropna().iloc[-1] < 30


def test_compute_rsi_short_series_nan():
    result = compute_rsi(pd.Series([100.0] * 5))

    assert result.isna().all()


def test_build_market_summary_no_records():
    result = build_market_summary([], None)

    assert result.warning == "No OHLCV records provided."
    assert all(
        value is None
        for key, value in result.model_dump().items()
        if key != "warning"
    )


def test_build_market_summary_single_record():
    result = build_market_summary(make_ohlcv_records(1), None)

    assert result.current_price == 100.0
    assert result.return_1d_pct is None
    assert result.ma_20 is None


def test_build_market_summary_with_info_pe():
    result = build_market_summary(
        make_ohlcv_records(5),
        {"trailingPE": 25.0, "forwardPE": 20.0},
    )

    assert result.trailing_pe == 25.0
    assert result.forward_pe == 20.0


def test_build_market_summary_info_price_overrides_close():
    result = build_market_summary(
        make_ohlcv_records(1, start_price=100.0),
        {"currentPrice": 105.0},
    )

    assert result.current_price == 105.0


def test_build_market_summary_20_records_has_ma20():
    result = build_market_summary(make_ohlcv_records(20), None)

    assert result.ma_20 is not None
    assert result.ma_50 is None


def test_stock_price_llm_context_date_from_datetime():
    ctx = StockPriceLLMContext.model_validate(
        {
            "trade_date": datetime(2024, 6, 15, 9, 30),
            "close_price": 150.0,
            "open_price": 149.0,
            "high_price": 151.0,
            "low_price": 148.0,
            "volume": 1_000_000,
        }
    )

    assert ctx.date == "2024-06-15"


def test_stock_price_llm_context_rounds_price_to_2dp():
    ctx = StockPriceLLMContext.model_validate(
        {
            "trade_date": "2024-06-15",
            "close_price": 150.1234,
            "open_price": 149.1234,
            "high_price": 151.1234,
            "low_price": 148.1234,
            "volume": 1_000_000,
        }
    )

    assert ctx.close == 150.12


def test_stock_report_create_from_datetime():
    report = StockReportCreate(
        ticker="AAPL",
        report="text",
        created_at=datetime(2024, 3, 15, 10, 0),
    )

    assert report.created_at == date(2024, 3, 15)


def test_stock_report_create_from_date_string():
    report = StockReportCreate(
        ticker="AAPL",
        report="text",
        created_at="2024-03-15",
    )

    assert report.created_at == date(2024, 3, 15)


def test_stock_report_create_invalid_string_raises():
    with pytest.raises(ValidationError):
        StockReportCreate(
            ticker="AAPL",
            report="text",
            created_at="not-a-date",
        )
