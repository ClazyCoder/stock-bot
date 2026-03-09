from db.repositories.base import BaseRepository
from typing import Any
from sqlalchemy import text


class AdminRepository(BaseRepository):
    async def send_raw_query(self, query: str) -> list[dict[str, Any]] | None:
        """
        Send a raw query to the database.

        Args:
            query: str - The query to send to the database.

        Returns:
            list[dict[str, Any]] | None: The result of the query, or None if an error occurs.
        """
        async with self._get_session() as session:
            try:
                result = await session.execute(text(query))
                orm_results = result.fetchall()
                return [row._asdict() for row in orm_results]
            except Exception as e:
                self.logger.error(
                    f"Error sending raw query: {e}", exc_info=True)
                return None
