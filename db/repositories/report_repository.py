from db.repositories.base import BaseRepository
from db.models import StockReport
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from schemas.llm import StockReportCreate, StockReportResponse
from typing import List
from datetime import datetime, date


class ReportRepository(BaseRepository):
    async def insert_stock_report(self, stock_report: List[StockReportCreate]) -> int | None:
        """
        Insert stock report into the database.
        Args:
            stock_report: List[StockReportCreate] - The stock report to insert.
        Returns:
            int | None: The number of affected rows if successful, None otherwise.
        """
        if not stock_report:
            self.logger.warning("No stock report data provided to insert")
            return 0

        async with self._get_session() as session:
            insert_data = [stock.model_dump() for stock in stock_report]
            tickers = [stock.ticker for stock in stock_report]
            try:
                self.logger.info(
                    f"Inserting stock report(s) for ticker(s): {tickers} ({len(insert_data)} report(s))")
                stmt = insert(StockReport).values(insert_data)
                stmt = stmt.on_conflict_do_update(index_elements=['ticker', 'created_at'], set_={
                    'report': stmt.excluded.report,
                    'updated_at': func.now()
                })
                result = await session.execute(stmt)
                affected_rows = result.rowcount
                await session.commit()
                self.logger.info(
                    f"Successfully inserted/updated {affected_rows} stock report(s) for ticker(s): {tickers} (attempted {len(insert_data)})")
                return affected_rows
            except Exception as e:
                self.logger.error(
                    f"Error inserting stock report for ticker(s): {tickers}: {e}", exc_info=True)
                await session.rollback()
                return None

    async def get_stock_reports(self, ticker: str) -> List[StockReportResponse] | None:
        """
        Get stock reports from the database.
        Args:
            ticker: str - The ticker of the stock to get reports for.
        Returns:
            List[StockReportResponse] | None: The stock reports if successful, None otherwise.
        """
        async with self._get_session() as session:
            try:
                self.logger.debug(
                    f"Fetching stock reports for ticker: {ticker}")
                stmt = select(StockReport).where(StockReport.ticker ==
                                                 ticker).order_by(StockReport.created_at.desc())
                result = await session.execute(stmt)
                orm_results = result.scalars().all()
                stock_reports = [StockReportResponse.model_validate(
                    orm_result) for orm_result in orm_results]
                if stock_reports:
                    self.logger.info(
                        f"Fetched {len(stock_reports)} stock report(s) for ticker: {ticker}")
                else:
                    self.logger.warning(
                        f"No stock reports found for ticker: {ticker}")
                return stock_reports
            except Exception as e:
                self.logger.error(
                    f"Error fetching stock reports for ticker {ticker}: {e}", exc_info=True)
                return None

    async def get_stock_report_with_date(self, ticker: str, target_date: date | datetime) -> StockReportResponse | None:
        """
        Get stock report from the database for a specific ticker and date.
        Args:
            ticker: str - The ticker of the stock to get report for.
            target_date: date | datetime - The date of the stock report to get. 
                        If datetime is provided, only the date part is used for comparison.
        Returns:
            StockReportResponse | None: The stock report if successful, None otherwise.
        """
        async with self._get_session() as session:
            try:
                # Normalize to date type (created_at is Date type in DB)
                report_date = target_date.date() if isinstance(
                    target_date, datetime) else target_date

                self.logger.debug(
                    f"Fetching stock report for ticker: {ticker}, date: {report_date}")
                # Since created_at is Date type, we can directly compare with date
                stmt = select(StockReport).where(
                    StockReport.ticker == ticker,
                    StockReport.created_at == report_date
                ).order_by(StockReport.created_at.desc())
                result = await session.execute(stmt)
                orm_result = result.scalar_one_or_none()

                if orm_result:
                    stock_report = StockReportResponse.model_validate(
                        orm_result)
                    self.logger.info(
                        f"Fetched stock report for ticker: {ticker}, date: {report_date} (created_at: {stock_report.created_at})")
                    return stock_report
                else:
                    self.logger.warning(
                        f"No stock report found for ticker: {ticker}, date: {report_date}")
                    return None
            except Exception as e:
                self.logger.error(
                    f"Error fetching stock report for ticker {ticker}, date {target_date}: {e}", exc_info=True)
                return None
