# db/connection.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from db.models import Base, Stock, User, Subscription
import asyncio


DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite+aiosqlite::///stock.db')

engine = create_async_engine(DATABASE_URL, echo=True, connect_args={
    "check_same_thread": False} if "sqlite" in DATABASE_URL else {})

asyncio.run(Base.metadata.create_all(bind=engine))

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
