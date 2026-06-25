from datetime import date

import pytest
from fastapi import HTTPException

from utils.common import (
    chunk_list,
    get_today_in_business_timezone,
    validate_query,
    validate_ticker,
)


def test_chunk_list_uneven_split():
    assert list(chunk_list(list(range(5)), 2)) == [[0, 1], [2, 3], [4]]


def test_chunk_list_exact_division():
    assert list(chunk_list(list(range(4)), 2)) == [[0, 1], [2, 3]]


def test_chunk_list_n_equals_one():
    assert list(chunk_list([1, 2, 3], 1)) == [[1], [2], [3]]


def test_chunk_list_n_larger_than_list():
    assert list(chunk_list([1, 2], 10)) == [[1, 2]]


def test_chunk_list_empty_input():
    assert list(chunk_list([], 3)) == []


def test_chunk_list_n_zero_raises():
    with pytest.raises(ValueError):
        list(chunk_list([1], 0))


def test_chunk_list_negative_n_raises():
    with pytest.raises(ValueError):
        list(chunk_list([1], -1))


def test_validate_ticker_valid_symbols():
    for symbol in ["AAPL", "BRK.B", "BRK-B", "TEST_1"]:
        validate_ticker(symbol)


def test_validate_ticker_special_char_raises():
    with pytest.raises(HTTPException) as exc:
        validate_ticker("AAPL!")
    assert exc.value.status_code == 400


def test_validate_ticker_empty_raises():
    with pytest.raises(HTTPException) as exc:
        validate_ticker("")
    assert exc.value.status_code == 400


def test_validate_ticker_space_raises():
    with pytest.raises(HTTPException) as exc:
        validate_ticker(" AAPL")
    assert exc.value.status_code == 400


def test_validate_query_valid():
    validate_query("buy AAPL today")


def test_validate_query_empty_raises():
    with pytest.raises(HTTPException) as exc:
        validate_query("")
    assert exc.value.status_code == 400


def test_validate_query_whitespace_only_raises():
    with pytest.raises(HTTPException) as exc:
        validate_query("   ")
    assert exc.value.status_code == 400


def test_returns_date_instance():
    assert isinstance(get_today_in_business_timezone(), date)
