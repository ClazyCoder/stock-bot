# schemas/llm.py
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


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


class StockReport(BaseModel):
    """
    LLM Context for stock report. Used for optimizing the LLM context.
    """
    id: int = Field(..., description="ID of the stock report")
    ticker: str = Field(..., description="Ticker of the stock")
    report: str = Field(..., description="Report of the stock")
    created_at: datetime = Field(..., description="Created at")
