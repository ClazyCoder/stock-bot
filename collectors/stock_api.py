import yfinance as yf
import pandas as pd
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
        self.main_leaders = self.get_market_leaders()
        self.all_tickers = [ticker for tickers in self.main_leaders.values()
                            for ticker in tickers]

    def get_market_leaders(self):
        '''
        Get the top 3 stocks in each sector.
        Returns a dictionary with the sector name as the key and the top 3 stocks as the value.
        '''
        main_leaders = {}
        for key, value in main_sectors.items():
            try:
                sector = yf.Sector(key)
                top3 = sector.top_companies.head(3).index.to_list()
                main_leaders[value] = top3
            except Exception as e:
                print(f"Error scanning {key} sector: {e}")
                continue
        return main_leaders

    async def fetch_stock_price(self, ticker: str) -> StockPrice:
        data = yf.download(ticker, period="1d")
        return StockPrice(
            ticker=ticker,
            trade_date=data.index[0],
            close_price=data['Close'][0],
            open_price=data['Open'][0],
            high_price=data['High'][0],
            low_price=data['Low'][0],
            volume=data['Volume'][0]
        )
