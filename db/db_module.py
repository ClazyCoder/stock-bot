from sqlalchemy import create_engine, Session
from dotenv import load_dotenv
import os
from db.stock_model import Stock, Base
from schemas.stock import StockPrice
from interfaces.db_interface import IDBModule
from typing import List
load_dotenv()


class STOCK_DBModule(IDBModule):
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
            date=stock_data.trade_date,  # trade_date -> date
            open=stock_data.open_price,  # open_price -> open
            high=stock_data.high_price,  # high_price -> high
            low=stock_data.low_price,    # low_price -> low
            close=stock_data.close_price,  # close_price -> close
            volume=stock_data.volume
        )
        self.session.add(stock_model)
        self.session.commit()

    def get_stock_data(self, ticker: str) -> List[StockPrice]:
        """
        Get stock data from the database.
        """
        return self.session.query(Stock).filter(Stock.ticker == ticker).all()
