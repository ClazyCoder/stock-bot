from schemas.stock import StockPrice
from typing import Protocol


class IStockProvider(Protocol):
    async def fetch_stock_price(self, ticker: str) -> StockPrice:
        """
        Fetch the current stock price for a given ticker.
        """
        pass
