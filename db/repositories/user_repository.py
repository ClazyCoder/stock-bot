from db.repositories.base import BaseRepository
from db.models import User
from sqlalchemy import select
from sqlalchemy.orm import selectinload


class UserRepository(BaseRepository):

    async def register_user(self, provider: str, provider_id: str):
        user = User(provider=provider, provider_id=provider_id,
                    is_authorized=True)
        self.session.add(user)
        await self.session.commit()
        return True

    async def get_authrized_user(self, provider: str, provider_id: str) -> User | None:
        stmt = select(User).where(User.provider == provider,
                                  User.provider_id == provider_id,
                                  User.is_authorized == True
                                  ).options(selectinload(User.subscriptions))
        result = await self.session.execute(stmt)
        orm_result = result.scalar_one_or_none()
        return orm_result
