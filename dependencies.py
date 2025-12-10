from fastapi import Depends
from collectors.stock_api import StockDataCollector
from services.stock_data_service import StockDataService
from sqlalchemy.ext.asyncio import AsyncSession
from interfaces import IStockProvider
from db.repositories.user_repository import UserRepository
from db.repositories.stock_repository import StockRepository
from db.connection import AsyncSessionLocal
from services.user_data_service import UserDataService
from typing import Generator

stock_repository: StockRepository = StockRepository(
    session=AsyncSessionLocal())
stock_data_collector: IStockProvider = StockDataCollector()


async def get_db_session() -> Generator[AsyncSession, None, None]:
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_stock_repository() -> StockRepository:
    return stock_repository


def get_collector() -> IStockProvider:
    return stock_data_collector


def get_stock_service(
    stock_repository: StockRepository = Depends(get_stock_repository),
    collector: IStockProvider = Depends(get_collector)
) -> StockDataService:
    return StockDataService(collector=collector, stock_repository=stock_repository)


user_repository: UserRepository = UserRepository(session=AsyncSessionLocal())


def get_user_repository() -> UserRepository:
    return user_repository


def get_user_data_service(user_repository: UserRepository = Depends(get_user_repository)) -> UserDataService:
    return UserDataService(user_repository=user_repository)
