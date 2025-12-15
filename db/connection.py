# db/connection.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from db.models import Base
import dotenv
dotenv.load_dotenv()


DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL is None:
    raise ValueError("DATABASE_URL is not set")
engine = create_async_engine(DATABASE_URL, echo=True, connect_args={})


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
