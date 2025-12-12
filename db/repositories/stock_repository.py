from db.repositories.base import BaseRepository
from schemas.stock import StockPriceCreate, StockPriceResponse
from db.models import Stock
from typing import List
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select


class StockRepository(BaseRepository):

    async def insert_stock_data(self, stock_data: List[StockPriceCreate] | StockPriceCreate):
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

        stock_models = [
            Stock(
                ticker=sd.ticker,
                trade_date=sd.trade_date,
                open=sd.open_price,
                high=sd.high_price,
                low=sd.low_price,
                close=sd.close_price,
                volume=sd.volume,
            )
            for sd in stock_data
        ]
        async with self._get_session() as session:
            try:
                session.add_all(stock_models)
                await session.commit()
                return True
            except IntegrityError as e:
                await session.rollback()
                self.logger.warning(f"Some stock data already exists: {e}")
                return False
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

                pydantic_results = [
                    StockPriceResponse(
                        id=stock.id,
                        ticker=stock.ticker,
                        trade_date=stock.trade_date,
                        open_price=stock.open,
                        high_price=stock.high,
                        low_price=stock.low,
                        close_price=stock.close,
                        volume=stock.volume,
                    ) for stock in orm_results
                ]
                return pydantic_results
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
