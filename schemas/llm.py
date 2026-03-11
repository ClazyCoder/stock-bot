# schemas/llm.py
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date
from utils.common import get_today_in_business_timezone
from typing import Optional, Iterable
import pandas as pd
from typing import Any, Mapping


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

    # Normalize price fields to 2 decimal places
    @field_validator('close', 'open', 'high', 'low')
    @classmethod
    def round_float(cls, v: float) -> float:
        return round(v, 2)

    # Normalize date to YYYY-MM-DD string format
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
                try:
                    return datetime.strptime(v, '%Y-%m-%d').date()
                except ValueError:
                    raise ValueError(
                        f"Invalid date string format: '{v}'. Expected ISO format (YYYY-MM-DDTHH:MM:SS) or date format (YYYY-MM-DD)"
                    )
        return v


class StockReportResponse(StockReportCreate):
    """
    Stock Report Data Response
    """
    id: int = Field(..., description="ID of the stock report")

    class Config:
        from_attributes = True


class MarketSummary(BaseModel):
    as_of_date: Optional[str] = None
    current_price: Optional[float] = None

    # Price return / momentum
    return_1d_pct: Optional[float] = None
    return_5d_pct: Optional[float] = None
    return_20d_pct: Optional[float] = None
    return_60d_pct: Optional[float] = None

    # Volume
    volume_today: Optional[int] = None
    volume_avg_20d: Optional[float] = None
    volume_ratio_20d: Optional[float] = None

    # Moving averages / trend
    ma_20: Optional[float] = None
    ma_50: Optional[float] = None
    ma_200: Optional[float] = None

    price_vs_ma20: Optional[str] = None
    price_vs_ma50: Optional[str] = None
    price_vs_ma200: Optional[str] = None

    # Technicals
    rsi_14: Optional[float] = None

    # 52-week positioning
    high_52w: Optional[float] = None
    low_52w: Optional[float] = None
    distance_from_52w_high_pct: Optional[float] = None
    distance_from_52w_low_pct: Optional[float] = None

    # Valuation / market metrics from yfinance info
    trailing_pe: Optional[float] = None
    forward_pe: Optional[float] = None
    price_to_book: Optional[float] = None
    price_to_sales_ttm: Optional[float] = None
    peg_ratio: Optional[float] = None

    market_cap: Optional[int] = None
    enterprise_value: Optional[int] = None

    beta: Optional[float] = None

    # Ownership / short interest / sentiment
    short_ratio: Optional[float] = None
    short_percent_of_float: Optional[float] = None
    institutional_ownership_pct: Optional[float] = None
    insider_ownership_pct: Optional[float] = None

    # Profitability / growth / health from yfinance info
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    profit_margin: Optional[float] = None

    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    earnings_quarterly_growth: Optional[float] = None

    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None

    analyst_target_mean: Optional[float] = None
    analyst_target_high: Optional[float] = None
    analyst_target_low: Optional[float] = None
    analyst_recommendation: Optional[str] = None
    number_of_analysts: Optional[int] = None

    return_on_equity: Optional[float] = None
    return_on_assets: Optional[float] = None
    enterprise_to_ebitda: Optional[float] = None

    warning: Optional[str] = None


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, adjust=False,
                        min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False,
                        min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def classify_vs_ma(price: float, ma: Optional[float], tolerance: float = 0.01) -> str:
    if ma is None or pd.isna(ma):
        return "unknown"
    if price > ma * (1 + tolerance):
        return "above"
    if price < ma * (1 - tolerance):
        return "below"
    return "near"


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _pct_from_ratio(value: Any) -> Optional[float]:
    """
    yfinance info fields like grossMargins=0.71068, heldPercentInstitutions=0.69701
    are often ratio-form. Convert them to percentage for easier LLM consumption.
    """
    v = _safe_float(value)
    if v is None:
        return None
    return v * 100.0


def build_market_summary(
    records: Iterable[object],
    info: Optional[Mapping[str, Any]] = None,
) -> MarketSummary:
    rows = [
        {
            "trade_date": r.date,
            "close_price": r.close,
            "open_price": r.open,
            "high_price": r.high,
            "low_price": r.low,
            "volume": r.vol,
        }
        for r in records
    ]

    if not rows:
        return MarketSummary(warning="No OHLCV records provided.")

    df = pd.DataFrame(rows).sort_values("trade_date").reset_index(drop=True)

    close = df["close_price"]
    high = df["high_price"]
    low = df["low_price"]
    volume = df["volume"]

    df["ma_20"] = close.rolling(20).mean()
    df["ma_50"] = close.rolling(50).mean()
    df["ma_200"] = close.rolling(200).mean()
    df["rsi_14"] = compute_rsi(close, period=14)

    last = df.iloc[-1]
    current_price = float(last["close_price"])
    volume_today = int(last["volume"])

    def pct_return(days: int) -> Optional[float]:
        if len(df) <= days:
            return None
        base = float(df.iloc[-(days + 1)]["close_price"])
        if base == 0:
            return None
        return (current_price / base - 1.0) * 100.0

    volume_avg_20d = float(volume.tail(20).mean()) if len(df) >= 20 else None
    high_52w = float(high.tail(252).max()) if len(df) >= 1 else None
    low_52w = float(low.tail(252).min()) if len(df) >= 1 else None

    distance_from_52w_high_pct = None
    if high_52w is not None and pd.notna(high_52w) and high_52w != 0:
        distance_from_52w_high_pct = (current_price / high_52w - 1.0) * 100.0

    distance_from_52w_low_pct = None
    if low_52w is not None and pd.notna(low_52w) and low_52w != 0:
        distance_from_52w_low_pct = (current_price / low_52w - 1.0) * 100.0

    ma_20 = float(last["ma_20"]) if pd.notna(last["ma_20"]) else None
    ma_50 = float(last["ma_50"]) if pd.notna(last["ma_50"]) else None
    ma_200 = float(last["ma_200"]) if pd.notna(last["ma_200"]) else None
    rsi_14 = float(last["rsi_14"]) if pd.notna(last["rsi_14"]) else None

    info = info or {}

    # Use info currentPrice if available; otherwise use OHLCV latest close.
    info_current_price = _safe_float(info.get("currentPrice"))
    final_price = info_current_price if info_current_price is not None else current_price

    # If currentPrice from info differs from OHLCV last close, we still keep MA/RSI from OHLCV,
    # but trend classification / distance metrics use final_price to reflect the latest quote.
    if final_price != current_price:
        if high_52w and high_52w != 0:
            distance_from_52w_high_pct = (final_price / high_52w - 1.0) * 100.0
        if low_52w and low_52w != 0:
            distance_from_52w_low_pct = (final_price / low_52w - 1.0) * 100.0

    return MarketSummary(
        as_of_date=pd.to_datetime(last["trade_date"]).strftime("%Y-%m-%d"),
        current_price=final_price,

        # OHLCV-derived
        return_1d_pct=pct_return(1),
        return_5d_pct=pct_return(5),
        return_20d_pct=pct_return(20),
        return_60d_pct=pct_return(60),

        volume_today=volume_today,
        volume_avg_20d=volume_avg_20d,
        volume_ratio_20d=(
            volume_today / volume_avg_20d) if volume_avg_20d else None,

        ma_20=ma_20,
        ma_50=ma_50,
        ma_200=ma_200,

        price_vs_ma20=classify_vs_ma(final_price, ma_20),
        price_vs_ma50=classify_vs_ma(final_price, ma_50),
        price_vs_ma200=classify_vs_ma(final_price, ma_200),

        rsi_14=rsi_14,

        high_52w=high_52w,
        low_52w=low_52w,
        distance_from_52w_high_pct=distance_from_52w_high_pct,
        distance_from_52w_low_pct=distance_from_52w_low_pct,

        # yfinance info-derived valuation / market metrics
        trailing_pe=_safe_float(info.get("trailingPE")),
        forward_pe=_safe_float(info.get("forwardPE")),
        price_to_book=_safe_float(info.get("priceToBook")),
        price_to_sales_ttm=_safe_float(
            info.get("priceToSalesTrailing12Months")),
        peg_ratio=_safe_float(info.get("trailingPegRatio")),

        market_cap=_safe_int(info.get("marketCap")),
        enterprise_value=_safe_int(info.get("enterpriseValue")),

        beta=_safe_float(info.get("beta")),

        short_ratio=_safe_float(info.get("shortRatio")),
        short_percent_of_float=_pct_from_ratio(
            info.get("shortPercentOfFloat")),
        institutional_ownership_pct=_pct_from_ratio(
            info.get("heldPercentInstitutions")),
        insider_ownership_pct=_pct_from_ratio(info.get("heldPercentInsiders")),

        # profitability / growth / health
        gross_margin=_pct_from_ratio(info.get("grossMargins")),
        operating_margin=_pct_from_ratio(info.get("operatingMargins")),
        profit_margin=_pct_from_ratio(info.get("profitMargins")),

        revenue_growth=_pct_from_ratio(info.get("revenueGrowth")),
        earnings_growth=_pct_from_ratio(info.get("earningsGrowth")),
        earnings_quarterly_growth=_pct_from_ratio(
            info.get("earningsQuarterlyGrowth")),

        debt_to_equity=_safe_float(info.get("debtToEquity")),
        current_ratio=_safe_float(info.get("currentRatio")),
        quick_ratio=_safe_float(info.get("quickRatio")),
        analyst_target_mean=_safe_float(info.get("targetMeanPrice")),
        analyst_target_high=_safe_float(info.get("targetHighPrice")),
        analyst_target_low=_safe_float(info.get("targetLowPrice")),
        analyst_recommendation=info.get("recommendationKey"),
        number_of_analysts=_safe_int(info.get("numberOfAnalystOpinions")),

        return_on_equity=_safe_float(info.get("returnOnEquity")),
        return_on_assets=_safe_float(info.get("returnOnAssets")),
        enterprise_to_ebitda=_safe_float(info.get("enterpriseToEbitda")),

        warning=None,
    )
