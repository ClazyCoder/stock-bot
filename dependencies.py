# dependencies.py
from collectors.stock_api import StockDataCollector
from services.stock_data_service import StockDataService
from sqlalchemy.ext.asyncio import AsyncSession
from interfaces import IStockProvider
from db.repositories.user_repository import UserRepository
from db.repositories.stock_repository import StockRepository
from db.connection import AsyncSessionLocal
from services.user_data_service import UserDataService
from typing import Generator
from langchain_mcp_adapters.client import MultiServerMCPClient
import os
import dotenv
dotenv.load_dotenv()

# Singleton instances
_stock_repository: StockRepository | None = None
_user_repository: UserRepository | None = None
_stock_data_collector: IStockProvider | None = None
_user_service: UserDataService | None = None
_stock_service: StockDataService | None = None
_mcp_client: MultiServerMCPClient | None = None


async def get_mcp_client() -> MultiServerMCPClient:
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MultiServerMCPClient(
            {
                "edgartools": {
                    "transport": "stdio",
                    "command": "python",
                    "args": ["-m", "edgar.ai"],
                    "env": {
                        "EDGAR_IDENTITY": os.getenv("EDGAR_IDENTITY", "Your Name your.email@example.com")
                    }
                }
            }
        )
    return _mcp_client


async def get_db_session() -> Generator[AsyncSession, None, None]:
    """Create and close a session for each FastAPI request."""
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()


def get_stock_repository() -> StockRepository:
    """Return singleton StockRepository (creates session in each method using SessionFactory)."""
    global _stock_repository
    if _stock_repository is None:
        _stock_repository = StockRepository(session_factory=AsyncSessionLocal)
    return _stock_repository


def get_user_repository() -> UserRepository:
    """Return singleton UserRepository (creates session in each method using SessionFactory)."""
    global _user_repository
    if _user_repository is None:
        _user_repository = UserRepository(session_factory=AsyncSessionLocal)
    return _user_repository


def get_collector() -> IStockProvider:
    """Return singleton Collector."""
    global _stock_data_collector
    if _stock_data_collector is None:
        _stock_data_collector = StockDataCollector()
    return _stock_data_collector


def get_stock_service() -> StockDataService:
    """Return singleton StockDataService."""
    global _stock_service
    if _stock_service is None:
        _stock_service = StockDataService(
            collector=get_collector(),
            stock_repository=get_stock_repository()
        )
    return _stock_service


def get_user_data_service() -> UserDataService:
    """Return singleton UserDataService."""
    global _user_service
    if _user_service is None:
        _user_service = UserDataService(user_repository=get_user_repository())
    return _user_service
