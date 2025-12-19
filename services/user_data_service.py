from db.repositories.user_repository import UserRepository
import logging
from schemas.user import UserDTO, SubscriptionDTO
from typing import List


class UserDataService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.logger = logging.getLogger(__name__)

    async def get_user(self, provider: str, provider_id: str) -> UserDTO | None:
        try:
            user = await self.user_repository.get_user(provider, provider_id)
            if user:
                return user
            else:
                self.logger.warning(
                    f"User not found for provider: {provider} and provider_id: {provider_id}")
                return None
        except Exception as e:
            self.logger.error(
                f"Database error while fetching user (provider: {provider}, provider_id: {provider_id}): {e}", exc_info=True)
            return None

    async def register_user(self, provider: str, provider_id: str) -> bool:
        result = await self.user_repository.register_user(provider, provider_id)
        if result is None:
            self.logger.error(
                f"Failed to register user for provider: {provider} and provider_id: {provider_id}: database error")
            return False
        elif result == 0:
            self.logger.warning(
                f"User already exists for provider: {provider} and provider_id: {provider_id}")
            return True  # User already exists is not an error
        else:
            self.logger.info(
                f"User registered for provider: {provider} and provider_id: {provider_id} ({result} row affected)")
            return True

    async def get_authorized_user(self, provider: str, provider_id: str) -> UserDTO | None:
        try:
            user = await self.user_repository.get_authorized_user(provider, provider_id)
            if user:
                return user
            else:
                self.logger.warning(
                    f"Authorized user not found for provider: {provider} and provider_id: {provider_id}")
                return None
        except Exception as e:
            self.logger.error(
                f"Database error while fetching authorized user (provider: {provider}, provider_id: {provider_id}): {e}", exc_info=True)
            return None

    async def add_subscription(self, provider_id: str, chat_id: str, ticker: str) -> bool:
        result = await self.user_repository.add_subscription(provider_id, chat_id, ticker)
        if result:
            self.logger.info(
                f"Subscription added for provider_id: {provider_id}, chat_id: {chat_id}, ticker: {ticker}")
            return True
        else:
            self.logger.error(
                f"Failed to add subscription for provider_id: {provider_id}, chat_id: {chat_id}, ticker: {ticker}")
            return False

    async def remove_subscription(self, provider_id: str, ticker: str) -> bool:
        result = await self.user_repository.remove_subscription(provider_id, ticker)
        if result:
            self.logger.info(
                f"Subscription removed for provider_id: {provider_id}, ticker: {ticker}")
            return True
        else:
            self.logger.error(
                f"Failed to remove subscription for provider_id: {provider_id}, ticker: {ticker}")
            return False

    async def get_subscriptions_with_ticker(self, ticker: str) -> List[SubscriptionDTO]:
        self.logger.info(f"Getting subscriptions with ticker: {ticker}")
        return await self.user_repository.get_subscriptions_with_ticker(ticker)

    async def get_unique_subscriptions_tickers(self) -> List[str]:
        self.logger.info("Getting unique subscriptions tickers")
        return await self.user_repository.get_unique_subscriptions_tickers()
