from analysis.llm_module import LLMModule
from db.repositories.stock_repository import StockRepository
from db.repositories.report_repository import ReportRepository
import logging
import os
from typing import List, Callable, Optional
from schemas.llm import StockPriceLLMContext
from utils.formatter import to_csv_string
from datetime import datetime
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.tools import BaseTool
from langchain.tools import tool

# Constants
EDGAR_IDENTITY_PLACEHOLDER = "Your Name your.email@example.com"


class LLMService:
    def __init__(self, stock_repository: StockRepository, report_repository: ReportRepository):
        self.logger = logging.getLogger(__name__)
        self.llm_module: Optional[LLMModule] = None
        self.stock_repository = stock_repository
        self.report_repository = report_repository
        self.logger.info("Initializing MCP client...")
        # Validate EDGAR_IDENTITY is set and not the placeholder
        edgar_identity = os.getenv("EDGAR_IDENTITY", "")
        if not edgar_identity or edgar_identity == EDGAR_IDENTITY_PLACEHOLDER:
            raise EnvironmentError(
                "EDGAR_IDENTITY environment variable is not set or is using the placeholder value. "
                "Please set EDGAR_IDENTITY to your actual name and email (e.g., 'John Doe john.doe@example.com'). "
                "This is required by the SEC EDGAR API to identify your application."
            )

        self._mcp_client = MultiServerMCPClient(
            {
                "edgartools": {
                    "transport": "stdio",
                    "command": "python",
                    "args": ["-m", "edgar.ai"],
                    "env": {
                        "EDGAR_IDENTITY": edgar_identity
                    }
                }
            }
        )
        self.logger.info("MCP client initialized successfully")

    async def build_tools(self, tool_func_list: List[Callable]) -> List[BaseTool]:
        mcp_tools = await self._mcp_client.get_tools()
        self.logger.info(f"Found {len(mcp_tools)} mcp tools")
        tools = [tool(func) for func in tool_func_list]
        self.logger.info(f"Built {len(tools)} local tools")
        return tools + mcp_tools

    async def _ensure_llm_module_initialized(self):
        """LLMModule이 초기화되지 않았다면 build_tools를 사용하여 초기화합니다."""
        if self.llm_module is None:
            self.logger.info("Initializing LLMModule with tools...")
            tool_func_list = [self.get_stock_data_llm_context,
                              self.get_stock_news_llm_context]
            tools = await self.build_tools(tool_func_list)
            self.llm_module = LLMModule(tools=tools)
            self.logger.info("LLMModule initialized successfully")

    async def generate_report_with_ticker(self, ticker: str) -> str:
        """
        Generate a report for a given ticker.
        First checks if a report for today already exists in the database.
        If not, generates a new report and saves it to the database.
        """
        self.logger.info(f"Generating report for {ticker}...")

        # Check if today's report already exists
        today = datetime.now().date()
        existing_report = await self.report_repository.get_stock_report_with_date(ticker, today)
        if existing_report:
            self.logger.info(
                f"Found existing report for {ticker} on {today}, returning cached report")
            return existing_report.report

        # Generate new report
        self.logger.info(
            f"No existing report found for {ticker} on {today}, generating new report...")
        await self._ensure_llm_module_initialized()
        report_content = await self.llm_module.generate_report_with_ticker(ticker)

        # Save report to database
        from schemas.llm import StockReportCreate
        stock_report = StockReportCreate(
            ticker=ticker,
            report=report_content,
            created_at=datetime.now()
        )
        insert_result = await self.report_repository.insert_stock_report([stock_report])
        if insert_result is None:
            self.logger.error(
                f"Failed to save report for {ticker} to database, but returning generated report")
        else:
            self.logger.info(
                f"Successfully saved report for {ticker} to database")

        return report_content

    async def get_today_stock_report(self, ticker: str) -> str:
        """
        Get today's stock report from the database.
        Args:
            ticker (str): The ticker of the stock to get report for.
        Returns:
            str: The stock report for the given ticker in string format.
        """
        self.logger.info(f"Getting today's stock report for {ticker}...")
        today = datetime.now().date()
        report = await self.report_repository.get_stock_report_with_date(ticker, today)
        if report:
            return report.report
        else:
            return None

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
