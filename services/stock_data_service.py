# services/stock_data_service.py
from interfaces import IDBModule, IStockProvider
import logging


class StockDataService:
    def __init__(self, collector: IStockProvider, db: IDBModule):
        self.logger = logging.getLogger(__name__)
        self.collector = collector
        self.db_module = db

    async def collect_and_save(self, ticker: str):
        # API에서 데이터 수집
        stock_data = await self.collector.fetch_stock_price(ticker)
        if stock_data:
            self.logger.info(f"Collected stock data for {ticker}")
        else:
            self.logger.error(f"Failed to collect stock data for {ticker}")
            return
        # DB에 저장
        result = await self.db_module.insert_stock_data(stock_data)
        if result:
            self.logger.info(f"Saved stock data for {ticker}")
        else:
            self.logger.error(f"Failed to save stock data for {ticker}")
