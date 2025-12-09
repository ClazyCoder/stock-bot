# routers/v1.py
from fastapi import APIRouter
from dependencies import get_stock_service
from services.stock_data_service import StockDataService
from fastapi import Depends

router = APIRouter(prefix="/v1", tags=["v1"])


@router.post("/collect_stock_price")
async def collect_stock_price(ticker: str, stock_service: StockDataService = Depends(get_stock_service)):
    return await stock_service.collect_and_save(ticker)
