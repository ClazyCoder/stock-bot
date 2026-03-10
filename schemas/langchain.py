from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, model_validator


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
    value: Optional[float] = Field(
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

    @model_validator(mode="after")
    def compute_derived_metrics(self) -> "FactExtractionResult":
        def safe_div(a, b):
            if a and b and a.value and b.value and b.value != 0:
                return ExtractedMetric(
                    value=round(a.value / b.value * 100, 2),
                    unit="Percentage",
                    period=a.period,
                    fiscal_year=a.fiscal_year,
                    source_text="Derived: computed from extracted values"
                )
            return None

        if not self.gross_margin and self.gross_profit and self.revenue:
            self.gross_margin = safe_div(self.gross_profit, self.revenue)
        if not self.operating_margin and self.operating_income and self.revenue:
            self.operating_margin = safe_div(
                self.operating_income, self.revenue)
        if not self.net_margin and self.net_income and self.revenue:
            self.net_margin = safe_div(self.net_income, self.revenue)
        if not self.capex and self.operating_cash_flow and self.free_cash_flow:
            ocf = self.operating_cash_flow.value
            fcf = self.free_cash_flow.value
            if ocf and fcf:
                self.capex = ExtractedMetric(
                    value=round(ocf - fcf, 2),
                    unit="USD",
                    period=self.operating_cash_flow.period,
                    fiscal_year=self.operating_cash_flow.fiscal_year,
                    source_text="Derived: OCF minus FCF"
                )
        return self
