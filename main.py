from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
import logging
import os
import dotenv
from routers import v1

dotenv.load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = logging.getLogger(__name__)
    logger.info("Starting stock-bot")
    logger.info("Starting stock-bot Services...")
    # TODO : Start services

    yield

    # TODO : Stop services
    logger.info("Stopping stock-bot Services...")
    logger.info("Stopping stock-bot")

app = FastAPI(lifespan=lifespan)
app.include_router(v1.router, prefix="/api")

if __name__ == "__main__":
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(level=logging.INFO, handlers=[
                        logging.StreamHandler(), logging.FileHandler('logs/stock-bot.log', encoding='utf-8')])
    uvicorn.run(app, host=os.getenv('HOST', '0.0.0.0'),
                port=int(os.getenv('PORT', 8000)))
