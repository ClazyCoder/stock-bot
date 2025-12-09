import yfinance as yf
import pandas as pd
import asyncio
from interfaces.stock_interface import IStockProvider
from schemas.stock import StockPrice
from typing import List

main_sectors = {
    'technology': '기술 💻',
    'financial-services': '금융 💰',
    'healthcare': '헬스케어 🏥',
    'consumer-cyclical': '소비재 🛍️'
}


class StockDataCollector(IStockProvider):
    def __init__(self):
        pass

    async def get_market_leaders(self, top: int = 3):
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

    async def fetch_stock_price(self, ticker: str) -> StockPrice:
        """
        Fetch stock price data asynchronously.
        Runs blocking yf.download() in a thread pool to avoid blocking the event loop.
        """
        # Run blocking I/O in a thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: yf.download(ticker, period="1d"))

        # Validate that data is not empty
        if data.empty or len(data) == 0:
            raise ValueError(f"No data returned for ticker: {ticker}")

        # Validate that required columns exist
        required_columns = ['Close', 'Open', 'High', 'Low', 'Volume']
        missing_columns = [
            col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(
                f"Missing required columns for ticker {ticker}: {missing_columns}")

        return StockPrice(
            ticker=ticker,
            trade_date=data.index[0],
            close_price=float(data['Close'].iloc[0]),
            open_price=float(data['Open'].iloc[0]),
            high_price=float(data['High'].iloc[0]),
            low_price=float(data['Low'].iloc[0]),
            volume=int(data['Volume'].iloc[0])
        )
