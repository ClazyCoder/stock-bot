from unittest.mock import AsyncMock, MagicMock

import pytest

from services.user_data_service import UserDataService


@pytest.fixture
def svc():
    repo = MagicMock()
    repo.get_user = AsyncMock()
    repo.register_user = AsyncMock()
    repo.get_authorized_user = AsyncMock()
    repo.add_subscription = AsyncMock()
    repo.remove_subscription = AsyncMock()
    repo.get_subscriptions_with_ticker = AsyncMock()
    repo.get_unique_subscriptions_tickers = AsyncMock()
    return UserDataService(user_repository=repo), repo


async def test_get_user_found(svc):
    service, repo = svc
    user = MagicMock()
    repo.get_user.return_value = user

    result = await service.get_user("telegram", "1")

    assert result is user


async def test_get_user_not_found(svc):
    service, repo = svc
    repo.get_user.return_value = None

    result = await service.get_user("telegram", "1")

    assert result is None


async def test_get_user_exception(svc):
    service, repo = svc
    repo.get_user.side_effect = Exception("db")

    result = await service.get_user("telegram", "1")

    assert result is None


async def test_register_user_new(svc):
    service, repo = svc
    repo.register_user.return_value = 1

    result = await service.register_user("telegram", "1")

    assert result is True


async def test_register_user_already_exists(svc):
    service, repo = svc
    repo.register_user.return_value = 0

    result = await service.register_user("telegram", "1")

    assert result is True


async def test_register_user_db_error(svc):
    service, repo = svc
    repo.register_user.return_value = None

    result = await service.register_user("telegram", "1")

    assert result is False


async def test_add_subscription_success(svc):
    service, repo = svc
    repo.add_subscription.return_value = True

    result = await service.add_subscription("1", "chat", "AAPL")

    assert result is True


async def test_remove_subscription_success(svc):
    service, repo = svc
    repo.remove_subscription.return_value = True

    result = await service.remove_subscription("1", "AAPL")

    assert result is True


async def test_get_unique_tickers_delegates(svc):
    service, repo = svc
    repo.get_unique_subscriptions_tickers.return_value = ["AAPL", "MSFT"]

    result = await service.get_unique_subscriptions_tickers()

    assert result == ["AAPL", "MSFT"]
