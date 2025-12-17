import yfinance as yf
import asyncio
import pandas as pd
from interfaces import IStockProvider
from schemas.stock import StockPriceCreate
from typing import List, Union
import logging

main_sectors = {
    'technology': 'Technology 💻',
    'financial-services': 'Financial Services 💰',
    'healthcare': 'Healthcare 🏥',
    'consumer-cyclical': 'Consumer Cyclical 🛍️'
}


class StockDataCollector(IStockProvider):
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_market_leaders(self, top: int = 3):
        '''
        Get the top N stocks in each sector.
        Returns a dictionary with the sector name as the key and the top N stocks as the value.
        '''
        self.logger.info(
            f"Getting market leaders for top {top} stocks in each sector")
        main_leaders = {}
        for key, value in main_sectors.items():
            try:
                self.logger.debug(f"Scanning sector: {key}")
                sector = yf.Sector(key)
                top_N = sector.top_companies.head(top).index.to_list()
                main_leaders[value] = top_N
                self.logger.info(
                    f"Found {len(top_N)} top stocks for sector {value}: {top_N}")
            except Exception as e:
                self.logger.error(
                    f"Error scanning {key} sector: {e}", exc_info=True)
                continue
        self.logger.info(
            f"Market leaders collection completed. Found leaders for {len(main_leaders)} sectors")
        return main_leaders

    async def fetch_stock_price(self, tickers: Union[str, List[str]], period: str = "1d") -> List[StockPriceCreate]:
        """
        Fetch stock price data for one or multiple tickers asynchronously.
        Runs blocking yf.download() in a thread pool to avoid blocking the event loop.

        Args:
            tickers (Union[str, List[str]]): Single ticker or list of ticker symbols.
            period (str): Period string for yfinance. Default: "1d".
        Returns:
            List[StockPriceCreate]: List of stock price data. Returns empty list if no data is found or if an error occurs.
        """
        if isinstance(tickers, str):
            tickers_list = [tickers]
        else:
            tickers_list = tickers

        self.logger.info(
            f"Fetching stock price data for {len(tickers_list)} ticker(s): {tickers_list}, period: {period}")

        loop = asyncio.get_running_loop()
        try:
            data = await loop.run_in_executor(
                None,
                lambda: yf.download(
                    tickers=" ".join(tickers_list),
                    period=period,
                    auto_adjust=False,
                    group_by='ticker' if len(tickers_list) > 1 else None,
                )
            )
        except Exception as e:
            self.logger.error(
                f"Error downloading stock data for tickers {tickers_list}: {e}", exc_info=True)
            return []

        results: List[StockPriceCreate] = []

        # Check if data is empty
        if data.empty or len(data) == 0:
            self.logger.warning(
                f"No data returned for tickers: {tickers_list}, period: {period}")
            return results

        # yfinance returns a multi-index dataframe with columns (ticker, field) if multiple tickers
        for ticker in tickers_list:
            try:
                if len(tickers_list) == 1:
                    # Single ticker: yfinance sometimes returns MultiIndex even for single ticker
                    if isinstance(data.columns, pd.MultiIndex):
                        # MultiIndex columns: try to extract ticker's data
                        level0_values = data.columns.get_level_values(
                            0).unique()
                        if ticker in level0_values:
                            # Ticker is in first level
                            stock_df = data[ticker]
                        else:
                            # Ticker might be in a different level or structure is different
                            # Try to flatten by taking the last level
                            stock_df = data.copy()
                            stock_df.columns = stock_df.columns.get_level_values(
                                -1)
                    else:
                        # Single level columns
                        stock_df = data
                else:
                    # Multiple tickers: extract specific ticker
                    if not isinstance(data.columns, pd.MultiIndex):
                        # If not MultiIndex, data might be empty or malformed
                        continue

                    level0_values = data.columns.get_level_values(0).unique()
                    if ticker not in level0_values:
                        # Skip this ticker if not found, but continue with others
                        continue

                    try:
                        stock_df = data[ticker]
                    except (KeyError, IndexError):
                        # Skip this ticker if extraction fails
                        continue

                if stock_df.empty or len(stock_df) == 0:
                    # Skip this ticker if no data, but continue with others
                    continue

                # Check if columns are still MultiIndex after extraction
                if isinstance(stock_df.columns, pd.MultiIndex):
                    # Flatten MultiIndex columns - take the last level (usually the field name)
                    stock_df = stock_df.copy()
                    stock_df.columns = stock_df.columns.get_level_values(-1)

                required_columns = ['Close', 'Open', 'High', 'Low', 'Volume']
                missing_columns = [
                    col for col in required_columns if col not in stock_df.columns]
                if missing_columns:
                    # Skip this ticker if required columns are missing
                    continue

                for idx in range(len(stock_df)):
                    close_price = stock_df['Close'].iloc[idx]
                    open_price = stock_df['Open'].iloc[idx]
                    high_price = stock_df['High'].iloc[idx]
                    low_price = stock_df['Low'].iloc[idx]
                    volume = stock_df['Volume'].iloc[idx]

                    # Skip rows with NaN or None values in required fields
                    if pd.isna(close_price) or pd.isna(open_price) or pd.isna(high_price) or pd.isna(low_price) or pd.isna(volume):
                        continue

                    results.append(StockPriceCreate(
                        ticker=ticker,
                        trade_date=stock_df.index[idx],
                        close_price=float(close_price),
                        open_price=float(open_price),
                        high_price=float(high_price),
                        low_price=float(low_price),
                        volume=int(volume)
                    ))
                self.logger.info(
                    f"Successfully processed {len(results)} data points for ticker {ticker}")
            except Exception as e:
                # Log error but continue processing other tickers
                # Skip this ticker if any error occurs
                self.logger.error(
                    f"Error fetching stock price for ticker {ticker}: {e}. Skipping this ticker.", exc_info=True)
                continue

        self.logger.info(
            f"Fetched stock price data: {len(results)} total records for {len(tickers_list)} ticker(s)")
        return results
