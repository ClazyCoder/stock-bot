from interfaces.bot_interface import IBot


class TelegramBot(IBot):
    def __init__(self, token: str):
        pass

    async def send_message(self, message: str):
        pass

    async def start(self):
        pass

    async def stop(self):
        pass
