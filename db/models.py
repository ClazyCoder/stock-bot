# db/db_models.py
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.schema import UniqueConstraint, Index
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Stock(Base):
    __tablename__ = 'stock_data'
    ticker = Column(String, primary_key=True)
    trade_date = Column(DateTime, primary_key=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, nullable=False)
    provider_id = Column(String, nullable=False)

    is_authorized = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    subscriptions = relationship(
        'Subscription', back_populates='user', cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('provider', 'provider_id', name='uq_provider_user'),

        Index('ix_provider_user', 'provider', 'provider_id')
    )


class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    ticker = Column(String, nullable=False)

    user = relationship('User', back_populates='subscriptions')
