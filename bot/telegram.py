from services.user_data_service import UserDataService
from services.llm_service import LLMService
from telegram.ext import Application, ContextTypes, CommandHandler
from telegram import Update
from telegram.error import Conflict, RetryAfter, TimedOut
import logging
import os
import secrets
import re
import asyncio
from typing import Callable
from functools import wraps
from utils.common import chunk_list
import textwrap


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
    def __init__(self, token: str, user_service: UserDataService, llm_service: LLMService):
        self.logger = logging.getLogger(__name__)
        self.application = Application.builder().token(token).build()
        self.user_service = user_service
        self.llm_service = llm_service
        self._register_handlers()
        self._register_error_handler()

    def _register_handlers(self):
        self.logger.info("Registering command handlers...")
        self.application.add_handler(CommandHandler("auth", self.auth))
        self.application.add_handler(CommandHandler("report", self.report))
        self.application.add_handler(CommandHandler("sub", self.subscribe))
        self.application.add_handler(CommandHandler("unsub", self.unsubscribe))
        self.logger.info(
            "Command handlers registered: /auth, /report, /sub, /unsub")

    def _register_error_handler(self):
        """Register error handler for telegram errors."""
        async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
            """Handle errors that occur during update processing."""
            error = context.error
            if isinstance(error, Conflict):
                self.logger.error(
                    f"Conflict error detected: Another bot instance may be running. "
                    f"Error: {error}. This usually means multiple instances are polling "
                    f"the same bot token simultaneously."
                )
                # Don't raise - log and continue to prevent spam
            elif isinstance(error, RetryAfter):
                self.logger.warning(
                    f"Rate limit hit: {error}. Waiting {error.retry_after} seconds..."
                )
            elif isinstance(error, TimedOut):
                self.logger.warning(f"Request timed out: {error}")
            else:
                self.logger.error(
                    f"Exception while handling an update: {error}",
                    exc_info=error
                )

        self.application.add_error_handler(error_handler)
        self.logger.info("Error handler registered")

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
            report = await self.llm_service.generate_report_with_ticker(ticker)
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

            # Security check: reject authentication if password is not configured
            if not expected_password or not expected_password.strip():
                self.logger.error(
                    "Authentication attempted but TELEGRAM_BOT_PASSWORD is not configured. Rejecting all authentication attempts.")
                await update.message.reply_text("Authentication failed - Server configuration error")
                return

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
            ticker = "".join(context.args) if context.args else ""
            if not ticker:
                self.logger.warning(
                    f"Subscribe command called without ticker by user {user_id}")
                await update.message.reply_text("Please provide a ticker Example: /sub AAPL")
                return
            ticker = ticker.strip().upper()
            if not re.fullmatch(r"[A-Z0-9.\-]+", ticker):
                self.logger.warning(
                    f"Subscribe command called with invalid ticker '{ticker}' by user {user_id}")
                await update.message.reply_text("Invalid ticker format. Please provide a valid ticker Example: /sub AAPL")
                return
            self.logger.info(
                f"Subscription request for ticker {ticker} by user {user_id}, chat {chat_id}")
            if await self.user_service.add_subscription(
                    provider_id=user_id,
                    chat_id=chat_id,
                    ticker=ticker):
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

    async def send_subscriptions(self, ticker: str):
        """
        Send subscriptions for a given ticker.
        Args:
            ticker: str - The ticker to send subscriptions for.
        """
        try:
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

            # Generate report using LLM service
            report = await self.llm_service.generate_report_with_ticker(ticker)
            self.logger.info(
                f"Report generated for ticker {ticker}")

            final_report = textwrap.dedent(f"""
                **REPORT FOR {ticker.upper()}**

                {report}
            """).strip()

            bot = self.application.bot
            message_tasks = [(bot.send_message(
                chat_id=subscription.chat_id, text=final_report), subscription)
                for subscription in subscriptions]
            for chunk in chunk_list(message_tasks, 20):
                tasks_only = [task for task, _ in chunk]
                subscriptions_chunk = [sub for _, sub in chunk]
                results = await asyncio.gather(*tasks_only, return_exceptions=True)
                success_count = sum(
                    1 for r in results if not isinstance(r, Exception))
                error_count = len(results) - success_count
                if error_count > 0:
                    for result, subscription in zip(results, subscriptions_chunk):
                        if isinstance(result, Exception):
                            self.logger.warning(
                                f"Failed to send message for ticker {ticker} to chat_id {subscription.chat_id}: {type(result).__name__}: {result}")
                await asyncio.sleep(1)
                self.logger.info(
                    f"Sent {success_count}/{len(chunk)} messages successfully for ticker {ticker}")
            self.logger.info(
                f"All messages sent for ticker {ticker} to {len(subscriptions)} subscribers")
        except Exception as e:
            self.logger.error(
                f"Error during sending subscriptions for ticker {ticker}: {e}", exc_info=True)

    async def start(self):
        self.logger.info("Starting Telegram bot...")
        try:
            # Delete any existing webhook to ensure clean state
            # This prevents conflicts if another instance was running
            try:
                await self.application.bot.delete_webhook(drop_pending_updates=True)
                self.logger.info("Deleted existing webhook (if any)")
            except Exception as e:
                self.logger.warning(
                    f"Could not delete webhook (may not exist): {e}")

            await self.application.initialize()
            self.logger.info("Telegram bot application initialized")
            await self.application.start()
            self.logger.info("Telegram bot application started")

            # Start polling with error handling for conflicts
            try:
                await self.application.updater.start_polling(
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=True
                )
                self.logger.info("Telegram bot polling started")
            except Conflict as e:
                self.logger.error(
                    f"Conflict error: Another bot instance may be running. "
                    f"Make sure only one instance is running. Error: {e}")
                # Try to stop and cleanup before raising
                try:
                    await self.application.updater.stop()
                    await self.application.stop()
                    await self.application.shutdown()
                except Exception as cleanup_error:
                    self.logger.warning(
                        f"Error during cleanup: {cleanup_error}")
                raise
            except (RetryAfter, TimedOut) as e:
                self.logger.warning(
                    f"Telegram API rate limit/timeout: {e}. Retrying...")
                # Wait a bit and retry
                await asyncio.sleep(5)
                await self.application.updater.start_polling(
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=True
                )
                self.logger.info("Telegram bot polling started after retry")

            self.logger.info("Telegram bot started successfully")
        except Exception as e:
            self.logger.error(
                f"Error starting Telegram bot: {e}", exc_info=True)
            raise

    async def stop(self):
        self.logger.info("Stopping Telegram bot...")
        try:
            # Stop polling first
            try:
                if self.application.updater.running:
                    await self.application.updater.stop()
                    self.logger.info("Telegram bot updater stopped")
            except Exception as e:
                self.logger.warning(f"Error stopping updater: {e}")

            # Stop application
            try:
                await self.application.stop()
                self.logger.info("Telegram bot application stopped")
            except Exception as e:
                self.logger.warning(f"Error stopping application: {e}")

            # Shutdown application
            try:
                await self.application.shutdown()
                self.logger.info("Telegram bot shutdown completed")
            except Exception as e:
                self.logger.warning(f"Error during shutdown: {e}")

            self.logger.info("Telegram bot stopped successfully")
        except Exception as e:
            self.logger.error(
                f"Error stopping Telegram bot: {e}", exc_info=True)
            # Don't raise - allow cleanup to continue even if there are errors
