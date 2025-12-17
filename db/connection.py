# db/connection.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from db.models import Base
import dotenv
dotenv.load_dotenv()


DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL is None:
    raise ValueError(
        "DATABASE_URL environment variable is not set. Please configure it in your .env file "
        "or set it in the environment before starting the application."
    )
engine = create_async_engine(DATABASE_URL, echo=True, connect_args={})

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
