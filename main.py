from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
import logging
import os
import dotenv
import routers.v1 as v1
from bot.telegram import TelegramBot
from dependencies import get_user_data_service, get_stock_service, get_mcp_client
from analysis.llm_module import LLMModule
from langchain.tools import tool
from typing import List, Callable
from langchain.tools import BaseTool
from scheduler import setup_scheduler
dotenv.load_dotenv()


def setup_httpx_logger():
    if not os.path.exists('logs'):
        os.makedirs('logs')

    target_loggers = ["httpx", "httpcore"]

    for logger_name in target_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)

        logger.propagate = False

        file_handler = logging.FileHandler(
            f"logs/{logger_name}.log", encoding='utf-8')

        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        if logger.hasHandlers():
            logger.handlers.clear()
        logger.addHandler(file_handler)


async def build_tools(tool_func_list: List[Callable]) -> List[BaseTool]:
    logger = logging.getLogger(__name__)
    mcp_client = await get_mcp_client()
    mcp_tools = await mcp_client.get_tools()
    logger.info(f"Found {len(mcp_tools)} mcp tools")
    tools = [tool(func) for func in tool_func_list]
    logger.info(f"Built {len(tools)} local tools")
    return tools + mcp_tools


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = logging.getLogger(__name__)
    logger.info("Starting stock-bot")
    logger.info("Starting stock-bot Services...")
    # Use singleton services (Bot and FastAPI share the same instances)
    user_service = get_user_data_service()
    stock_service = get_stock_service()
    scheduler = setup_scheduler()
    llm_module = LLMModule(
        tools=await build_tools([stock_service.get_stock_data_llm_context, stock_service.get_stock_news_llm_context]))
    bots = [TelegramBot(token=os.getenv('TELEGRAM_BOT_TOKEN'),
                        user_service=user_service, stock_service=stock_service, llm_module=llm_module)]
    for bot in bots:
        await bot.start()
    scheduler.start()
    logger.info("Scheduler started")
    yield

    logger.info("Stopping stock-bot Services...")
    logger.info("Stopping stock-bot")
    for bot in bots:
        await bot.stop()
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)
app.include_router(v1.router, prefix="/api")

if __name__ == "__main__":
    setup_httpx_logger()
    logging.basicConfig(level=logging.INFO, handlers=[
        logging.StreamHandler(), logging.FileHandler('logs/stock-bot.log', encoding='utf-8')], format='%(asctime)s - %(levelname)s - %(message)s')
    uvicorn.run(app, host=os.getenv('HOST', '0.0.0.0'),
                port=int(os.getenv('PORT', 8000)))
