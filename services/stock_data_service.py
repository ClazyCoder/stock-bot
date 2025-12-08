# services/stock_data_service.py
from collectors.stock_api import StockDataCollector
from db.db_module import STOCK_DBModule
from schemas.stock import StockPrice


class StockDataService:
    def __init__(self):
        self.collector = StockDataCollector()
        self.db = STOCK_DBModule()

    async def collect_and_save(self, ticker: str):
        # API에서 데이터 수집
        stock_data = await self.collector.fetch_stock_price(ticker)
        # DB에 저장
        self.db.insert_stock_data(stock_data)
