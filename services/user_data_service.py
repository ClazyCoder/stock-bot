from db.repositories.user_repository import UserRepository
import logging
from schemas.user import UserDTO, SubscriptionDTO
from typing import List


class UserDataService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.logger = logging.getLogger(__name__)

    async def get_user(self, provider: str, provider_id: str) -> UserDTO | None:
        user = await self.user_repository.get_user(provider, provider_id)
        if user:
            return user
        else:
            self.logger.error(
                f"User not found for provider: {provider} and provider_id: {provider_id}")
            return None

    async def register_user(self, provider: str, provider_id: str) -> bool:
        result = await self.user_repository.register_user(provider, provider_id)
        if result:
            self.logger.info(
                f"User registered for provider: {provider} and provider_id: {provider_id}")
            return True
        else:
            self.logger.error(
                f"Failed to register user for provider: {provider} and provider_id: {provider_id}")
            return False

    async def get_authorized_user(self, provider: str, provider_id: str) -> UserDTO | None:
        user = await self.user_repository.get_authorized_user(provider, provider_id)
        if user:
            return user
        else:
            self.logger.error(
                f"Authorized user not found for provider: {provider} and provider_id: {provider_id}")
            return None

    async def add_subscription(self, user_id: int, chat_id: int, ticker: str) -> bool:
        result = await self.user_repository.add_subscription(user_id, chat_id, ticker)
        if result:
            self.logger.info(
                f"Subscription added for user_id: {user_id}, chat_id: {chat_id}, ticker: {ticker}")
            return True
        else:
            self.logger.error(
                f"Failed to add subscription for user_id: {user_id}, chat_id: {chat_id}, ticker: {ticker}")
            return False

    async def remove_subscription(self, user_id: int, chat_id: int, ticker: str) -> bool:
        result = await self.user_repository.remove_subscription(user_id, chat_id, ticker)
        if result:
            self.logger.info(
                f"Subscription removed for user_id: {user_id}, chat_id: {chat_id}, ticker: {ticker}")
            return True
        else:
            self.logger.error(
                f"Failed to remove subscription for user_id: {user_id}, chat_id: {chat_id}, ticker: {ticker}")
            return False

    async def get_subscriptions_with_ticker(self, ticker: str) -> List[SubscriptionDTO]:
        self.logger.info(f"Getting subscriptions with ticker: {ticker}")
        return await self.user_repository.get_subscriptions_with_ticker(ticker)

    async def get_unique_subscriptions_tickers(self) -> List[str]:
        self.logger.info("Getting unique subscriptions tickers")
        return await self.user_repository.get_unique_subscriptions_tickers()
