from unittest.mock import MagicMock, patch

import pandas as pd

from collectors.stock_api import StockDataCollector
from schemas.stock import StockPriceCreate


def make_flat_df(
    close=150.0,
    open_=149.0,
    high=152.0,
    low=148.0,
    volume=1_000_000,
):
    return pd.DataFrame(
        {
            "Close": [close],
            "Open": [open_],
            "High": [high],
            "Low": [low],
            "Volume": [volume],
        },
        index=pd.to_datetime(["2024-01-02"]),
    )


def make_multi_df(tickers: list[str]):
    cols = pd.MultiIndex.from_tuples(
        [(ticker, field) for ticker in tickers for field in ["Close", "Open", "High", "Low", "Volume"]]
    )
    row = [value for _ in tickers for value in [150.0, 149.0, 151.0, 148.0, 1_000_000]]
    return pd.DataFrame([row], columns=cols, index=pd.to_datetime(["2024-01-02"]))


async def test_fetch_single_ticker_flat_columns():
    collector = StockDataCollector()

    with patch("collectors.stock_api.yf.download", return_value=make_flat_df()):
        result = await collector.fetch_stock_price("AAPL")

    assert len(result) == 1
    assert isinstance(result[0], StockPriceCreate)
    assert result[0].close_price == 150.0
    assert result[0].ticker == "AAPL"


async def test_fetch_single_ticker_multiindex_columns():
    collector = StockDataCollector()

    with patch("collectors.stock_api.yf.download", return_value=make_multi_df(["AAPL"])):
        result = await collector.fetch_stock_price(["AAPL"])

    assert len(result) == 1
    assert isinstance(result[0], StockPriceCreate)
    assert result[0].close_price == 150.0


async def test_fetch_multiple_tickers_returns_all():
    collector = StockDataCollector()

    with patch("collectors.stock_api.yf.download", return_value=make_multi_df(["AAPL", "MSFT"])):
        result = await collector.fetch_stock_price(["AAPL", "MSFT"])

    assert len(result) == 2
    assert {item.ticker for item in result} == {"AAPL", "MSFT"}


async def test_fetch_str_input_normalized_to_list():
    collector = StockDataCollector()

    with patch("collectors.stock_api.yf.download", return_value=make_flat_df()) as mock_dl:
        await collector.fetch_stock_price("AAPL")

    assert mock_dl.call_args.kwargs["tickers"] == "AAPL"


async def test_fetch_empty_dataframe_returns_empty():
    collector = StockDataCollector()

    with patch("collectors.stock_api.yf.download", return_value=pd.DataFrame()):
        result = await collector.fetch_stock_price(["AAPL"])

    assert result == []


async def test_fetch_download_raises_returns_empty():
    collector = StockDataCollector()

    with patch("collectors.stock_api.yf.download", side_effect=RuntimeError("network")):
        result = await collector.fetch_stock_price(["AAPL"])

    assert result == []


async def test_fetch_skips_nan_rows():
    collector = StockDataCollector()
    df = pd.DataFrame(
        {
            "Close": [float("nan"), 150.0],
            "Open": [149.0, 149.0],
            "High": [151.0, 151.0],
            "Low": [148.0, 148.0],
            "Volume": [1_000_000, 1_000_000],
        },
        index=pd.to_datetime(["2024-01-01", "2024-01-02"]),
    )

    with patch("collectors.stock_api.yf.download", return_value=df):
        result = await collector.fetch_stock_price(["AAPL"])

    assert len(result) == 1
    assert result[0].trade_date == pd.Timestamp("2024-01-02")


async def test_fetch_missing_column_skips_ticker():
    collector = StockDataCollector()
    df = make_multi_df(["AAPL"]).drop(columns=[("AAPL", "Volume")])

    with patch("collectors.stock_api.yf.download", return_value=df):
        result = await collector.fetch_stock_price(["AAPL"])

    assert result == []


def test_get_market_leaders_all_sectors():
    collector = StockDataCollector()
    mock_sector = MagicMock()
    mock_sector.top_companies.head.return_value.index.to_list.return_value = ["AAPL", "MSFT", "GOOGL"]

    with patch("collectors.stock_api.yf.Sector", return_value=mock_sector):
        result = collector.get_market_leaders()

    assert len(result) == 4
    assert all(value == ["AAPL", "MSFT", "GOOGL"] for value in result.values())


def test_get_market_leaders_one_sector_raises():
    collector = StockDataCollector()
    mock_sector = MagicMock()
    mock_sector.top_companies.head.return_value.index.to_list.return_value = ["A", "B", "C"]
    mock_sector_cls = MagicMock(side_effect=[Exception("fail"), mock_sector, mock_sector, mock_sector])

    with patch("collectors.stock_api.yf.Sector", mock_sector_cls):
        result = collector.get_market_leaders()

    assert len(result) == 3
