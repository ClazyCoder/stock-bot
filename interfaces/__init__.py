# interfaces/__init__.py
from .db_interface import IStockDBModule
from .stock_interface import IStockProvider

__all__ = ['IStockDBModule', 'IStockProvider']
