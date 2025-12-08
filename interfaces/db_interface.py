from typing import Protocol
from schemas.stock import StockPrice
from typing import List


class IDBModule(Protocol):
    def insert_stock_data(self, stock_data: StockPrice):
        """
        Insert stock data into the database.
        """
        pass

    def get_stock_data(self, ticker: str) -> List[StockPrice]:
        """
        Get stock data from the database.
        """
        pass
