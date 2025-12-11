from schemas.stock import StockPrice
from typing import Protocol


class IStockProvider(Protocol):
    async def fetch_stock_price(self, ticker: str, period: str = "1d") -> StockPrice:
        """
        Fetch the current stock price for a given ticker.
        Args:
            ticker: str - The ticker of the stock to fetch the price for.
            period: str - The period of the stock to fetch the price for.
        Returns:
            StockPrice - The current stock price for the given ticker.
        """
        pass
