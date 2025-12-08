from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class StockPrice(BaseModel):
    """
    Stock Chat Data for OHLCV
    """
    ticker: str = Field(..., description="Ticker")
    date: datetime = Field(default_factory=datetime.now, description="Date")
    trade_date: datetime = Field(
        default_factory=datetime.now, description="Trade Date")
    close_price: float = Field(..., description="Close Price")
    open_price: float = Field(..., description="Open Price")
    high_price: float = Field(..., description="High Price")
    low_price: float = Field(..., description="Low Price")
    volume: int = Field(0, description="Volume")


class AnalysisReport(BaseModel):
    """
    Final Result DTO
    """
    ticker: str
    created_at: datetime = Field(default_factory=datetime.now)

    current_price: float
    company_name: str

    summary: str
    sentiment_score: float  # 0.8 (Positive / Neutral / Negative)
    recommendation: str  # "BUY" / "HOLD" / "SELL"
