from fastapi import Depends
from db.provider import StockDBProvider
from collectors.stock_api import StockDataCollector
from services.stock_data_service import StockDataService
from sqlalchemy.orm import Session
from interfaces import IStockDBModule, IStockProvider
from db.connection import SessionLocal
from typing import Generator

stock_db_provider: IStockDBModule = StockDBProvider(session_local=SessionLocal)
stock_data_collector: IStockProvider = StockDataCollector()


async def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_stock_db_provider() -> IStockDBModule:
    return stock_db_provider


def get_collector() -> IStockProvider:
    return stock_data_collector


def get_stock_service(
    db_module: IStockDBModule = Depends(get_stock_db_provider),
    collector: IStockProvider = Depends(get_collector)
) -> StockDataService:
    return StockDataService(collector=collector, db=db_module)
