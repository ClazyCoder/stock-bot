from typing import Protocol, Callable, Awaitable


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

    def add_command_handler(self, command: str, handler: Callable[[str], Awaitable[str]]):
        """
        Add a command handler for the bot.
        """
        pass
