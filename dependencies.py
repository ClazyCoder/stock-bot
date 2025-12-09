from fastapi import Depends
from db.db_module import SQLDBModule
from collectors.stock_api import StockDataCollector
from services.stock_data_service import StockDataService
from sqlalchemy.orm import Session
from interfaces import IDBModule, IStockProvider


sql_db_module = SQLDBModule()
stock_data_collector = StockDataCollector()


async def get_db_session() -> Session:
    session = await sql_db_module.get_session()
    try:
        yield session
    finally:
        await session.close()


def get_db_module() -> IDBModule:
    return sql_db_module


def get_collector() -> IStockProvider:
    return stock_data_collector


def get_stock_service(
    db_module: IDBModule = Depends(get_db_module),
    collector: IStockProvider = Depends(get_collector)
) -> StockDataService:
    return StockDataService(collector=collector, db=db_module)
