# scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
import logging
from jobs import collect_all_stock_data
from bot.telegram import TelegramBot

logger = logging.getLogger(__name__)


def setup_scheduler(telegram_bot: TelegramBot) -> AsyncIOScheduler:
    """
    Setup the scheduler for the stock collector.
    Args:
        telegram_bot: TelegramBot - The Telegram bot instance.
    Returns:
        AsyncIOScheduler: The scheduler instance.
    """
    logger.info("Setting up scheduler...")
    scheduler = AsyncIOScheduler()

    # Collect stock data and news daily at 9:00 AM
    scheduler.add_job(
        func=collect_all_stock_data,
        args=[telegram_bot],
        trigger=CronTrigger(day_of_week='mon-fri', hour=9,
                            minute=0, timezone='Asia/Seoul'),
        id='stock_collector',
        max_instances=1,
        replace_existing=True
    )
    logger.info(
        "Scheduler job 'stock_collector' added (runs Mon-Fri at 9:00 AM)")

    return scheduler
