from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
import logging
import os
import dotenv
import routers.v1 as v1
from bot.telegram import TelegramBot
from dependencies import get_user_repository, get_stock_repository, get_collector
from db.connection import init_db
from services.user_data_service import UserDataService
from services.stock_data_service import StockDataService

dotenv.load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = logging.getLogger(__name__)
    await init_db()
    logger.info("Starting stock-bot")
    logger.info("Starting stock-bot Services...")

    user_repository = get_user_repository()
    stock_repository = get_stock_repository()
    collector = get_collector()

    user_service = UserDataService(user_repository=user_repository)
    stock_service = StockDataService(
        collector=collector, stock_repository=stock_repository)

    bots = [TelegramBot(token=os.getenv('TELEGRAM_BOT_TOKEN'),
                        user_service=user_service, stock_service=stock_service)]
    for bot in bots:
        await bot.start()
    yield

    # TODO : Stop services
    logger.info("Stopping stock-bot Services...")
    logger.info("Stopping stock-bot")
    for bot in bots:
        await bot.stop()

app = FastAPI(lifespan=lifespan)
app.include_router(v1.router, prefix="/api")

if __name__ == "__main__":
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(level=logging.INFO, handlers=[
        logging.StreamHandler(), logging.FileHandler('logs/stock-bot.log', encoding='utf-8')])
    uvicorn.run(app, host=os.getenv('HOST', '0.0.0.0'),
                port=int(os.getenv('PORT', 8000)))
