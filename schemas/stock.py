from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, List


class StockSymbol(BaseModel):
    """
    Schema representing a stock ticker symbol for use in API requests and responses.
    """
    ticker: str = Field(..., description="Ticker")


class StockRequest(StockSymbol):
    """
    Schema for requests involving a stock ticker symbol, such as fetching price or analysis data.
    """
    period: Literal["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"] = Field(
        default="1d",
        description="Period for the stock price data. Valid periods: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max"
    )


class StockPriceCreate(StockSymbol):
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


class StockPriceResponse(StockPriceCreate):
    """
    Stock Chart Data (OHLCV) Response
    """
    id: int = Field(..., description="ID")

    class Config:
        from_attributes = True


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


class StockNewsChunkCreate(StockSymbol):
    """
    Stock News Chunk Data (text only, embedding is generated in repository)
    Note: Title is stored in the parent StockNews model, not in chunks.
    """
    content: str = Field(..., description="Content")


class StockNewsChunkResponse(StockNewsChunkCreate):
    """
    Stock News Chunk Data Response including the embedding vector generated
    from the chunk content in the repository layer (not provided in the
    create request).
    """
    id: int = Field(..., description="ID")
    embedding: List[float] = Field(
        ..., description="Embedding vector generated from the chunk content; not supplied in create requests.")

    class Config:
        from_attributes = True


class StockNewsCreate(StockSymbol):
    """
    Stock News Data
    """
    title: str = Field(..., description="Title")
    full_content: str = Field(..., description="Full Content")
    published_at: datetime = Field(..., description="Published at")
    url: str = Field(..., description="URL")


class StockNewsResponse(StockNewsCreate):
    """
    Stock News Data Response
    """
    id: int = Field(..., description="ID")

    class Config:
        from_attributes = True
