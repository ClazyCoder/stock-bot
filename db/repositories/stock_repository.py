from db.repositories.base import BaseRepository
from schemas.stock import StockPrice
from db.models import Stock
from typing import List
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select


class StockRepository(BaseRepository):

    async def insert_stock_data(self, stock_data: StockPrice):
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
            await self.session.commit()
            return True
        except IntegrityError as e:
            await self.session.rollback()
            self.logger.warning(f"Stock data already exists: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error inserting stock data: {e}")
            await self.session.rollback()
            return False

    async def get_stock_data(self, ticker: str) -> List[StockPrice] | None:
        """
        Get stock data from the database.
        """
        try:
            stmt = select(Stock).where(Stock.ticker == ticker)
            result = await self.session.execute(stmt)
            orm_results = result.scalars().all()

            pydantic_results = [
                StockPrice(
                    ticker=stock.ticker,
                    trade_date=stock.trade_date,
                    open_price=stock.open,
                    high_price=stock.high,
                    low_price=stock.low,
                    close_price=stock.close,
                    volume=stock.volume,
                    created_at=stock.created_at,
                    updated_at=stock.updated_at
                ) for stock in orm_results
            ]
            return pydantic_results
        except Exception as e:
            self.logger.error(f"Error fetching stock data: {e}")
            return []
