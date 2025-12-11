from pydantic import BaseModel, Field
from datetime import datetime


class StockSymbol(BaseModel):
    """
    Schema representing a stock ticker symbol for use in API requests and responses.
    """
    ticker: str = Field(..., description="Ticker")


class StockRequest(StockSymbol):
    """
    Schema for requests involving a stock ticker symbol, such as fetching price or analysis data.
    """
    period: str = Field(default="1d", description="Period")
    """
    Period for the stock price data.
    Args:
        period: str - The period of the stock to fetch the price for.
        Valid periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    """


class StockPrice(StockSymbol):
    """
    Stock Chart Data (OHLCV)
    """
    trade_date: datetime = Field(
        default_factory=datetime.now, description="Trade Date")
    close_price: float = Field(..., description="Close Price")
    open_price: float = Field(..., description="Open Price")
    high_price: float = Field(..., description="High Price")
    low_price: float = Field(..., description="Low Price")
    volume: int = Field(0, description="Volume")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Created At")
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Updated At")


class AnalysisReport(BaseModel):
    """
    Final Result Data Transfer Object
    """
    ticker: str
    created_at: datetime = Field(default_factory=datetime.now)

    current_price: float
    company_name: str

    summary: str
    sentiment_score: float  # 0.8 (Positive / Neutral / Negative)
    recommendation: str  # "BUY" / "HOLD" / "SELL"
