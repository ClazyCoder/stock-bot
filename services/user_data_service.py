from db.repositories.user_repository import UserRepository
import logging
from schemas.user import UserDTO


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
