from sqlalchemy.ext.asyncio import async_sessionmaker
from contextlib import asynccontextmanager
import logging


class BaseRepository:
    def __init__(self, session_factory: async_sessionmaker):
        self.session_factory = session_factory
        self.logger = logging.getLogger(__name__)

    @asynccontextmanager
    async def _get_session(self):
        """Create and automatically close a session for each method call."""
        session = self.session_factory()
        try:
            yield session
        finally:
            await session.close()
