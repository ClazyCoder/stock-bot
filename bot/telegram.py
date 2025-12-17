from services.user_data_service import UserDataService
from services.stock_data_service import StockDataService
from analysis.llm_module import LLMModule
from telegram.ext import Application, ContextTypes, CommandHandler
from telegram import Update
import logging
import os
import secrets
import re
import asyncio
from typing import Callable
from functools import wraps
from datetime import time
from utils.common import chunk_list
import pytz

kst = pytz.timezone('Asia/Seoul')


def auth_required(func: Callable):
    @wraps(func)
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user:
            return
        user_id = str(update.effective_user.id)
        user = await self.user_service.get_authorized_user("telegram", user_id)
        if not user:
            await update.message.reply_text("You are not authorized to use this bot")
            return
        return await func(self, update, context)
    return wrapper


class TelegramBot:
    def __init__(self, token: str, user_service: UserDataService, stock_service: StockDataService, llm_module: LLMModule):
        self.logger = logging.getLogger(__name__)
        self.application = Application.builder().token(token).build()
        self.user_service = user_service
        self.stock_service = stock_service
        self.llm_module = llm_module
        self._register_handlers()

    def _register_handlers(self):
        self.logger.info("Registering command handlers...")
        self.application.add_handler(CommandHandler("auth", self.auth))
        self.application.add_handler(CommandHandler("report", self.report))
        self.application.add_handler(CommandHandler("sub", self.subscribe))
        self.application.add_handler(CommandHandler("unsub", self.unsubscribe))
        self.logger.info(
            "Command handlers registered: /auth, /report, /sub, /unsub")

    @auth_required
    async def report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(
            update.effective_user.id) if update.effective_user else "unknown"
        try:
            ticker = "".join(context.args) if context.args else None
            if not ticker:
                self.logger.warning(
                    f"Report command called without ticker by user {user_id}")
                await update.message.reply_text("Please provide a ticker")
                return

            if not re.match(r'^[a-zA-Z0-9._-]+$', ticker):
                self.logger.warning(
                    f"Invalid ticker format '{ticker}' provided by user {user_id}")
                await update.message.reply_text("Invalid ticker format. Ticker must contain only alphanumeric characters and common separators (., _, -)")
                return
            self.logger.info(
                f"Generating report for ticker {ticker} requested by user {user_id}")
            await update.message.reply_text("Generating report... this may take a while...")
            report = await self.llm_module.generate_report_with_ticker(ticker)
            await update.message.reply_text(report)
            self.logger.info(
                f"Report generated and sent successfully for ticker {ticker} to user {user_id}")
        except Exception as e:
            self.logger.error(
                f"Error during report generation for ticker {ticker} by user {user_id}: {e}", exc_info=True)
            await update.message.reply_text("Error during report - Internal server error")

    async def auth(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(
            update.effective_user.id) if update.effective_user else "unknown"
        try:
            password = "".join(context.args) if context.args else ""
            expected_password = os.getenv('TELEGRAM_BOT_PASSWORD', '')
            self.logger.info(f"Authentication attempt by user {user_id}")
            if secrets.compare_digest(password, expected_password):
                result = await self.user_service.register_user("telegram", user_id)
                if result:
                    self.logger.info(
                        f"Authentication successful for user {user_id}")
                    await update.message.reply_text("Authentication successful")
                else:
                    self.logger.warning(
                        f"Authentication failed for user {user_id}: registration failed")
                    await update.message.reply_text("Authentication failed")
            else:
                self.logger.warning(
                    f"Authentication failed for user {user_id}: invalid password")
                await update.message.reply_text("Authentication failed")
        except Exception as e:
            self.logger.error(
                f"Error during authentication for user {user_id}: {e}", exc_info=True)
            await update.message.reply_text("Authentication failed - Internal server error")

    @auth_required
    async def subscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(
            update.effective_user.id) if update.effective_user else "unknown"
        chat_id = str(
            update.effective_chat.id) if update.effective_chat else "unknown"
        try:
            ticker = "".join(context.args) if context.args else None
            if not ticker:
                self.logger.warning(
                    f"Subscribe command called without ticker by user {user_id}")
                await update.message.reply_text("Please provide a ticker Example: /sub AAPL")
                return
            ticker = ticker.upper()
            self.logger.info(
                f"Subscription request for ticker {ticker} by user {user_id}, chat {chat_id}")
            if await self.user_service.add_subscription(
                    provider_id=user_id,
                    chat_id=chat_id,
                    ticker=ticker):
                await self.add_job(ticker)
                self.logger.info(
                    f"Subscription successful for ticker {ticker} by user {user_id}")
                await update.message.reply_text("Subscription successful. The report will be sent to you daily at 9:00 AM KST.")
            else:
                self.logger.warning(
                    f"Subscription failed for ticker {ticker} by user {user_id}")
                await update.message.reply_text("Subscription failed")

        except Exception as e:
            self.logger.error(
                f"Error during subscription for ticker {ticker} by user {user_id}: {e}", exc_info=True)
            await update.message.reply_text("Subscription failed - Internal server error")

    @auth_required
    async def unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(
            update.effective_user.id) if update.effective_user else "unknown"
        try:
            ticker = "".join(context.args) if context.args else None
            if not ticker:
                self.logger.warning(
                    f"Unsubscribe command called without ticker by user {user_id}")
                await update.message.reply_text("Please provide a ticker Example: /unsub AAPL")
                return
            ticker = ticker.upper()
            self.logger.info(
                f"Unsubscription request for ticker {ticker} by user {user_id}")
            if await self.user_service.remove_subscription(
                    provider_id=user_id,
                    ticker=ticker):
                self.logger.info(
                    f"Unsubscription successful for ticker {ticker} by user {user_id}")
                await update.message.reply_text("Unsubscription successful")
            else:
                self.logger.warning(
                    f"Unsubscription failed for ticker {ticker} by user {user_id}")
                await update.message.reply_text("Unsubscription failed")
        except Exception as e:
            self.logger.error(
                f"Error during unsubscription for ticker {ticker} by user {user_id}: {e}", exc_info=True)
            await update.message.reply_text("Unsubscription failed - Internal server error")

    async def send_subscriptions(self, context: ContextTypes.DEFAULT_TYPE):
        try:
            job = context.job
            ticker = job.data
            self.logger.info(
                f"Starting process for sending subscriptions for ticker {ticker}")
            subscriptions = await self.user_service.get_subscriptions_with_ticker(
                ticker=ticker)
            if not subscriptions:
                self.logger.info(
                    f"No subscriptions found for ticker {ticker}")
                return
            self.logger.info(
                f"Found {len(subscriptions)} subscriptions for ticker {ticker}")
            report = await self.llm_module.generate_report_with_ticker(ticker)
            self.logger.info(
                f"Report generated for ticker {ticker}")
            final_report = f"""
            # REPORT FOR {ticker}\n\n
            {report}
            """
            message_tasks = [context.bot.send_message(
                chat_id=subscription.chat_id, text=final_report) for subscription in subscriptions]
            for chunk in chunk_list(message_tasks, 20):
                results = await asyncio.gather(*chunk, return_exceptions=True)
                success_count = sum(
                    1 for r in results if not isinstance(r, Exception))
                error_count = len(results) - success_count
                if error_count > 0:
                    self.logger.warning(
                        f"Failed to send {error_count} messages for ticker {ticker}")
                await asyncio.sleep(1)
                self.logger.info(
                    f"Sent {success_count}/{len(chunk)} messages successfully for ticker {ticker}")
            self.logger.info(
                f"All messages sent for ticker {ticker} to {len(subscriptions)} subscribers")
        except Exception as e:
            self.logger.error(
                f"Error during sending subscriptions for ticker {ticker}: {e}", exc_info=True)

    async def add_job(self, ticker: str):
        job_queue = self.application.job_queue
        job_name = f"job_{ticker}"
        job_exists = job_queue.get_jobs_by_name(job_name)
        if job_exists:
            self.logger.info(f"Job for ticker {ticker} already exists")
            return
        job_queue.run_daily(self.send_subscriptions,
                            time=time(hour=9, minute=0, tzinfo=kst), days=range(1, 6), data=ticker, name=job_name)
        self.logger.info(f"Job for ticker {ticker} added : {job_name}")

    async def load_all_jobs(self):
        tickers = await self.user_service.get_unique_subscriptions_tickers()
        self.logger.info(f"Loading {len(tickers)} jobs")
        for ticker in tickers:
            await self.add_job(ticker)
            self.logger.info(f"Job for ticker {ticker} added")
        self.logger.info("All jobs loaded")

    async def start(self):
        self.logger.info("Starting Telegram bot...")
        try:
            await self.application.initialize()
            self.logger.info("Telegram bot application initialized")
            await self.application.start()
            self.logger.info("Telegram bot application started")
            await self.application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
            self.logger.info("Telegram bot polling started")
            await self.load_all_jobs()
            self.logger.info("Telegram bot started successfully")
        except Exception as e:
            self.logger.error(
                f"Error starting Telegram bot: {e}", exc_info=True)
            raise

    async def stop(self):
        self.logger.info("Stopping Telegram bot...")
        try:
            await self.application.updater.stop()
            self.logger.info("Telegram bot updater stopped")
            await self.application.stop()
            self.logger.info("Telegram bot application stopped")
            await self.application.shutdown()
            self.logger.info("Telegram bot shutdown completed")
            self.logger.info("Telegram bot stopped successfully")
        except Exception as e:
            self.logger.error(
                f"Error stopping Telegram bot: {e}", exc_info=True)
            raise
