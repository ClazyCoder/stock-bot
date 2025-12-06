from schemas.stock import StockPrice
from typing import Protocol


class IStockProvider(Protocol):
    async def fetch_current_stock_price(self, ticker: str) -> StockPrice:
        """
        Fetch the current stock price for a given ticker.
        """
        pass


class IStockAnalyzer(Protocol):
    async def analyze_stock_price(self, stock_price: StockPrice) -> StockPrice:
        """
        Analyze the stock price and return a summary of the analysis.
        """
        pass


class IStockRecommendation(Protocol):
    async def recommend_stock(self, stock_price: StockPrice) -> StockPrice:
        """
        Recommend a stock based on the analysis.
        """
        pass
