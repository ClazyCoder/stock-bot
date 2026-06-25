from schemas.langchain import (
    ExtractedMetric,
    FactExtractionResult,
    clean_value,
    normalize_fact_extraction,
)


def test_clean_value_float_passthrough():
    assert clean_value(1.5) == 1.5


def test_clean_value_int_to_float():
    assert clean_value(42) == 42.0


def test_clean_value_none_returns_none():
    assert clean_value(None) is None


def test_clean_value_string_with_symbols():
    assert clean_value("$1,234.56") == 1234.56


def test_clean_value_nonnumeric_returns_none():
    assert clean_value("N/A") is None


def test_normalize_converts_usd_billion():
    result = normalize_fact_extraction(
        FactExtractionResult(
            revenue=ExtractedMetric(value=5_000_000_000.0, unit="USD")
        )
    )

    assert result.revenue.value == 5.0
    assert result.revenue.unit == "USD_Billion"


def test_normalize_usd_below_billion_unchanged():
    result = normalize_fact_extraction(
        FactExtractionResult(
            revenue=ExtractedMetric(value=500_000_000.0, unit="USD")
        )
    )

    assert result.revenue.value == 500_000_000.0
    assert result.revenue.unit == "USD"


def test_normalize_none_field_no_error():
    result = normalize_fact_extraction(FactExtractionResult())

    assert isinstance(result, FactExtractionResult)


def test_normalize_string_value_cleaned_and_converted():
    result = normalize_fact_extraction(
        FactExtractionResult(
            net_income=ExtractedMetric(value="2,500,000,000", unit="USD")
        )
    )

    assert result.net_income.value == 2.5
    assert result.net_income.unit == "USD_Billion"


def test_normalize_non_usd_unit_unchanged():
    result = normalize_fact_extraction(
        FactExtractionResult(
            gross_margin=ExtractedMetric(value=0.71, unit="Percentage")
        )
    )

    assert result.gross_margin.value == 0.71
    assert result.gross_margin.unit == "Percentage"
