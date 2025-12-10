from sqlalchemy.ext.asyncio import AsyncSession
import logging


class BaseRepository:
    def __init__(self, session_local: AsyncSession):
        self.session = session_local
        self.logger = logging.getLogger(__name__)
