from analysis.llm_module import LLMModule
from db.repositories.stock_repository import StockRepository
from db.repositories.report_repository import ReportRepository
from schemas.llm import StockReportCreate
import logging
import asyncio
from typing import Dict
from utils.common import get_today_in_business_timezone


class LLMService:
    def __init__(self, llm_module: LLMModule, stock_repository: StockRepository, report_repository: ReportRepository):
        self.logger = logging.getLogger(__name__)
        self.llm_module = llm_module
        self.stock_repository = stock_repository
        self.report_repository = report_repository
        # Per-ticker locks to prevent race conditions in report generation
        self._report_locks: Dict[str, asyncio.Lock] = {}
        self._locks_lock = asyncio.Lock()

    async def _get_ticker_lock(self, ticker: str) -> asyncio.Lock:
        """Get or create a lock for a specific ticker."""
        async with self._locks_lock:
            if ticker not in self._report_locks:
                self._report_locks[ticker] = asyncio.Lock()
            return self._report_locks[ticker]

    async def generate_report_with_ticker(self, ticker: str) -> str:
        """
        Generate a report for a given ticker.
        First checks if a report for today already exists in the database.
        If not, generates a new report and saves it to the database.
        Uses per-ticker locking to prevent race conditions when multiple
        concurrent requests try to generate reports for the same ticker.
        """
        self.logger.info(f"Generating report for {ticker}...")

        # Use timezone-aware date to ensure consistent behavior regardless of server location
        today = get_today_in_business_timezone()

        # Fast path: Check for existing report before acquiring lock to avoid lock contention
        # in the common case where a report already exists
        existing_report = await self.report_repository.get_stock_report_with_date(ticker, today)
        if existing_report:
            self.logger.info(
                f"Found existing report for {ticker} on {today}, returning cached report")
            return existing_report.report

        # Get ticker-specific lock to prevent concurrent generation
        ticker_lock = await self._get_ticker_lock(ticker)

        async with ticker_lock:
            # Double-check after acquiring lock (another request may have completed)
            existing_report = await self.report_repository.get_stock_report_with_date(ticker, today)
            if existing_report:
                self.logger.info(
                    f"Found existing report for {ticker} on {today} (after lock acquisition), returning cached report")
                return existing_report.report

            # Generate new report
            self.logger.info(
                f"No existing report found for {ticker} on {today}, generating new report...")
            report_content = await self.llm_module.generate_report_with_ticker(ticker)

            # Save report to database
            stock_report = StockReportCreate(
                ticker=ticker,
                report=report_content,
                created_at=today  # Use the date variable already computed above
            )
            insert_result = await self.report_repository.insert_stock_report([stock_report])
            if insert_result is None:
                self.logger.error(
                    f"Failed to save report for {ticker} to database, but returning generated report")
            else:
                self.logger.info(
                    f"Successfully saved report for {ticker} to database")

            return report_content

    async def get_today_stock_report(self, ticker: str) -> str | None:
        """
        Get today's stock report from the database.
        Args:
            ticker (str): The ticker of the stock to get report for.
        Returns:
            str: The stock report for the given ticker in string format.
        """
        self.logger.info(f"Getting today's stock report for {ticker}...")
        # Use timezone-aware date to ensure consistent behavior regardless of server location
        today = get_today_in_business_timezone()
        report = await self.report_repository.get_stock_report_with_date(ticker, today)
        if report:
            return report.report
        else:
            return None
