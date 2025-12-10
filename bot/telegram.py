from services.user_data_service import UserDataService
from services.stock_data_service import StockDataService
from telegram.ext import Application, ContextTypes, CommandHandler
from telegram import Update
import logging
import os
import secrets


class TelegramBot:
    def __init__(self, token: str, user_service: UserDataService, stock_service: StockDataService):
        self.application = Application.builder().token(token).build()
        self.user_service = user_service
        self.stock_service = stock_service
        self._register_handlers()
        self.logger = logging.getLogger(__name__)

    def _register_handlers(self):
        # TODO : Register handlers
        self.application.add_handler(CommandHandler("auth", self.auth))

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
