import logging
from db.repositories.stock_repository import StockRepository
from typing import List
from schemas.llm import StockPriceLLMContext
from utils.formatter import to_csv_string
from langchain.tools import tool, BaseTool


class StockTools:
    def __init__(self, stock_repository: StockRepository):
        self.logger = logging.getLogger(__name__)
        self.stock_repository = stock_repository

    async def get_stock_news_llm_context(self, ticker: str, query: str, top_k: int = 5, candidate_pool: int = 20) -> List[str]:
        """
        Get stock news from the database and convert it to LLM context.
        Args:
            ticker (str): The ticker of the stock to get news for.
            query (str): The query to get news for.
            top_k (int): The number of news to get.
            candidate_pool (int): The number of chunks to get.
        Returns:
            List[str]: The List of stock news for the given ticker and query in string format. Returns empty list if no news is found. The news format is "Title: {title}\nPublished at: {published_at}\nFull content: \n{full_content}".
        """
        self.logger.info(
            f"Getting stock news LLM context for {ticker} with query {query}, top_k={top_k}, candidate_pool={candidate_pool}")
        try:
            stock_news = await self.stock_repository.get_stock_news(ticker, query, top_k, candidate_pool)
            if stock_news:
                result = [
                    f"Title: {news.title}\nPublished at: {news.published_at}\nFull content: \n{'-'*100}\n{news.full_content}\n{'-'*100}" for news in stock_news]
                self.logger.info(
                    f"Generated LLM context for ticker {ticker}: {len(result)} news items")
                return result
            else:
                self.logger.warning(
                    f"No stock news found for ticker {ticker} when generating LLM context; returning empty list.")
                return []
        except Exception as e:
            self.logger.error(
                f"Error getting stock news LLM context for ticker {ticker} with query {query}: {e}. Returning empty list.",
                exc_info=True,
            )
            return []

    async def get_stock_data_llm_context(self, ticker: str, count: int = 5) -> str | None:
        """
        Get stock data from the database and convert it to LLM context.
        Args:
            ticker (str): The ticker of the stock to get data for.
            count (int): The number of data to get. from the latest data.
        Returns:
            str | None: The stock data for the given ticker in CSV string format. if no data is found, return None.
        """
        self.logger.info(
            f"Getting stock data LLM context for {ticker} with count {count}")
        try:
            stock_data = await self.stock_repository.get_stock_data(ticker)
            if not stock_data:
                self.logger.warning(
                    f"No stock data found for ticker {ticker} when generating LLM context")
                return None
            stock_data_llm_context = [
                StockPriceLLMContext.model_validate(data) for data in stock_data[-count:]]
            csv_string = to_csv_string(stock_data_llm_context)
            self.logger.info(
                f"Generated LLM context for ticker {ticker}: {len(stock_data_llm_context)} records")
            return csv_string
        except Exception as e:
            self.logger.error(
                f"Error getting stock data LLM context for ticker {ticker}: {e}", exc_info=True)
            return None

    def get_tools(self) -> List[BaseTool]:
        tools = [tool(self.get_stock_data_llm_context),
                 tool(self.get_stock_news_llm_context)]
        self.logger.info(f"Built {len(tools)} tools")
        return tools
