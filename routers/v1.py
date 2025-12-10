# routers/v1.py
from fastapi import APIRouter, HTTPException
from dependencies import get_stock_service, get_user_data_service
from services.stock_data_service import StockDataService
from services.user_data_service import UserDataService
from fastapi import Depends
from schemas import StockRequest

router = APIRouter(prefix="/v1", tags=["v1"])


@router.post("/collect")
async def collect_stock_price(request: StockRequest, stock_service: StockDataService = Depends(get_stock_service)):
    """
    Collects the latest stock price for the given ticker and saves it to the database.
    Parameters:
        request (StockRequest): The request body containing the stock ticker symbol.
        stock_service (StockDataService): The service used to collect and save stock data. Injected via FastAPI Depends.
    Returns:
        The result of the collect_and_save operation, typically a success message or the saved data.
    Error cases:
        - If the ticker symbol is invalid or not found, an error response may be returned.
        - If there is a problem with the external stock data provider, an error may occur.
        - If there is a database error while saving the data, an error may be returned.
    """
    success = await stock_service.collect_and_save(request.ticker)
    message = (
        "Stock data collected successfully"
        if success
        else "Failed to collect stock data"
    )
    return {
        "success": success,
        "message": message,
        "ticker": request.ticker,
    }


@router.get(f"/user")
async def get_user(provider: str, provider_id: str, user_data_service: UserDataService = Depends(get_user_data_service)):
    user = await user_data_service.get_user(provider, provider_id)
    if user:
        return user
    else:
        raise HTTPException(status_code=404, detail="User not found")
