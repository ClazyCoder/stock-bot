from typing import List, Tuple
from typing import Protocol, Union
from schemas.stock import StockNewsCreate, StockNewsChunkCreate


class INewsProvider(Protocol):
    async def fetch_news(self, ticker: Union[str, List[str]]) -> List[Tuple[StockNewsCreate, List[StockNewsChunkCreate]]]:
        """
        Fetch the news for one or multiple tickers.
        Args:
            ticker: Union[str, List[str]] - The ticker or tickers of the news to fetch.
        Returns:
            List[Tuple[StockNewsCreate, List[StockNewsChunkCreate]]] - List of tuples containing news and chunks for each ticker.
        """
        pass

