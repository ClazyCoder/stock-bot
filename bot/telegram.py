from services.user_data_service import UserDataService
from services.stock_data_service import StockDataService
from analysis.llm_module import LLMModule
from telegram.ext import Application, ContextTypes, CommandHandler
from telegram import Update
import logging
import os
import secrets
import re


class TelegramBot:
    def __init__(self, token: str, user_service: UserDataService, stock_service: StockDataService, llm_module: LLMModule):
        self.application = Application.builder().token(token).build()
        self.user_service = user_service
        self.stock_service = stock_service
        self.llm_module = llm_module
        self._register_handlers()
        self.logger = logging.getLogger(__name__)

    def _register_handlers(self):
        # TODO : Register handlers
        self.application.add_handler(CommandHandler("auth", self.auth))
        self.application.add_handler(CommandHandler("report", self.report))

    async def report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            ticker = "".join(context.args) if context.args else None
            if not ticker:
                await update.message.reply_text("Please provide a ticker")
                return

            # Validate ticker: only alphanumeric characters and common separators
            if not re.match(r'^[a-zA-Z0-9._/-]+$', ticker):
                await update.message.reply_text("Invalid ticker format. Ticker must contain only alphanumeric characters and common separators (., _, -, /)")
                return
            await update.message.reply_text("Generating report... this may take a while...")
            report = await self.llm_module.generate_report_with_ticker(ticker)
            await update.message.reply_text(report)
        except Exception as e:
            self.logger.error(f"Error during report: {e}")
            await update.message.reply_text("Error during report - Internal server error")

    async def auth(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = str(update.effective_user.id)
            password = "".join(context.args) if context.args else ""
            expected_password = os.getenv('TELEGRAM_BOT_PASSWORD', '')
            if secrets.compare_digest(password, expected_password):
                result = await self.user_service.register_user("telegram", user_id)
                if result:
                    await update.message.reply_text("Authentication successful")
                else:
                    await update.message.reply_text("Authentication failed")
            else:
                await update.message.reply_text("Authentication failed")
        except Exception as e:
            self.logger.error(f"Error during authentication: {e}")
            await update.message.reply_text("Authentication failed - Internal server error")

    async def start(self):
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        self.logger.info("Telegram bot started")

    async def stop(self):
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
        self.logger.info("Telegram bot stopped")
