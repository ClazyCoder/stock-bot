# routers/v1.py
from fastapi import APIRouter
from dependencies import get_stock_service
from services.stock_data_service import StockDataService
from fastapi import Depends
from schemas import StockRequest

router = APIRouter(prefix="/v1", tags=["v1"])


@router.post("/collect")
async def collect_stock_price(request: StockRequest, stock_service: StockDataService = Depends(get_stock_service)):
    return await stock_service.collect_and_save(request.ticker)
