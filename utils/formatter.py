from schemas.llm import StockPriceLLMContext
from typing import List
import csv
from io import StringIO


def to_csv_string(stock_data_list: List[StockPriceLLMContext]) -> str:
    """
    Convert a list of StockPriceLLMContext objects to a CSV string.
    Properly escapes field values that may contain commas, quotes, or newlines.
    Args:
        stock_data_list (List[StockPriceLLMContext]): The list of StockPriceLLMContext objects to convert.
    Returns:
        str: The CSV string with properly escaped values.
    """
    if not stock_data_list:
        return ""

    with StringIO() as output:
        fieldnames = list(stock_data_list[0].model_dump().keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)

        writer.writeheader()
        for data in stock_data_list:
            writer.writerow(data.model_dump())

        return output.getvalue()
