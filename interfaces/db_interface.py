from typing import Protocol
from schemas.stock import StockPrice
from schemas.user import UserDTO
from typing import List


class IStockDBModule(Protocol):
    async def insert_stock_data(self, stock_data: StockPrice) -> bool:
        """
        Insert stock data into the database.
        """
        pass

    async def get_stock_data(self, ticker: str) -> List[StockPrice] | None:
        """
        Get stock data from the database.
        """
        pass


class IBotDBModule(Protocol):
    async def register_user(self, provider: str, provider_id: str) -> bool:
        """
        Register a new user.
        """
        pass

    async def get_authrized_user(self, provider: str, provider_id: str) -> UserDTO | None:
        """
        Get an authorized user.
        """
        pass
