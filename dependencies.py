# dependencies.py
from langchain.tools import BaseTool
from typing import List
from analysis.llm_module import LLMModule
from collectors.stock_api import StockDataCollector
from collectors.news_api import NewsDataCollector
from services.stock_data_service import StockDataService
from sqlalchemy.ext.asyncio import AsyncSession
from collectors.interfaces import IStockProvider, INewsProvider
from db.repositories.user_repository import UserRepository
from db.repositories.stock_repository import StockRepository
from db.repositories.report_repository import ReportRepository
from db.connection import AsyncSessionLocal
from services.user_data_service import UserDataService
from services.llm_service import LLMService
from typing import Generator
from langchain_mcp_adapters.client import MultiServerMCPClient
from llm_tools.stock_tools import StockTools
import os
import logging
import dotenv
import asyncio
from db.repositories.admin.admin_repository import AdminRepository

dotenv.load_dotenv()
logger = logging.getLogger(__name__)


_llm_lock = asyncio.Lock()
_mcp_lock = asyncio.Lock()

# Singleton instances
_stock_repository: StockRepository | None = None
_user_repository: UserRepository | None = None
_report_repository: ReportRepository | None = None
_stock_data_collector: IStockProvider | None = None
_user_service: UserDataService | None = None
_stock_service: StockDataService | None = None
_llm_service: LLMService | None = None
_news_collector: INewsProvider | None = None
_mcp_client: MultiServerMCPClient | None = None
_mcp_tools: List[BaseTool] | None = None
_admin_report_repository: AdminRepository | None = None


async def get_edgar_tools() -> List[BaseTool]:
    """
    Return singleton EdgarTools.
    Caches the MCP client and tools to avoid recreating connections on every call.
    """
    global _mcp_client, _mcp_tools

    # Return cached tools if available
    if _mcp_tools is not None:
        return _mcp_tools

    async with _mcp_lock:
        # Double-check after acquiring lock
        if _mcp_tools is not None:
            return _mcp_tools

        # Constants
        EDGAR_IDENTITY_PLACEHOLDER = "Your Name your.email@example.com"
        logger.info("Initializing MCP client singleton...")

        # Validate EDGAR_IDENTITY is set and not the placeholder
        edgar_identity = os.getenv("EDGAR_IDENTITY", "")
        if not edgar_identity or edgar_identity == EDGAR_IDENTITY_PLACEHOLDER:
            raise EnvironmentError(
                "EDGAR_IDENTITY environment variable is not set or is using the placeholder value. "
                "Please set EDGAR_IDENTITY to your actual name and email (e.g., 'John Doe john.doe@example.com'). "
                "This is required by the SEC EDGAR API to identify your application."
            )

        _mcp_client = MultiServerMCPClient(
            {
                "edgartools": {
                    "transport": "stdio",
                    "command": "python",
                    "args": ["-m", "edgar.ai"],
                    "env": {
                        "EDGAR_IDENTITY": edgar_identity
                    }
                }
            }
        )
        logger.info("MCP client initialized successfully")
        _mcp_tools = await _mcp_client.get_tools()
        logger.info(f"Found {len(_mcp_tools)} mcp tools")
        return _mcp_tools


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


def get_report_repository() -> ReportRepository:
    """Return singleton ReportRepository (creates session in each method using SessionFactory)."""
    global _report_repository
    if _report_repository is None:
        logger.info("Initializing ReportRepository singleton")
        _report_repository = ReportRepository(
            session_factory=AsyncSessionLocal)
    return _report_repository


async def get_llm_service() -> LLMService:
    """Return singleton LLMService."""
    global _llm_service
    async with _llm_lock:
        if _llm_service is None:
            logger.info("Initializing LLMService singleton")
            local_tools = StockTools(
                stock_repository=get_stock_repository()).get_tools()
            mcp_tools = await get_edgar_tools()
            tools = local_tools + mcp_tools
            llm_module = LLMModule(tools=tools)
            _llm_service = LLMService(
                llm_module=llm_module,
                stock_repository=get_stock_repository(),
                report_repository=get_report_repository()
            )
            logger.info("LLMService initialized successfully")
        return _llm_service


async def get_admin_report_repository() -> AdminRepository:
    """Return singleton AdminReportRepository."""
    global _admin_report_repository
    if _admin_report_repository is None:
        logger.info("Initializing AdminReportRepository singleton")
        _admin_report_repository = AdminRepository(
            session_factory=AsyncSessionLocal)
    return _admin_report_repository
