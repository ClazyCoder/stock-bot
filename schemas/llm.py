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

    @field_validator('close', 'open', 'high', 'low')
    @classmethod
    def round_float(cls, v: float) -> float:
        return round(v, 2)

    @field_validator('date', mode='before')
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, datetime):
            return v.strftime('%Y-%m-%d')
        return str(v).split("T")[0]

    class Config:
        from_attributes = True
        populate_by_name = True
