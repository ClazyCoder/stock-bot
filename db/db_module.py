from sqlalchemy import create_engine, Session
from dotenv import load_dotenv
import os
from db.stock_model import Stock, Base
from schemas.stock import StockPrice
from interfaces.db_interface import IDBModule
from typing import List
from sqlalchemy.exc import IntegrityError

load_dotenv()


class SQLiteDBModule(IDBModule):
    def __init__(self):
        self.engine = create_engine(os.getenv('STOCK_DATABASE_URL'))
        Base.metadata.create_all(self.engine)
        self.session = Session(self.engine)

    def get_session(self):
        return self.session

    def insert_stock_data(self, stock_data: StockPrice):
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
            self.session.add(stock_model)
            self.session.commit()
            return True
        except IntegrityError as e:
            self.session.rollback()
            print(f"Error inserting stock data: {e}")
            return False

    def get_stock_data(self, ticker: str) -> List[StockPrice] | None:
        """
        Get stock data from the database.
        """
        try:
            return self.session.query(Stock).filter(Stock.ticker == ticker).order_by(Stock.trade_date.desc()).all()
        except Exception as e:
            print(f"Error getting stock data: {e}")
            return None


class MySQLDBModule(IDBModule):
    # TODO: Implement MySQL DBModule
    pass


class PostgreSQLDBModule(IDBModule):
    # TODO: Implement PostgreSQL DBModule
    pass
