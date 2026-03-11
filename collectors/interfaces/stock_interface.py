from schemas.stock import StockPriceCreate
from typing import List
from typing import Protocol, Union, Any


class IStockProvider(Protocol):
    async def fetch_stock_price(self, tickers: Union[str, List[str]], period: str = "1d") -> List[StockPriceCreate]:
        """
        Fetch the current stock price for one or multiple tickers.
        Args:
            tickers: Union[str, List[str]] - The ticker or tickers of the stock to fetch the price for.
            period: str - The period of the stock to fetch the price for. Valid periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        Returns:
            List[StockPriceCreate] - The current stock price for the given tickers.
        """
        pass

    async def fetch_stock_info(self, ticker: str) -> dict[str, Any] | None:
        """
        Fetch the raw stock info from provider.
        Args:
            ticker (str): The ticker of the stock to get info for.
        Returns:
            dict[str, Any] | None: The raw stock info for the given ticker.
        """
        pass
