from schemas.llm import StockPriceLLMContext
from typing import List


def to_csv_string(stock_data_list: List[StockPriceLLMContext]) -> str:
    """
    Convert a list of StockPriceLLMContext objects to a CSV string.
    Args:
        stock_data_list (List[StockPriceLLMContext]): The list of StockPriceLLMContext objects to convert.
    Returns:
        str: The CSV string.
    """
    if not stock_data_list:
        return ""

    header = ",".join(stock_data_list[0].model_dump().keys())

    rows = []
    for data in stock_data_list:
        row = ",".join(str(v) for v in data.model_dump().values())
        rows.append(row)

    return f"{header}\n" + "\n".join(rows)
