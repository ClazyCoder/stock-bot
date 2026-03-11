from __future__ import annotations

from typing import List, Literal, Optional, Union
from pydantic import BaseModel, Field
import re

UnitType = Literal[
    "USD",
    "USD_Million",
    "USD_Billion",
    "Percentage",
    "Ratio",
    "Count",
    "Text",
]

PeriodType = Literal[
    "FY",
    "Q1",
    "Q2",
    "Q3",
    "Q4",
    "TTM",
    "PointInTime",
    "Unknown",
]

FilingType = Literal[
    "10-K",
    "10-Q",
    "8-K",
    "EarningsRelease",
    "InvestorPresentation",
    "Other",
]


class ExtractedMetric(BaseModel):
    """Canonical representation of a single extracted financial or market metric."""
    value: Optional[Union[float, str]] = Field(
        default=None,
        description="Numeric value of the metric. Null if unavailable or non-numeric."
    )
    unit: Optional[UnitType] = Field(
        default=None,
        description="Normalized unit for the metric."
    )
    period: PeriodType = Field(
        default="Unknown",
        description="Reporting period associated with the metric."
    )
    fiscal_year: Optional[int] = Field(
        default=None,
        description="Fiscal year associated with this metric, if known."
    )
    as_of_date: Optional[str] = Field(
        default=None,
        description="Date associated with this metric in YYYY-MM-DD format if available."
    )
    source_text: Optional[str] = Field(
        default=None,
        description="Short source snippet directly supporting the metric."
    )


class TextMetric(BaseModel):
    """For non-numeric facts that still need source traceability."""
    value: Optional[str] = Field(
        default=None,
        description="Textual extracted value."
    )
    source_text: Optional[str] = Field(
        default=None,
        description="Short source snippet directly supporting the value."
    )
    warning: Optional[str] = Field(
        default=None,
        description="Warning about ambiguity or inconsistency."
    )


class RiskFlag(BaseModel):
    """Qualitative risk flag extracted from source documents."""
    label: str = Field(description="Short normalized risk label.")
    detail: Optional[str] = Field(
        default=None,
        description="Short explanation of the risk."
    )
    source_text: Optional[str] = Field(
        default=None,
        description="Supporting source snippet."
    )


class FactExtractionResult(BaseModel):
    company_name: Optional[str] = None
    ticker: Optional[str] = None
    filing_type: Optional[FilingType] = None
    fiscal_period: Optional[PeriodType] = None
    fiscal_year: Optional[int] = None
    report_date: Optional[str] = None

    revenue: Optional[ExtractedMetric] = None
    revenue_growth_yoy: Optional[ExtractedMetric] = None
    gross_margin: Optional[ExtractedMetric] = None
    net_income: Optional[ExtractedMetric] = None
    operating_cash_flow: Optional[ExtractedMetric] = None
    free_cash_flow: Optional[ExtractedMetric] = None
    cash_and_equivalents: Optional[ExtractedMetric] = None
    total_debt: Optional[ExtractedMetric] = None
    r_and_d_expense: Optional[ExtractedMetric] = None
    inventory: Optional[ExtractedMetric] = None
    inventory_change: Optional[ExtractedMetric] = None
    share_repurchases: Optional[ExtractedMetric] = None

    major_risk_flags: List[RiskFlag] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


def clean_value(val: Union[float, str]) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, (float, int)):
        return float(val)

    clean_str = re.sub(r'[^\d.-]', '', str(val))
    try:
        return float(clean_str)
    except ValueError:
        return None


def normalize_fact_extraction(fact: FactExtractionResult) -> FactExtractionResult:
    fields_to_normalize = [
        'revenue', 'net_income', 'operating_cash_flow',
        'free_cash_flow', 'total_debt', 'inventory',
        'r_and_d_expense', 'share_repurchases', 'cash_and_equivalents', 'inventory_change'
    ]

    for field_name in fields_to_normalize:
        field = getattr(fact, field_name)
        if field and field.value is not None:
            field.value = clean_value(field.value)
            if field.value and field.unit == "USD":
                if field.value >= 1_000_000_000:
                    field.value = round(field.value / 1_000_000_000, 3)
                    field.unit = "USD_Billion"

    return fact
