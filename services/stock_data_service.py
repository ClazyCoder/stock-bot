# services/stock_data_service.py
from collectors.interfaces import IStockProvider, INewsProvider
from db.repositories.stock_repository import StockRepository
import logging
from typing import List
from schemas.stock import StockPriceResponse, StockNewsResponse
from typing import Union


class StockDataService:
    def __init__(self, collector: IStockProvider, stock_repository: StockRepository, news_collector: INewsProvider):
        self.logger = logging.getLogger(__name__)
        self.collector = collector
        self.stock_repository = stock_repository
        self.news_collector = news_collector

    async def collect_and_save(self, ticker: Union[str, List[str]], period: str = "1d"):
        # Collect data from API
        stock_data = await self.collector.fetch_stock_price(ticker, period)
        if stock_data:
            self.logger.info(f"Collected stock data for {ticker}")
        else:
            self.logger.error(f"Failed to collect stock data for {ticker}")
            return False
        # Save to database
        result = await self.stock_repository.insert_stock_data(stock_data)
        if result is None:
            self.logger.error(
                f"Failed to save stock data for {ticker}: database error")
            return False
        elif result == 0:
            self.logger.warning(
                f"No stock data was inserted/updated for {ticker} (may already exist)")
            return True  # Not an error, just no new data
        else:
            self.logger.info(
                f"Saved stock data for {ticker}: {result} row(s) affected")
            return True

    async def get_stock_data(self, ticker: str) -> List[StockPriceResponse] | None:
        """
        Get stock data from the database.
        Args:
            ticker (str): The ticker of the stock to get data for.
        Returns:
            List[StockPriceResponse] | None: The stock data for the given ticker.
        """
        self.logger.info(f"Getting stock data for ticker: {ticker}")
        try:
            result = await self.stock_repository.get_stock_data(ticker)
            if result:
                self.logger.info(
                    f"Found {len(result)} stock data records for ticker: {ticker}")
            else:
                self.logger.warning(
                    f"No stock data found for ticker: {ticker}")
            return result
        except Exception as e:
            self.logger.error(
                f"Error getting stock data for ticker {ticker}: {e}", exc_info=True)
            return None

    async def collect_and_save_stock_news(self, tickers: Union[str, List[str]]) -> bool:
        """
        Collect and save stock news for the given ticker or tickers.
        Args:
            tickers (Union[str, List[str]]): The ticker or tickers of the stock to collect news for.
        Returns:
            bool: True if the stock news was collected and saved successfully, False otherwise.
        """
        try:
            news_list = await self.news_collector.fetch_news(tickers)
            if not news_list:
                self.logger.warning(f"No news collected for {tickers}")
                return False

            self.logger.info(
                f"Collected {len(news_list)} news items for {tickers}")
            result = await self.stock_repository.insert_multiple_stock_news(news_list)
            if result is None:
                self.logger.error(
                    f"Failed to save stock news for {tickers}: database error")
                return False
            elif result == 0:
                self.logger.warning(
                    f"No stock news was inserted/updated for {tickers} (may already exist)")
                return True  # Not an error, just no new data
            else:
                self.logger.info(
                    f"Saved stock news for {tickers}: {result} row(s) affected")
                return True
        except Exception as e:
            self.logger.error(
                f"Failed to collect stock news for {tickers}: {e}", exc_info=True)
            return False

    async def get_stock_news(self, ticker: str, query: str, top_k: int = 5, candidate_pool: int = 20) -> StockNewsResponse | None:
        """
        Get stock news from the database.
        Args:
            ticker (str): The ticker of the stock to get news for.
            query (str): The query to get news for.
            top_k (int): The number of news to get.
            candidate_pool (int): The number of chunks to get.
        Returns:
            List[StockNewsResponse] | None: The stock news for the given ticker and query embedding.
        """
        self.logger.info(
            f"Getting stock news for {ticker} with query {query}, top_k={top_k}, candidate_pool={candidate_pool}")
        try:
            result = await self.stock_repository.get_stock_news(ticker, query, top_k, candidate_pool)
            if result:
                self.logger.info(
                    f"Found {len(result)} stock news items for ticker {ticker} with query {query}")
            else:
                self.logger.warning(
                    f"No stock news found for ticker {ticker} with query {query}")
            return result
        except Exception as e:
            self.logger.error(
                f"Error getting stock news for ticker {ticker} with query {query}: {e}", exc_info=True)
            return None
