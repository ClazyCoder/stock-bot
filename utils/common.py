from typing import List, Generator, TypeVar
from fastapi import HTTPException
import logging
import re
import os
from datetime import datetime, date
from zoneinfo import ZoneInfo

T = TypeVar('T')

logger = logging.getLogger(__name__)

# Business timezone for stock reports (default: Asia/Seoul/KST)
# Can be overridden via BUSINESS_TIMEZONE environment variable
BUSINESS_TIMEZONE = ZoneInfo(os.getenv('BUSINESS_TIMEZONE', 'Asia/Seoul'))


def get_today_in_business_timezone() -> date:
    """
    Get today's date in the business timezone (default: Asia/Seoul).
    This ensures consistent date determination regardless of server location.

    Returns:
        date: Today's date in the business timezone
    """
    return datetime.now(BUSINESS_TIMEZONE).date()


def get_now_in_business_timezone() -> datetime:
    """
    Get current datetime in the business timezone (default: Asia/Seoul).

    Returns:
        datetime: Current datetime in the business timezone
    """
    return datetime.now(BUSINESS_TIMEZONE)


def chunk_list(lst: List[T], n: int) -> Generator[List[T], None, None]:
    """
    Chunk a list into smaller lists of size n.
    Args:
        lst (List[T]): The list to chunk.
        n (int): The size of the chunks. Must be greater than 0.
    Returns:
        Generator[List[T], None, None]: A generator of lists.
    Raises:
        ValueError: If n is less than or equal to 0.
    """
    if n <= 0:
        raise ValueError(f"Chunk size 'n' must be greater than 0, got {n}")
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def validate_ticker(ticker: str) -> None:
    """
    Validates that the ticker contains only allowed characters (alphanumeric, dots, hyphens, underscores).
    Raises HTTPException with 400 status code if validation fails.

    Args:
        ticker: The ticker symbol to validate

    Raises:
        HTTPException: If the ticker format is invalid
    """
    if not ticker or not isinstance(ticker, str):
        raise HTTPException(
            status_code=400,
            detail="Ticker must be a non-empty string"
        )
    if not re.match(r'^[a-zA-Z0-9._-]+$', ticker):
        logger.warning(f"Invalid ticker format '{ticker}' provided")
        raise HTTPException(
            status_code=400,
            detail="Invalid ticker format. Ticker must contain only alphanumeric characters and common separators (., _, -)"
        )


def validate_query(query: str) -> None:
    """
    Validates that the query string is not empty or whitespace-only.
    Raises HTTPException with 400 status code if validation fails.

    Args:
        query: The query string to validate

    Raises:
        HTTPException: If the query is empty or invalid
    """
    if not query or not isinstance(query, str):
        raise HTTPException(
            status_code=400,
            detail="Query must be a non-empty string"
        )
    if not query.strip():
        logger.warning("Empty or whitespace-only query provided")
        raise HTTPException(
            status_code=400,
            detail="Query must not be empty or contain only whitespace"
        )
