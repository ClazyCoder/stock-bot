# schemas/llm.py
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date
from utils.common import get_today_in_business_timezone


class StockPriceLLMContext(BaseModel):
    """
    LLM Context for stock price data. Used for optimizing the LLM context.
    """
    date: str = Field(..., description="YYYY-MM-DD",
                      validation_alias="trade_date")
    close: float = Field(..., description="Close price",
                         validation_alias="close_price")
    open: float = Field(..., description="Open price",
                        validation_alias="open_price")
    high: float = Field(..., description="High price",
                        validation_alias="high_price")
    low: float = Field(..., description="Low price",
                       validation_alias="low_price")
    vol: int = Field(..., alias="volume", validation_alias="volume")

    # Round float to 2 decimal places for token optimization
    @field_validator('close', 'open', 'high', 'low')
    @classmethod
    def round_float(cls, v: float) -> float:
        return round(v, 2)

    # Parse date to YYYY-MM-DD format for token optimization
    @field_validator('date', mode='before')
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, datetime):
            return v.strftime('%Y-%m-%d')
        return str(v).split("T")[0]

    class Config:
        from_attributes = True
        populate_by_name = True


class StockNewsLLMContext(BaseModel):
    """
    LLM Context for news data. Used for optimizing the LLM context.
    """
    title: str = Field(..., description="Title of the news")
    content: str = Field(..., description="Content of the news")
    published_at: datetime = Field(..., description="Published at")


class StockReportCreate(BaseModel):
    """
    Stock Report Data for creation
    Note: created_at is a date (not datetime) to ensure one report per ticker per day.
    """
    ticker: str = Field(..., description="Ticker of the stock")
    report: str = Field(..., description="Report of the stock")
    created_at: date = Field(
        default_factory=get_today_in_business_timezone, 
        description="Created at (date only, ensures one report per day in business timezone)")
    
    @field_validator('created_at', mode='before')
    @classmethod
    def normalize_to_date(cls, v):
        """Convert datetime to date if needed."""
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, str):
            # Try to parse as datetime first, then extract date
            try:
                dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
                return dt.date()
            except ValueError:
                # Try date format
                return datetime.strptime(v, '%Y-%m-%d').date()
        return v


class StockReportResponse(StockReportCreate):
    """
    Stock Report Data Response
    """
    id: int = Field(..., description="ID of the stock report")

    class Config:
        from_attributes = True
