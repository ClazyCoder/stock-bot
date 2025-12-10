from interfaces import IDBModule, IStockProvider


class TelegramBot():
    def __init__(self, token: str, dbmodule: IDBModule, collector: IStockProvider):
        pass

    async def send_message(self, message: str):
        pass

    async def start(self):
        pass

    async def stop(self):
        pass
