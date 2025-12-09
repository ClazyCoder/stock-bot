# interfaces/__init__.py
from .db_interface import IDBModule
from .stock_interface import IStockProvider
from .bot_interface import IBot

__all__ = ['IDBModule', 'IStockProvider', 'IBot']
