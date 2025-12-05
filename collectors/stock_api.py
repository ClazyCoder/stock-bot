import yfinance as yf
import pandas as pd

main_sectors = {
    'technology': '기술 💻',
    'financial-services': '금융 💰',
    'healthcare': '헬스케어 🏥',
    'consumer-cyclical': '소비재 🛍️'
}


class StockDataCollector:
    def __init__(self):
        self.main_leaders = self.market_leaders()
        self.all_tickers = [ticker for tickers in self.main_leaders.values()
                            for ticker in tickers]
        self.data = yf.download(
            self.all_tickers, period="5d", group_by='ticker')
        self.data = self.data.stack(level=0)
        self.data.index.names = ['Date', 'Ticker']

    def market_leaders(self):
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

    def save_data(self):
        self.data.to_csv('stock_data.csv')
        print("Stock data saved to stock_data.csv")

    def load_data(self):
        self.data = pd.read_csv('stock_data.csv', header=[
                                0, 1], index_col=[0, 1])
        self.data.index.names = ['Date', 'Ticker']
        return self.data
