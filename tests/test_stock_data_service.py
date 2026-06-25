from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from schemas.stock import StockPriceCreate
from services.stock_data_service import StockDataService


@pytest.fixture
def svc():
    collector = MagicMock()
    repo = MagicMock()
    news = MagicMock()
    collector.fetch_stock_price = AsyncMock()
    collector.fetch_stock_info = AsyncMock()
    repo.insert_stock_data = AsyncMock()
    repo.get_stock_data = AsyncMock()
    repo.insert_multiple_stock_news = AsyncMock()
    repo.get_stock_news = AsyncMock()
    news.fetch_news = AsyncMock()
    return StockDataService(collector=collector, stock_repository=repo, news_collector=news), collector, repo, news


def make_stock_price() -> StockPriceCreate:
    return StockPriceCreate(
        ticker="AAPL",
        close_price=150,
        open_price=149,
        high_price=151,
        low_price=148,
        volume=1000,
        trade_date=datetime.now(),
    )


async def test_collect_and_save_success(svc):
    service, collector, repo, _ = svc
    collector.fetch_stock_price.return_value = [make_stock_price()]
    repo.insert_stock_data.return_value = 1

    result = await service.collect_and_save("AAPL")

    assert result is True


async def test_collect_and_save_empty_data(svc):
    service, collector, repo, _ = svc
    collector.fetch_stock_price.return_value = []

    result = await service.collect_and_save("AAPL")

    assert result is False
    repo.insert_stock_data.assert_not_called()


async def test_collect_and_save_repo_returns_none(svc):
    service, collector, repo, _ = svc
    collector.fetch_stock_price.return_value = [make_stock_price()]
    repo.insert_stock_data.return_value = None

    result = await service.collect_and_save("AAPL")

    assert result is False


async def test_collect_and_save_repo_returns_zero(svc):
    service, collector, repo, _ = svc
    collector.fetch_stock_price.return_value = [make_stock_price()]
    repo.insert_stock_data.return_value = 0

    result = await service.collect_and_save("AAPL")

    assert result is True


async def test_get_stock_data_returns_records(svc):
    service, _, repo, _ = svc
    records = [MagicMock()]
    repo.get_stock_data.return_value = records

    result = await service.get_stock_data("AAPL")

    assert result == records


async def test_get_stock_data_none(svc):
    service, _, repo, _ = svc
    repo.get_stock_data.return_value = None

    result = await service.get_stock_data("AAPL")

    assert result is None


async def test_get_stock_data_exception(svc):
    service, _, repo, _ = svc
    repo.get_stock_data.side_effect = Exception("db")

    result = await service.get_stock_data("AAPL")

    assert result is None


async def test_collect_news_success(svc):
    service, _, repo, news = svc
    news.fetch_news.return_value = [(MagicMock(), [MagicMock()])]
    repo.insert_multiple_stock_news.return_value = 3

    result = await service.collect_and_save_stock_news("AAPL")

    assert result is True


async def test_collect_news_empty(svc):
    service, _, repo, news = svc
    news.fetch_news.return_value = []

    result = await service.collect_and_save_stock_news("AAPL")

    assert result is False
    repo.insert_multiple_stock_news.assert_not_called()


async def test_collect_news_repo_error(svc):
    service, _, repo, news = svc
    news.fetch_news.return_value = [(MagicMock(), [MagicMock()])]
    repo.insert_multiple_stock_news.return_value = None

    result = await service.collect_and_save_stock_news("AAPL")

    assert result is False


async def test_get_raw_stock_info_success(svc):
    service, collector, _, _ = svc
    collector.fetch_stock_info.return_value = {"symbol": "AAPL"}

    result = await service.get_raw_stock_info("AAPL")

    assert result == {"symbol": "AAPL"}


async def test_get_raw_stock_info_exception(svc):
    service, collector, _, _ = svc
    collector.fetch_stock_info.side_effect = Exception("boom")

    result = await service.get_raw_stock_info("AAPL")

    assert result is None
