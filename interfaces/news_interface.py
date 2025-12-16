from typing import List
from typing import Protocol, Union
from schemas.stock import StockNewsCreate


class INewsProvider(Protocol):
    async def fetch_news(self, ticker: Union[str, List[str]]) -> List[StockNewsCreate]:
        """
        Fetch the news for one or multiple tickers.
        Args:
            ticker: Union[str, List[str]] - The ticker or tickers of the news to fetch.
        Returns:
            List[StockNewsCreate] - The news for the given tickers.
        """
        pass
