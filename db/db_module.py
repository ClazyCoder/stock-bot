from sqlalchemy import create_engine, Session
from dotenv import load_dotenv
import os
from db.stock_model import Stock, Base
from schemas import StockPrice
from interfaces import IDBModule
from typing import List
from sqlalchemy.exc import IntegrityError
import asyncio

load_dotenv()


class SQLDBModule(IDBModule):
    def __init__(self):
        self.engine = create_engine(
            os.getenv('STOCK_DATABASE_URL', 'sqlite:///stock.db'))
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)

    async def get_session(self):
        return self.session

    def _insert_sync(self, stock_data: StockPrice):
        try:
            self.session.add(stock_data)
            self.session.commit()
            return True
        except IntegrityError as e:
            self.session.rollback()
            print(f"Error inserting stock data: {e}")
            return False

    async def insert_stock_data(self, stock_data: StockPrice):
        """
        Insert stock data into the database.
        Converts StockPrice (Pydantic) to Stock (SQLAlchemy ORM).
        """
        # Convert StockPrice (Pydantic) to Stock (SQLAlchemy)
        stock_model = Stock(
            ticker=stock_data.ticker,
            trade_date=stock_data.trade_date,  # trade_date -> trade_date
            open=stock_data.open_price,  # open_price -> open
            high=stock_data.high_price,  # high_price -> high
            low=stock_data.low_price,    # low_price -> low
            close=stock_data.close_price,  # close_price -> close
            volume=stock_data.volume,  # volume -> volume
            created_at=stock_data.created_at,  # created_at -> created_at
            updated_at=stock_data.updated_at  # updated_at -> updated_at
        )
        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, lambda: self._insert_sync(stock_model))
            return result
        except Exception as e:
            print(f"Error inserting stock data: {e}")
            return False

    async def get_stock_data(self, ticker: str) -> List[StockPrice] | None:
        """
        Get stock data from the database.
        """
        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.session.query(Stock).filter(
                    Stock.ticker == ticker).all()
            )
            return result
        except Exception as e:
            print(f"Error getting stock data: {e}")
            return None


class VectorDBModule():
    # TODO: Implement VectorDBModule
    pass


class UserDBModule():
    # TODO: Implement UserDBModule
    pass
