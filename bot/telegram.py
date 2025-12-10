from interfaces import IBotDBModule, IStockProvider
from telegram.ext import Application, ContextTypes, CommandHandler
from telegram import Update
import logging
import os


class TelegramBot:
    def __init__(self, token: str, dbmodule: IBotDBModule, collector: IStockProvider):
        self.application = Application.builder().token(token).build()
        self.dbmodule = dbmodule
        self.collector = collector
        self._register_handlers()
        self.logger = logging.getLogger(__name__)

    def _register_handlers(self):
        # TODO : Register handlers
        self.application.add_handler(CommandHandler("auth", self.auth))

    async def auth(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        password = "".join(context.args)
        if password == os.getenv('TELEGRAM_BOT_PASSWORD'):
            await self.dbmodule.register_user("telegram", user_id)
            await update.message.reply_text("Authentication successful")
        else:
            await update.message.reply_text("Authentication failed")

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
