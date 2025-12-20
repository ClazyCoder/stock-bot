from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
import logging
import os
import dotenv
import routers.v1 as v1
from bot.telegram import TelegramBot
from dependencies import get_user_data_service, get_llm_service
from scheduler import setup_scheduler
dotenv.load_dotenv()


def ensure_logs_directory():
    """Ensure the logs directory exists. Safe to call multiple times."""
    if not os.path.exists('logs'):
        os.makedirs('logs')


def setup_httpx_logger():
    ensure_logs_directory()

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure logs directory exists before any logging operations
    ensure_logs_directory()

    logger = logging.getLogger(__name__)
    logger.info("Starting stock-bot")
    logger.info("Starting stock-bot Services...")

    # Validate required environment variables
    telegram_bot_password = os.getenv('TELEGRAM_BOT_PASSWORD', '')
    if not telegram_bot_password or not telegram_bot_password.strip():
        raise ValueError(
            "TELEGRAM_BOT_PASSWORD environment variable must be set to a non-empty value. "
            "This is required for bot authentication security."
        )

    # Use singleton services (Bot and FastAPI share the same instances)
    user_service = get_user_data_service()
    llm_service = get_llm_service()
    bots = [TelegramBot(token=os.getenv('TELEGRAM_BOT_TOKEN'),
                        user_service=user_service, llm_service=llm_service)]
    for bot in bots:
        await bot.start()
    scheduler = setup_scheduler(telegram_bot=bots[0])
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
    ensure_logs_directory()
    setup_httpx_logger()
    logging.basicConfig(level=logging.INFO, handlers=[
        logging.StreamHandler(), logging.FileHandler('logs/stock-bot.log', encoding='utf-8')], format='%(asctime)s - %(levelname)s - %(message)s')
    uvicorn.run(app, host=os.getenv('HOST', '0.0.0.0'),
                port=int(os.getenv('PORT', 8000)))
