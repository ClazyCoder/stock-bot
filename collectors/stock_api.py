import yfinance as yf
import asyncio
from interfaces import IStockProvider
from schemas import StockPrice

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

    async def fetch_stock_price(self, ticker: str) -> StockPrice:
        """
        Fetch stock price data asynchronously.
        Runs blocking yf.download() in a thread pool to avoid blocking the event loop.
        """
        # Run blocking I/O in a thread pool to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None,
                                          # auto_adjust=False to avoid auto-adjusting the data
                                          lambda: yf.download(
                                              ticker, period="1d", auto_adjust=False)
                                          )

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
            close_price=float(data['Close'].iloc[0].item()),
            open_price=float(data['Open'].iloc[0].item()),
            high_price=float(data['High'].iloc[0].item()),
            low_price=float(data['Low'].iloc[0].item()),
            volume=int(data['Volume'].iloc[0].item())
        )
