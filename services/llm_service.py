from analysis.llm_module import LLMModule
from db.repositories.stock_repository import StockRepository
from db.repositories.report_repository import ReportRepository
import logging
import os
from typing import List, Callable
from schemas.llm import StockPriceLLMContext
from utils.formatter import to_csv_string
from datetime import datetime
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.tools import BaseTool
from langchain.tools import tool


class LLMService:
    def __init__(self, llm_module: LLMModule, stock_repository: StockRepository, report_repository: ReportRepository):
        self.logger = logging.getLogger(__name__)
        self.llm_module = llm_module
        self.stock_repository = stock_repository
        self.report_repository = report_repository

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
