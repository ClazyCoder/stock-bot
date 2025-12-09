from interfaces.bot_interface import IBot


class TelegramBot(IBot):
    def __init__(self, token: str):
        pass

    def send_message(self, message: str):
        pass

    def start(self):
        pass

    def stop(self):
        pass
