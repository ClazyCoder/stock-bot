from typing import Protocol


class IBot(Protocol):
    async def send_message(self, message: str):
        """
        Send a message to the bot.
        """
        pass

    async def start(self):
        """
        Start the bot.
        """
        pass

    async def stop(self):
        """
        Stop the bot.
        """
        pass
