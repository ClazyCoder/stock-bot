from db.repositories.base import BaseRepository
from typing import List, Dict
from sqlalchemy import text


class AdminRepository(BaseRepository):
    async def send_raw_query(self, query: str) -> List[Dict] | None:
        '''
        Send a raw query to the database.
        Args:
            query: str - The query to send to the database.
        Returns:
            List[Dict]: The result of the query.
        '''
        async with self._get_session() as session:
            try:
                result = await session.execute(text(query))
                orm_results = result.fetchall()
                return [row._asdict() for row in orm_results]
            except Exception as e:
                self.logger.error(
                    f"Error sending raw query: {e}", exc_info=True)
                return None
