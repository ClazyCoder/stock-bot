from db.repositories.base import BaseRepository
from db.models import User, Subscription
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from schemas.user import UserDTO, SubscriptionDTO
from typing import List


class UserRepository(BaseRepository):
    async def get_user(self, provider: str, provider_id: str) -> UserDTO | None:
        async with self._get_session() as session:
            stmt = select(User).where(User.provider == provider,
                                      User.provider_id == provider_id).options(selectinload(User.subscriptions))
            result = await session.execute(stmt)
            orm_result = result.scalar_one_or_none()

            if orm_result:
                return UserDTO.model_validate(orm_result)
            else:
                self.logger.error(
                    f"User not found for provider: {provider} and provider_id: {provider_id}")
                return None

    async def register_user(self, provider: str, provider_id: str):
        async with self._get_session() as session:
            try:
                user = User(provider=provider, provider_id=provider_id,
                            is_authorized=True)
                session.add(user)
                await session.commit()
                return True
            except Exception as e:
                self.logger.error(
                    f"Failed to register user (provider: {provider}, provider_id: {provider_id}): {e}")
                await session.rollback()
                return False

    async def get_authorized_user(self, provider: str, provider_id: str) -> UserDTO | None:
        async with self._get_session() as session:
            stmt = select(User).where(User.provider == provider,
                                      User.provider_id == provider_id,
                                      User.is_authorized == True
                                      ).options(selectinload(User.subscriptions))
            result = await session.execute(stmt)
            orm_result = result.scalar_one_or_none()
            if orm_result:
                return UserDTO.model_validate(orm_result)
            else:
                self.logger.warning(
                    f"Authorized user not found for provider: {provider} and provider_id: {provider_id}")
                return None

    async def remove_user(self, provider: str, provider_id: str) -> bool:
        async with self._get_session() as session:
            stmt = select(User).where(User.provider == provider,
                                      User.provider_id == provider_id)
            result = await session.execute(stmt)
            orm_result = result.scalar_one_or_none()
            if orm_result:
                await session.delete(orm_result)
                await session.commit()
                return True
            else:
                self.logger.error(
                    f"User not found for provider: {provider} and provider_id: {provider_id}")
                return False

    async def add_subscription(self, provider_id: str, chat_id: str, ticker: str) -> bool:
        async with self._get_session() as session:
            try:
                user = await self.get_authorized_user(provider="telegram", provider_id=provider_id)
                if not user:
                    self.logger.error(
                        f"User not found for provider: telegram and provider_id: {provider_id}")
                    return False
                subscription = Subscription(
                    user_id=user.id, chat_id=chat_id, ticker=ticker)
                session.add(subscription)
                await session.commit()
                return True
            except IntegrityError as e:
                self.logger.warning(
                    f"Subscription already exists (user_id: {provider_id}, chat_id: {chat_id}, ticker: {ticker}): {e}")
                await session.rollback()
                return False
            except Exception as e:
                self.logger.error(
                    f"Failed to add subscription (user_id: {provider_id}, chat_id: {chat_id}, ticker: {ticker}): {e}")
                await session.rollback()
                return False

    async def remove_subscription(self, provider_id: str, chat_id: str, ticker: str) -> bool:
        async with self._get_session() as session:
            try:
                user = await self.get_authorized_user(provider="telegram", provider_id=provider_id)
                if not user:
                    self.logger.error(
                        f"User not found for provider: telegram and provider_id: {provider_id}")
                    return False
                stmt = select(Subscription).where(
                    Subscription.user_id == user.id, Subscription.chat_id == chat_id, Subscription.ticker == ticker)
                result = await session.execute(stmt)
                orm_result = result.scalar_one_or_none()
                if orm_result:
                    await session.delete(orm_result)
                    await session.commit()
                    return True
                else:
                    self.logger.warning(
                        f"Subscription not found (user_id: {provider_id}, chat_id: {chat_id}, ticker: {ticker})")
                    return False
            except Exception as e:
                self.logger.error(
                    f"Failed to remove subscription (user_id: {provider_id}, chat_id: {chat_id}, ticker: {ticker}): {e}")
                await session.rollback()
                return False

    async def get_subscriptions_with_ticker(self, ticker: str) -> List[SubscriptionDTO]:
        async with self._get_session() as session:
            stmt = select(Subscription).join(User).where(
                Subscription.ticker == ticker, User.is_authorized == True)
            result = await session.execute(stmt)
            orm_results = result.scalars().all()
            return [SubscriptionDTO.model_validate(subscription) for subscription in orm_results]

    async def get_subscriptions_with_user_id(self, provider_id: str) -> List[SubscriptionDTO]:
        async with self._get_session() as session:
            user = await self.get_user(provider="telegram", provider_id=provider_id)
            if not user:
                self.logger.error(
                    f"User not found for provider: telegram and provider_id: {provider_id}")
                return []
            stmt = select(Subscription).join(User).where(
                Subscription.user_id == user.id, User.is_authorized == True)
            result = await session.execute(stmt)
            orm_results = result.scalars().all()
            return [SubscriptionDTO.model_validate(subscription) for subscription in orm_results]

    async def get_unique_subscriptions_tickers(self) -> List[str]:
        async with self._get_session() as session:
            stmt = select(Subscription.ticker).distinct()
            result = await session.execute(stmt)
            orm_results = result.scalars().all()
            return list(orm_results)
