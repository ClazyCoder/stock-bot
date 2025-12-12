import yfinance as yf
import asyncio
import pandas as pd
from interfaces import IStockProvider
from schemas import StockPrice
from typing import List

main_sectors = {
    'technology': 'Technology 💻',
    'financial-services': 'Financial Services 💰',
    'healthcare': 'Healthcare 🏥',
    'consumer-cyclical': 'Consumer Cyclical 🛍️'
}


class StockDataCollector(IStockProvider):
    def __init__(self):
        pass

    def get_market_leaders(self, top: int = 3):
        '''
        Get the top N stocks in each sector.
        Returns a dictionary with the sector name as the key and the top N stocks as the value.
        '''
        main_leaders = {}
        for key, value in main_sectors.items():
            try:
                sector = yf.Sector(key)
                top_N = sector.top_companies.head(top).index.to_list()
                main_leaders[value] = top_N
            except Exception as e:
                print(f"Error scanning {key} sector: {e}")
                continue
        return main_leaders

    async def fetch_stock_price(self, tickers, period: str = "1d") -> List[StockPrice]:
        """
        Fetch stock price data for one or multiple tickers asynchronously.
        Runs blocking yf.download() in a thread pool to avoid blocking the event loop.

        Args:
            tickers (Union[str, List[str]]): Single ticker or list of ticker symbols.
            period (str): Period string for yfinance. Default: "1d".
        Returns:
            List[StockPrice]
        """
        if isinstance(tickers, str):
            tickers_list = [tickers]
        else:
            tickers_list = tickers

        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(
            None,
            lambda: yf.download(
                tickers=" ".join(tickers_list),
                period=period,
                auto_adjust=False,
                group_by='ticker' if len(tickers_list) > 1 else None,
            )
        )

        results: List[StockPrice] = []

        # yfinance returns a multi-index dataframe with columns (ticker, field) if multiple tickers
        for ticker in tickers_list:
            if len(tickers_list) == 1:
                # Single ticker: yfinance sometimes returns MultiIndex even for single ticker
                if isinstance(data.columns, pd.MultiIndex):
                    # MultiIndex columns: try to extract ticker's data
                    level0_values = data.columns.get_level_values(0).unique()
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
                if ticker not in data.columns.get_level_values(0):
                    raise ValueError(f"No data returned for ticker: {ticker}")
                stock_df = data[ticker]

            if stock_df.empty or len(stock_df) == 0:
                raise ValueError(f"No data returned for ticker: {ticker}")

            # Check if columns are still MultiIndex after extraction
            if isinstance(stock_df.columns, pd.MultiIndex):
                # Flatten MultiIndex columns - take the last level (usually the field name)
                stock_df = stock_df.copy()
                stock_df.columns = stock_df.columns.get_level_values(-1)

            required_columns = ['Close', 'Open', 'High', 'Low', 'Volume']
            missing_columns = [
                col for col in required_columns if col not in stock_df.columns]
            if missing_columns:
                raise ValueError(
                    f"Missing required columns for ticker {ticker}: {missing_columns}. "
                    f"Available columns: {list(stock_df.columns)}"
                )

            for idx in range(len(stock_df)):
                results.append(StockPrice(
                    ticker=ticker,
                    trade_date=stock_df.index[idx],
                    close_price=float(stock_df['Close'].iloc[idx].item()),
                    open_price=float(stock_df['Open'].iloc[idx].item()),
                    high_price=float(stock_df['High'].iloc[idx].item()),
                    low_price=float(stock_df['Low'].iloc[idx].item()),
                    volume=int(stock_df['Volume'].iloc[idx].item())
                ))
        return results
