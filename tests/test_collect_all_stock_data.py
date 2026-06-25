from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jobs.stock_collector import collect_all_stock_data


@pytest.fixture
def services():
    stock_svc = MagicMock()
    stock_svc.collect_and_save = AsyncMock(return_value=True)
    stock_svc.collect_and_save_stock_news = AsyncMock(return_value=True)

    user_svc = MagicMock()
    user_svc.get_unique_subscriptions_tickers = AsyncMock(
        return_value=["AAPL", "MSFT", "TSLA"]
    )

    llm_svc = MagicMock()
    llm_svc.generate_report_with_ticker = AsyncMock()

    telegram = MagicMock()
    telegram.send_subscriptions = AsyncMock()

    return stock_svc, user_svc, llm_svc, telegram


async def test_no_tickers_returns_early(services):
    stock_svc, user_svc, llm_svc, telegram = services
    user_svc.get_unique_subscriptions_tickers = AsyncMock(return_value=[])

    with patch("jobs.stock_collector.get_stock_service", return_value=stock_svc), \
        patch("jobs.stock_collector.get_user_data_service", return_value=user_svc), \
        patch(
            "jobs.stock_collector.get_llm_service",
            new_callable=AsyncMock,
            return_value=llm_svc,
        ), \
        patch("jobs.stock_collector.asyncio.sleep", new_callable=AsyncMock):
        await collect_all_stock_data(telegram)

    stock_svc.collect_and_save.assert_not_called()


async def test_stock_data_collected_for_all_tickers(services):
    stock_svc, user_svc, llm_svc, telegram = services

    with patch("jobs.stock_collector.get_stock_service", return_value=stock_svc), \
        patch("jobs.stock_collector.get_user_data_service", return_value=user_svc), \
        patch(
            "jobs.stock_collector.get_llm_service",
            new_callable=AsyncMock,
            return_value=llm_svc,
        ), \
        patch("jobs.stock_collector.asyncio.sleep", new_callable=AsyncMock):
        await collect_all_stock_data(telegram)

    assert stock_svc.collect_and_save.call_count == 1


async def test_invalid_batch_size_env_defaults_to_5(monkeypatch, services):
    stock_svc, user_svc, llm_svc, telegram = services
    monkeypatch.setenv("STOCK_DATA_BATCH_SIZE", "xyz")
    user_svc.get_unique_subscriptions_tickers = AsyncMock(return_value=list("ABCDEFGHIJ"))

    with patch("jobs.stock_collector.get_stock_service", return_value=stock_svc), \
        patch("jobs.stock_collector.get_user_data_service", return_value=user_svc), \
        patch(
            "jobs.stock_collector.get_llm_service",
            new_callable=AsyncMock,
            return_value=llm_svc,
        ), \
        patch("jobs.stock_collector.asyncio.sleep", new_callable=AsyncMock):
        await collect_all_stock_data(telegram)

    assert stock_svc.collect_and_save.call_count == 2


async def test_stock_data_failure_does_not_halt_pipeline(services):
    stock_svc, user_svc, llm_svc, telegram = services
    stock_svc.collect_and_save.side_effect = RuntimeError("fail")

    with patch("jobs.stock_collector.get_stock_service", return_value=stock_svc), \
        patch("jobs.stock_collector.get_user_data_service", return_value=user_svc), \
        patch(
            "jobs.stock_collector.get_llm_service",
            new_callable=AsyncMock,
            return_value=llm_svc,
        ), \
        patch("jobs.stock_collector.asyncio.sleep", new_callable=AsyncMock):
        await collect_all_stock_data(telegram)

    stock_svc.collect_and_save_stock_news.assert_called()


async def test_news_failure_does_not_halt_pipeline(services):
    stock_svc, user_svc, llm_svc, telegram = services
    stock_svc.collect_and_save_stock_news.side_effect = RuntimeError("fail")

    with patch("jobs.stock_collector.get_stock_service", return_value=stock_svc), \
        patch("jobs.stock_collector.get_user_data_service", return_value=user_svc), \
        patch(
            "jobs.stock_collector.get_llm_service",
            new_callable=AsyncMock,
            return_value=llm_svc,
        ), \
        patch("jobs.stock_collector.asyncio.sleep", new_callable=AsyncMock):
        await collect_all_stock_data(telegram)

    llm_svc.generate_report_with_ticker.assert_called()


async def test_reports_generated_for_each_ticker(services):
    stock_svc, user_svc, llm_svc, telegram = services

    with patch("jobs.stock_collector.get_stock_service", return_value=stock_svc), \
        patch("jobs.stock_collector.get_user_data_service", return_value=user_svc), \
        patch(
            "jobs.stock_collector.get_llm_service",
            new_callable=AsyncMock,
            return_value=llm_svc,
        ), \
        patch("jobs.stock_collector.asyncio.sleep", new_callable=AsyncMock):
        await collect_all_stock_data(telegram)

    assert llm_svc.generate_report_with_ticker.call_count == 3
    assert [call.args[0] for call in llm_svc.generate_report_with_ticker.call_args_list] == [
        "AAPL",
        "MSFT",
        "TSLA",
    ]


async def test_telegram_send_called_per_ticker(services):
    stock_svc, user_svc, llm_svc, telegram = services

    with patch("jobs.stock_collector.get_stock_service", return_value=stock_svc), \
        patch("jobs.stock_collector.get_user_data_service", return_value=user_svc), \
        patch(
            "jobs.stock_collector.get_llm_service",
            new_callable=AsyncMock,
            return_value=llm_svc,
        ), \
        patch("jobs.stock_collector.asyncio.sleep", new_callable=AsyncMock):
        await collect_all_stock_data(telegram)

    assert telegram.send_subscriptions.call_count == 3
    assert [call.args[0] for call in telegram.send_subscriptions.call_args_list] == [
        "AAPL",
        "MSFT",
        "TSLA",
    ]


async def test_sleep_between_batches_not_after_last(monkeypatch, services):
    stock_svc, user_svc, llm_svc, telegram = services
    user_svc.get_unique_subscriptions_tickers = AsyncMock(
        return_value=["AAPL", "MSFT", "TSLA", "NVDA", "META", "AMZN"]
    )
    monkeypatch.setenv("STOCK_DATA_BATCH_SIZE", "3")
    monkeypatch.setenv("STOCK_NEWS_BATCH_SIZE", "3")
    sleep_mock = AsyncMock()

    with patch("jobs.stock_collector.get_stock_service", return_value=stock_svc), \
        patch("jobs.stock_collector.get_user_data_service", return_value=user_svc), \
        patch(
            "jobs.stock_collector.get_llm_service",
            new_callable=AsyncMock,
            return_value=llm_svc,
        ), \
        patch("jobs.stock_collector.asyncio.sleep", new=sleep_mock):
        await collect_all_stock_data(telegram)

    assert sleep_mock.call_count == 2
