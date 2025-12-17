from db.repositories.base import BaseRepository
from schemas.stock import StockPriceCreate, StockPriceResponse, StockNewsCreate, StockNewsChunkCreate, StockNewsResponse
from db.models import Stock, StockNews, StockNewsChunk
from typing import List
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select, func


class StockRepository(BaseRepository):

    async def insert_stock_data(self, stock_data: List[StockPriceCreate] | StockPriceCreate) -> bool:
        """
        Insert one or multiple stock data entries into the database.
        Accepts a single StockPrice or a list of StockPrice (Pydantic) models.
        Converts StockPrice (Pydantic) to Stock (SQLAlchemy ORM).
        Args:
            stock_data (List[StockPrice] | StockPrice): The stock data to insert.
        Returns:
            bool: True if the stock data was inserted successfully, False otherwise.
        """
        # Normalize input type to list
        if not isinstance(stock_data, list):
            stock_data = [stock_data]

        async with self._get_session() as session:
            try:
                stmt = insert(Stock).values(stock_data.model_dump()).on_conflict_do_nothing(
                    index_elements=['ticker', 'trade_date'])
                await session.execute(stmt)
                await session.commit()
                return True
            except Exception as e:
                self.logger.error(f"Error inserting stock data: {e}")
                await session.rollback()
                return False

    async def get_stock_data(self, ticker: str) -> List[StockPriceResponse] | None:
        """
        Get stock data from the database.
        Args:
            ticker (str): The ticker of the stock to get data for.
        Returns:
            List[StockPriceResponse] | None: The stock data for the given ticker.
        """
        async with self._get_session() as session:
            try:
                stmt = select(Stock).where(Stock.ticker == ticker)
                result = await session.execute(stmt)
                orm_results = result.scalars().all()

                return [StockPriceResponse.model_validate(stock) for stock in orm_results]
            except Exception as e:
                self.logger.error(f"Error fetching stock data: {e}")
                return []

    async def remove_stock_data(self, id: int) -> bool:
        """
        Remove stock data from the database.
        Args:
            id (int): The id of the stock data to remove.
        Returns:
            bool: True if the stock data was removed successfully, False otherwise.
        """
        async with self._get_session() as session:
            stmt = select(Stock).where(Stock.id == id)
            result = await session.execute(stmt)
            orm_result = result.scalar_one_or_none()
            if orm_result:
                await session.delete(orm_result)
                await session.commit()
                return True
            else:
                self.logger.error(f"Stock data not found for id: {id}")
                return False

    async def insert_stock_news(self, stock_news: StockNewsCreate, chunks: List[StockNewsChunkCreate]) -> bool:
        """
        Insert stock news and chunks into the database.
        Args:
            stock_news: StockNewsCreate - The stock news to insert.
            chunks: List[StockNewsChunkCreate] - The chunks of the stock news to insert.
        Returns:
            bool: True if the stock news and chunks were inserted successfully, False otherwise.
        """
        async with self._get_session() as session:
            try:
                stmt = insert(StockNews).values(
                    stock_news.model_dump())\
                    .on_conflict_do_nothing(index_elements=['url'])\
                    .returning(StockNews.id)
                result = await session.execute(stmt)
                stock_news_id = result.scalar_one_or_none()
                if not stock_news_id:
                    self.logger.error(
                        f"Stock news already exists: {stock_news.url}")
                    await session.rollback()
                    return False
                chunk_data_list = []
                for chunk in chunks:
                    dumped = chunk.model_dump()
                    dumped['parent_id'] = stock_news_id
                    chunk_data_list.append(dumped)

                if chunk_data_list:
                    await session.execute(insert(StockNewsChunk), chunk_data_list)

                await session.commit()
                return True
            except Exception as e:
                self.logger.error(f"Error inserting stock news: {e}")
                await session.rollback()
                return False

    async def get_stock_news(self, ticker: str, query_embedding: List[float], top_k: int = 5, candidate_pool: int = 20) -> List[StockNewsResponse] | None:
        """
        Get stock news from the database.
        Args:
            ticker: str - The ticker of the stock news to get.
            query_embedding: List[float] - The embedding of the query to get the stock news for.
        Returns:
            List[StockNewsResponse] | None: The stock news for the given ticker and query embedding.
        """
        async with self._get_session() as session:
            try:
                distance_col = StockNewsChunk.embedding.cosine_distance(
                    query_embedding).label("distance")
                subquery = (
                    select(
                        StockNewsChunk.parent_id,
                        distance_col
                    ).where(StockNewsChunk.ticker == ticker)
                    .order_by(distance_col.asc())
                    .limit(candidate_pool)
                    .subquery()
                )
                score_col = func.sum(
                    1 - subquery.c.distance)
                stmt = (
                    select(StockNews, score_col, func.count(
                        subquery.c.parent_id).label("chunk_count")).join(subquery, StockNews.id == subquery.c.parent_id).group_by(StockNews.id).order_by(score_col.desc()).limit(top_k)
                )
                result = await session.execute(stmt)
                orm_results = result.all()
                return [StockNewsResponse.model_validate(news) for news, _score, _count in orm_results]
            except Exception as e:
                self.logger.error(f"Error getting stock news: {e}")
                raise e
