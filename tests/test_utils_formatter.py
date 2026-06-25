from conftest import make_ohlcv_records
from schemas.llm import StockPriceLLMContext
from utils.formatter import to_csv_string


def test_to_csv_string_empty_returns_empty():
    assert to_csv_string([]) == ""


def test_to_csv_string_single_item_has_header_and_row():
    records: list[StockPriceLLMContext] = make_ohlcv_records(1)
    result = to_csv_string(records)

    assert "date" in result
    assert len(result.split("\n")) == 3


def test_to_csv_string_multiple_items_correct_count():
    result = to_csv_string(make_ohlcv_records(3))

    assert len(result.split("\n")) == 5
