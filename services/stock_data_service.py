# services/stock_data_service.py
from interfaces import IStockProvider
from db.repositories.stock_repository import StockRepository
import logging


class StockDataService:
    def __init__(self, collector: IStockProvider, stock_repository: StockRepository):
        self.logger = logging.getLogger(__name__)
        self.collector = collector
        self.stock_repository = stock_repository

    async def collect_and_save(self, ticker: str):
        # API에서 데이터 수집
        stock_data = await self.collector.fetch_stock_price(ticker)
        if stock_data:
            self.logger.info(f"Collected stock data for {ticker}")
        else:
            self.logger.error(f"Failed to collect stock data for {ticker}")
            return False
        # DB에 저장
        result = await self.stock_repository.insert_stock_data(stock_data)
        if result:
            self.logger.info(f"Saved stock data for {ticker}")
        else:
            self.logger.error(f"Failed to save stock data for {ticker}")
            return False
        return True
