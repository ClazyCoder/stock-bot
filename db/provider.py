from interfaces import IBotDBModule
from db.repositories.user_repository import UserRepository
from db.repositories.stock_repository import StockRepository
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.user import UserDTO


class BotDataProvider(IBotDBModule):
    def __init__(self, session_local: AsyncSession):
        self.user_repository = UserRepository(session_local)
        self.stock_repository = StockRepository(session_local)

    async def register_user(self, provider: str, provider_id: str) -> bool:
        return await self.user_repository.register_user(provider, provider_id)

    async def get_authrized_user(self, provider: str, provider_id: str) -> UserDTO | None:
        return await self.user_repository.get_authrized_user(provider, provider_id)
