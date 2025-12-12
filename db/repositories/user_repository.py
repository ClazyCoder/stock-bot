from db.repositories.base import BaseRepository
from db.models import User
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from schemas.user import UserDTO, SubscriptionDTO


class UserRepository(BaseRepository):
    async def get_user(self, provider: str, provider_id: str) -> UserDTO | None:
        async with self._get_session() as session:
            stmt = select(User).where(User.provider == provider,
                                      User.provider_id == provider_id).options(selectinload(User.subscriptions))
            result = await session.execute(stmt)
            orm_result = result.scalar_one_or_none()

            if orm_result:
                return UserDTO(
                    id=orm_result.id,
                    provider=orm_result.provider,
                    provider_id=orm_result.provider_id,
                    is_authorized=orm_result.is_authorized,
                    created_at=orm_result.created_at,
                    subscriptions=[SubscriptionDTO(
                        ticker=subscription.ticker) for subscription in orm_result.subscriptions]
                )
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
                return UserDTO(
                    id=orm_result.id,
                    provider=orm_result.provider,
                    provider_id=orm_result.provider_id,
                    is_authorized=orm_result.is_authorized,
                    created_at=orm_result.created_at,
                    subscriptions=[SubscriptionDTO(
                        ticker=subscription.ticker) for subscription in orm_result.subscriptions]
                )
            else:
                self.logger.error(
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
