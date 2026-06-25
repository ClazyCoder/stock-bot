import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.llm_service import LLMService


@pytest.fixture
def svc():
    llm = MagicMock()
    llm.generate_report_with_ticker = AsyncMock(return_value="Generated Report")
    repo = MagicMock()
    repo.get_stock_report_with_date = AsyncMock()
    repo.insert_stock_report = AsyncMock(return_value=1)
    return LLMService(llm_module=llm, report_repository=repo), llm, repo


async def test_generate_uses_cached_report(svc):
    service, llm, repo = svc
    repo.get_stock_report_with_date.return_value = MagicMock(report="Cached")

    result = await service.generate_report_with_ticker("AAPL")

    assert result == "Cached"
    llm.generate_report_with_ticker.assert_not_called()


async def test_generate_creates_new_when_no_cache(svc):
    service, llm, repo = svc
    repo.get_stock_report_with_date.return_value = None

    result = await service.generate_report_with_ticker("AAPL")

    assert result == "Generated Report"
    llm.generate_report_with_ticker.assert_called_once_with("AAPL")
    repo.insert_stock_report.assert_called_once()


async def test_force_generate_skips_cache(svc):
    service, llm, repo = svc
    repo.get_stock_report_with_date.return_value = MagicMock(report="Cached")

    result = await service.generate_report_with_ticker("AAPL", force_generate=True)

    assert result == "Generated Report"
    llm.generate_report_with_ticker.assert_called_once_with("AAPL")


async def test_db_save_failure_still_returns_report(svc):
    service, _, repo = svc
    repo.get_stock_report_with_date.return_value = None
    repo.insert_stock_report.return_value = None

    result = await service.generate_report_with_ticker("AAPL")

    assert result == "Generated Report"


async def test_concurrent_same_ticker_generates_once(svc):
    service, llm, repo = svc
    calls = {"count": 0}

    async def get_report(*_args, **_kwargs):
        calls["count"] += 1
        if calls["count"] <= 2:
            return None
        return MagicMock(report="Generated Report")

    async def generate_report(_ticker):
        await asyncio.sleep(0.01)
        return "Generated Report"

    repo.get_stock_report_with_date.side_effect = get_report
    llm.generate_report_with_ticker = AsyncMock(side_effect=generate_report)

    result1, result2 = await asyncio.gather(
        service.generate_report_with_ticker("AAPL"),
        service.generate_report_with_ticker("AAPL"),
    )

    assert result1 == "Generated Report"
    assert result2 == "Generated Report"
    assert llm.generate_report_with_ticker.call_count == 1


async def test_get_today_report_found(svc):
    service, _, repo = svc
    repo.get_stock_report_with_date.return_value = MagicMock(report="Today's Report")

    result = await service.get_today_stock_report("AAPL")

    assert result == "Today's Report"


async def test_get_today_report_not_found(svc):
    service, _, repo = svc
    repo.get_stock_report_with_date.return_value = None

    result = await service.get_today_stock_report("AAPL")

    assert result is None
