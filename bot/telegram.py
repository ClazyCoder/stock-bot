from interfaces import IDBModule, IStockProvider
from telegram.ext import Application
from telegram import Update
import logging


class TelegramBot:
    def __init__(self, token: str, dbmodule: IDBModule, collector: IStockProvider):
        self.application = Application.builder().token(token).build()
        self.dbmodule = dbmodule
        self.collector = collector
        self._register_handlers()
        self.logger = logging.getLogger(__name__)

    def _register_handlers(self):
        # TODO : Register handlers
        pass

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
