# services/stock_data_service.py
from interfaces.db_interface import IDBModule
from interfaces.stock_interface import IStockProvider
from schemas.stock import StockPrice


class StockDataService:
    def __init__(self, collector: IStockProvider, db: IDBModule):
        self.collector = collector
        self.db_module = db

    async def collect_and_save(self, ticker: str):
        # API에서 데이터 수집
        stock_data = await self.collector.fetch_stock_price(ticker)
        # DB에 저장
        self.db_module.insert_stock_data(stock_data)

    async def get_stock_data(self, ticker: str):
        return self.db_module.get_stock_data(ticker)
