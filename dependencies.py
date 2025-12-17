# dependencies.py
from collectors.stock_api import StockDataCollector
from collectors.news_api import NewsDataCollector
from services.stock_data_service import StockDataService
from sqlalchemy.ext.asyncio import AsyncSession
from interfaces import IStockProvider, INewsProvider
from db.repositories.user_repository import UserRepository
from db.repositories.stock_repository import StockRepository
from db.connection import AsyncSessionLocal
from services.user_data_service import UserDataService
from typing import Generator
from langchain_mcp_adapters.client import MultiServerMCPClient
import os
import logging
import dotenv
dotenv.load_dotenv()

logger = logging.getLogger(__name__)

# Singleton instances
_stock_repository: StockRepository | None = None
_user_repository: UserRepository | None = None
_stock_data_collector: IStockProvider | None = None
_user_service: UserDataService | None = None
_stock_service: StockDataService | None = None
_mcp_client: MultiServerMCPClient | None = None
_news_collector: INewsProvider | None = None


async def get_mcp_client() -> MultiServerMCPClient:
    global _mcp_client
    if _mcp_client is None:
        logger.info("Initializing MCP client...")
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
        logger.info("MCP client initialized successfully")
    return _mcp_client


async def get_db_session() -> Generator[AsyncSession, None, None]:
    """Create and close a session for each FastAPI request."""
    logger.debug("Creating database session")
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        logger.debug("Closing database session")
        await session.close()


def get_stock_repository() -> StockRepository:
    """Return singleton StockRepository (creates session in each method using SessionFactory)."""
    global _stock_repository
    if _stock_repository is None:
        logger.info("Initializing StockRepository singleton")
        _stock_repository = StockRepository(session_factory=AsyncSessionLocal)
    return _stock_repository


def get_user_repository() -> UserRepository:
    """Return singleton UserRepository (creates session in each method using SessionFactory)."""
    global _user_repository
    if _user_repository is None:
        logger.info("Initializing UserRepository singleton")
        _user_repository = UserRepository(session_factory=AsyncSessionLocal)
    return _user_repository


def get_collector() -> IStockProvider:
    """Return singleton Collector."""
    global _stock_data_collector
    if _stock_data_collector is None:
        logger.info("Initializing StockDataCollector singleton")
        _stock_data_collector = StockDataCollector()
    return _stock_data_collector


def get_news_collector() -> INewsProvider:
    """Return singleton NewsDataCollector."""
    global _news_collector
    if _news_collector is None:
        logger.info("Initializing NewsDataCollector singleton")
        _news_collector = NewsDataCollector()
    return _news_collector


def get_stock_service() -> StockDataService:
    """Return singleton StockDataService."""
    global _stock_service
    if _stock_service is None:
        logger.info("Initializing StockDataService singleton")
        _stock_service = StockDataService(
            collector=get_collector(),
            stock_repository=get_stock_repository(),
            news_collector=get_news_collector()
        )
    return _stock_service


def get_user_data_service() -> UserDataService:
    """Return singleton UserDataService."""
    global _user_service
    if _user_service is None:
        logger.info("Initializing UserDataService singleton")
        _user_service = UserDataService(user_repository=get_user_repository())
    return _user_service
