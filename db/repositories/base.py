from sqlalchemy.ext.asyncio import AsyncSession
import logging


class BaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logging.getLogger(__name__)
