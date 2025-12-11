# services/stock_data_service.py
from interfaces import IStockProvider
from db.repositories.stock_repository import StockRepository
import logging
from typing import List
from schemas.stock import StockPrice


class StockDataService:
    def __init__(self, collector: IStockProvider, stock_repository: StockRepository):
        self.logger = logging.getLogger(__name__)
        self.collector = collector
        self.stock_repository = stock_repository

    async def collect_and_save(self, ticker: str, period: str = "1d"):
        # Collect data from API
        stock_data = await self.collector.fetch_stock_price(ticker, period)
        if stock_data:
            self.logger.info(f"Collected stock data for {ticker}")
        else:
            self.logger.error(f"Failed to collect stock data for {ticker}")
            return False
        # Save to database
        result = await self.stock_repository.insert_stock_data(stock_data)
        if result:
            self.logger.info(f"Saved stock data for {ticker}")
        else:
            self.logger.error(f"Failed to save stock data for {ticker}")
            return False
        return True

    async def get_stock_data(self, ticker: str) -> List[StockPrice] | None:
        """
        Get stock data from the database.
        Args:
            ticker (str): The ticker of the stock to get data for.
        Returns:
            List[StockPrice] | None: The stock data for the given ticker.
        """
        return await self.stock_repository.get_stock_data(ticker)
