# scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
import logging
from .jobs import collect_stock_datas

logger = logging.getLogger(__name__)


def setup_scheduler() -> AsyncIOScheduler:
    """
    Setup the scheduler for the stock collector.
    Returns:
        AsyncIOScheduler: The scheduler instance.
    """
    logger.info("Setting up scheduler...")
    scheduler = AsyncIOScheduler()

    # Collect stock data and news daily at 9:00 AM
    scheduler.add_job(
        func=lambda: asyncio.create_task(collect_stock_datas()),
        trigger=CronTrigger(day_of_week='mon-fri', hour=9, minute=0),
        id='stock_collector',
        max_instances=1,
        replace_existing=True
    )
    logger.info(
        "Scheduler job 'stock_collector' added (runs Mon-Fri at 9:00 AM)")

    return scheduler
