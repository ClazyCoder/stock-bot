from fastapi import Depends
from db.repositories.stock_repository import StockRepository
from collectors.stock_api import StockDataCollector
from services.stock_data_service import StockDataService
from sqlalchemy.orm import Session
from interfaces import IDBModule, IStockProvider
from db.connection import SessionLocal
from typing import Generator

stock_db_module: IDBModule = StockRepository(session_local=SessionLocal)
stock_data_collector: IStockProvider = StockDataCollector()


async def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_db_module() -> IDBModule:
    return stock_db_module


def get_collector() -> IStockProvider:
    return stock_data_collector


def get_stock_service(
    db_module: IDBModule = Depends(get_db_module),
    collector: IStockProvider = Depends(get_collector)
) -> StockDataService:
    return StockDataService(collector=collector, db=db_module)
