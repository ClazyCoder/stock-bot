from sqlalchemy import create_engine, MetaData, Session
from dotenv import load_dotenv
import os
from db.stock_model import Stock

load_dotenv()


class DBModule:
    def __init__(self):
        self.engine = create_engine(os.getenv('DATABASE_URL'))
        self.metadata = MetaData()
        self.metadata.create_all(self.engine)
        self.session = Session(self.engine)

    def get_session(self):
        return self.session

    def insert_stock_data(self, stock_data: Stock):
        self.session.add(stock_data)
        self.session.commit()
