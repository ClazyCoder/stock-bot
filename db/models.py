# db/db_models.py
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.schema import UniqueConstraint, Index
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class Stock(Base):
    __tablename__ = 'stock_data'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, index=True)
    trade_date = Column(DateTime)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('ticker', 'trade_date', name='uq_ticker_trade_date'),
    )


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, nullable=False)
    provider_id = Column(String, nullable=False)

    is_authorized = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    subscriptions = relationship(
        'Subscription', back_populates='user', cascade="all, delete-orphan", passive_deletes=True)

    __table_args__ = (
        UniqueConstraint('provider', 'provider_id', name='uq_provider_user'),

        Index('ix_provider_user', 'provider', 'provider_id')
    )


class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(
        'users.id', ondelete='CASCADE'), nullable=False)
    chat_id = Column(String, nullable=False)

    ticker = Column(String, nullable=False)

    user = relationship('User', back_populates='subscriptions')
    created_at = Column(DateTime, server_default=func.now())


class StockNews(Base):
    __tablename__ = 'stock_news'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    full_content = Column(String, nullable=True)
    published_at = Column(DateTime)
    url = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now())

    chunks = relationship("StockNewsChunk", backref="parent",
                          cascade="all, delete-orphan", passive_deletes=True)


class StockNewsChunk(Base):
    __tablename__ = 'stock_news_chunks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, index=True, nullable=False)
    parent_id = Column(Integer, ForeignKey(
        'stock_news.id', ondelete='CASCADE'), nullable=False)
    embedding = Column(Vector(768))
    content = Column(String, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now())
