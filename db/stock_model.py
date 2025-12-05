from sqlalchemy import Column, Integer, String, DateTime, Float
from db.db_module import Base


class Stock(Base):
    __tablename__ = 'stock_data'
    ticker = Column(String, primary_key=True)
    date = Column(DateTime, primary_key=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
