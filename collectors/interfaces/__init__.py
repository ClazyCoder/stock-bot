# collectors/interfaces/__init__.py
from .stock_interface import IStockProvider
from .news_interface import INewsProvider

__all__ = ['IStockProvider', 'INewsProvider']

