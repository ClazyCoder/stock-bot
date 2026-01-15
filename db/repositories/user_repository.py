from db.repositories.base import BaseRepository
from db.models import User, Subscription
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.user import UserDTO, SubscriptionDTO
from typing import List


class UserRepository(BaseRepository):
    # Internal methods: accept session as parameter for reuse within transactions
    async def _get_user_in_session(
        self,
        session: AsyncSession,
        provider: str,
        provider_id: str
    ) -> User | None:
        """Get user within an existing session (internal method for reuse)."""
        stmt = select(User).where(
            User.provider == provider,
            User.provider_id == provider_id
        ).options(selectinload(User.subscriptions))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_authorized_user_in_session(
        self,
        session: AsyncSession,
        provider: str,
        provider_id: str
    ) -> User | None:
        """Get authorized user within an existing session (internal method for reuse)."""
        stmt = select(User).where(
            User.provider == provider,
            User.provider_id == provider_id,
            User.is_authorized == True
        ).options(selectinload(User.subscriptions))
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    # Public methods: create their own sessions and use internal methods
    async def get_user(self, provider: str, provider_id: str) -> UserDTO | None:
        async with self._get_session() as session:
            orm_result = await self._get_user_in_session(session, provider, provider_id)
            if orm_result:
                self.logger.info(
                    f"User found: provider={provider}, provider_id={provider_id}")
                return UserDTO.model_validate(orm_result)
            else:
                self.logger.warning(
                    f"User not found for provider: {provider} and provider_id: {provider_id}")
                return None

    async def register_user(self, provider: str, provider_id: str) -> int | None:
        """
        Register a new user in the database.
        Args:
            provider: str - The provider name (e.g., 'telegram').
            provider_id: str - The provider-specific user ID.
        Returns:
            int | None: The number of affected rows (1 if successful, 0 if user already exists), None on error.
        """
        async with self._get_session() as session:
            try:
                user = User(provider=provider, provider_id=provider_id,
                            is_authorized=True)
                session.add(user)
                await session.commit()
                affected_rows = 1  # One user was inserted
                self.logger.info(
                    f"Successfully registered user: provider={provider}, provider_id={provider_id} ({affected_rows} row affected)")
                return affected_rows
            except IntegrityError as e:
                # User already exists (unique constraint violation)
                await session.rollback()
                self.logger.warning(
                    f"User already exists (provider: {provider}, provider_id: {provider_id}): {e}")
                return 0
            except Exception as e:
                self.logger.error(
                    f"Failed to register user (provider: {provider}, provider_id: {provider_id}): {e}", exc_info=True)
                await session.rollback()
                return None

    async def get_authorized_user(self, provider: str, provider_id: str) -> UserDTO | None:
        try:
            async with self._get_session() as session:
                orm_result = await self._get_authorized_user_in_session(session, provider, provider_id)
                if orm_result:
                    self.logger.info(
                        f"Authorized user found: provider={provider}, provider_id={provider_id}")
                    return UserDTO.model_validate(orm_result)
                else:
                    self.logger.warning(
                        f"Authorized user not found for provider: {provider} and provider_id: {provider_id}")
                    return None
        except Exception as e:
            self.logger.error(
                f"Failed to get authorized user (provider: {provider}, provider_id: {provider_id}): {e}", exc_info=True)
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
                self.logger.info(
                    f"Successfully removed user: provider={provider}, provider_id={provider_id}")
                return True
            else:
                self.logger.warning(
                    f"User not found for removal: provider={provider}, provider_id={provider_id}")
                return False

    async def add_subscription(self, provider_id: str, chat_id: str, ticker: str) -> bool:
        async with self._get_session() as session:
            try:
                # Query user within the same transaction to ensure consistency
                user_orm = await self._get_authorized_user_in_session(
                    session, "telegram", provider_id
                )
                if not user_orm:
                    self.logger.warning(
                        f"User not found for provider: telegram and provider_id: {provider_id}")
                    return False

                subscription = Subscription(
                    user_id=user_orm.id, chat_id=chat_id, ticker=ticker)
                session.add(subscription)
                await session.commit()
                self.logger.info(
                    f"Successfully added subscription: provider_id={provider_id}, chat_id={chat_id}, ticker={ticker}")
                return True
            except IntegrityError as e:
                self.logger.warning(
                    f"Subscription already exists (provider_id: {provider_id}, chat_id: {chat_id}, ticker: {ticker}): {e}")
                await session.rollback()
                return False
            except Exception as e:
                self.logger.error(
                    f"Failed to add subscription (provider_id: {provider_id}, chat_id: {chat_id}, ticker: {ticker}): {e}", exc_info=True)
                await session.rollback()
                return False

    async def remove_subscription(self, provider_id: str, ticker: str) -> bool:
        async with self._get_session() as session:
            try:
                # Query user within the same transaction to ensure consistency
                user_orm = await self._get_authorized_user_in_session(
                    session, "telegram", provider_id
                )
                if not user_orm:
                    self.logger.warning(
                        f"User not found for provider: telegram and provider_id: {provider_id}")
                    return False
                # Use SELECT FOR UPDATE to lock rows and prevent race conditions
                stmt = select(Subscription).where(
                    Subscription.user_id == user_orm.id, Subscription.ticker == ticker).with_for_update()
                result = await session.execute(stmt)
                orm_results = result.scalars().all()
                if orm_results:
                    count_before = len(orm_results)
                    for subscription in orm_results:
                        await session.delete(subscription)
                    await session.commit()
                    # Log actual count that was removed (count_before may differ if concurrent requests occurred)
                    self.logger.info(
                        f"Successfully removed {count_before} subscription(s): provider_id={provider_id}, ticker={ticker}")
                    return True
                else:
                    self.logger.warning(
                        f"Subscription not found (provider_id: {provider_id}, ticker: {ticker})")
                    return False
            except Exception as e:
                self.logger.error(
                    f"Failed to remove subscription (provider_id: {provider_id}, ticker: {ticker}): {e}", exc_info=True)
                await session.rollback()
                return False

    async def get_subscriptions_with_ticker(self, ticker: str) -> List[SubscriptionDTO]:
        async with self._get_session() as session:
            stmt = select(Subscription).join(User).where(
                Subscription.ticker == ticker, User.is_authorized.is_(True))
            result = await session.execute(stmt)
            orm_results = result.scalars().all()
            subscriptions = [SubscriptionDTO.model_validate(
                subscription) for subscription in orm_results]
            self.logger.info(
                f"Found {len(subscriptions)} subscriptions for ticker: {ticker}")
            return subscriptions

    async def get_subscriptions_with_user_id(self, provider_id: str) -> List[SubscriptionDTO]:
        async with self._get_session() as session:
            # Query user within the same transaction to ensure consistency
            user_orm = await self._get_user_in_session(session, "telegram", provider_id)
            if not user_orm:
                self.logger.warning(
                    f"User not found for provider: telegram and provider_id: {provider_id}")
                return []
            stmt = select(Subscription).join(User).where(
                Subscription.user_id == user_orm.id, User.is_authorized == True)
            result = await session.execute(stmt)
            orm_results = result.scalars().all()
            subscriptions = [SubscriptionDTO.model_validate(
                subscription) for subscription in orm_results]
            self.logger.info(
                f"Found {len(subscriptions)} subscriptions for user: provider_id={provider_id}")
            return subscriptions

    async def get_unique_subscriptions_tickers(self) -> List[str]:
        async with self._get_session() as session:
            stmt = select(Subscription.ticker).distinct()
            result = await session.execute(stmt)
            orm_results = result.scalars().all()
            tickers = list(orm_results)
            self.logger.info(
                f"Found {len(tickers)} unique subscription tickers")
            return tickers
