"""Offline integration checks for the yfinance/curl_cffi dependency boundary."""
import json

import pytest
import yfinance as yf
from curl_cffi import Curl, requests
from yfinance.data import YfData


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def reject(*args, **kwargs):
        raise AssertionError("Unexpected network access in compatibility test")
    monkeypatch.setattr(Curl, "perform", reject)
    monkeypatch.setattr(requests.Session, "request", reject)


def response(payload):
    class Response:
        text = json.dumps(payload)
        def json(self):
            return payload
    return Response()


def test_default_and_explicit_curl_sessions_are_accepted():
    ticker = yf.Ticker("AAPL")
    assert ticker.ticker == "AAPL"
    previous = YfData()._session
    with requests.Session() as session:
        assert getattr(session, "cache", None) is None
        assert YfData(session=session)._session is session
        assert yf.Ticker("MSFT", session=session).session is session
    YfData(session=previous)
    ticker.session.close()


async def test_collector_info_uses_real_yfinance_parser(monkeypatch):
    from collectors.stock_api import StockDataCollector
    payload = {"quoteSummary": {"result": [{"price": {"shortName": "Example", "regularMarketPrice": {"raw": 150.0, "fmt": "150.00"}}}]}}
    monkeypatch.setattr(YfData, "get_raw_json", lambda *a, **kw: payload)
    monkeypatch.setattr(YfData, "cache_get", lambda *a, **kw: response({"timeseries": {"result": []}}))
    info = await StockDataCollector().fetch_stock_info("AAPL")
    assert info["symbol"] == "AAPL"
    assert info["regularMarketPrice"] == 150.0
    assert info["shortName"] == "Example"


def test_search_preserves_news_and_quotes(monkeypatch):
    news = [{"title": "Example news", "link": "https://example.invalid/news"}]
    monkeypatch.setattr(YfData, "cache_get", lambda *a, **kw: response({"quotes": [{"symbol": "AAPL"}], "news": news}))
    search = yf.Search("AAPL").search()
    assert search.news == news
    assert search.quotes == [{"symbol": "AAPL"}]


def test_ticker_history_parses_normal_chart(monkeypatch):
    payload = {"chart": {"error": None, "result": [{
        "meta": {"currency": "USD", "symbol": "AAPL", "exchangeName": "NMS", "instrumentType": "EQUITY", "firstTradeDate": 345479400, "regularMarketTime": 1704205800, "gmtoffset": -18000, "timezone": "EST", "exchangeTimezoneName": "America/New_York", "regularMarketPrice": 150.0, "priceHint": 2, "dataGranularity": "1d", "range": "1d", "validRanges": ["1d", "5d", "1mo"]},
        "timestamp": [1704205800],
        "indicators": {"quote": [{"open": [149.0], "high": [152.0], "low": [148.0], "close": [150.0], "volume": [1000]}], "adjclose": [{"adjclose": [150.0]}]}
    }]}}
    monkeypatch.setattr(YfData, "get", lambda *a, **kw: response(payload))
    monkeypatch.setattr(YfData, "cache_get", lambda *a, **kw: response(payload))
    ticker = yf.Ticker("AAPL")
    ticker._tz = "America/New_York"
    frame = ticker.history(period="1d", auto_adjust=False, raise_errors=True)
    assert len(frame) == 1
    assert frame["Close"].iloc[0] == 150.0
    assert frame["Volume"].iloc[0] == 1000
