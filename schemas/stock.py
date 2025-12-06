from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class StockPrice(BaseModel):
    """
    Stock Chat Data for OHLCV
    """
    date: datetime
    close: float = Field(..., description="Close Price")
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: int = Field(0, description="Volume")


class CompanyInfo(BaseModel):
    """
    Company Fundamental Information
    """
    ticker: str
    name: str
    sector: str
    industry: Optional[str] = None
    market_cap: Optional[int] = None


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
