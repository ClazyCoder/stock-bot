from typing import Protocol


class IBot(Protocol):
    def send_message(self, message: str):
        """
        Send a message to the bot.
        """
        pass

    def start(self):
        """
        Start the bot.
        """
        pass

    def stop(self):
        """
        Stop the bot.
        """
        pass
