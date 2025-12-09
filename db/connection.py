# db/connection.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base


DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///stock.db')

engine = create_engine(DATABASE_URL, connect_args={
                       "check_same_thread": False} if "sqlite" in DATABASE_URL else {})

Base.metadata.create_all(engine)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
