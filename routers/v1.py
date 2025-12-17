# routers/v1.py
from fastapi import APIRouter, HTTPException, Depends
from dependencies import get_stock_service, get_user_data_service
from schemas import StockRequest
from schemas.stock import StockSymbol
from services.stock_data_service import StockDataService
from services.user_data_service import UserDataService
from utils.common import validate_ticker, validate_query
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1", tags=["v1"])


@router.post("/collect")
async def collect_stock_price(request: StockRequest, stock_service: StockDataService = Depends(get_stock_service)):
    """
    Collects the latest stock price for the given ticker and saves it to the database.
    Parameters:
        request (StockRequest): The request body containing the stock ticker symbol.
    Returns:
        The result of the collect_and_save operation, typically a success message or the saved data.
    Error cases:
        - If the ticker symbol is invalid or not found, an error response may be returned.
        - If there is a problem with the external stock data provider, an error may occur.
        - If there is a database error while saving the data, an error may be returned.
    """
    validate_ticker(request.ticker)
    logger.info(
        f"Collecting stock price for ticker: {request.ticker}, period: {request.period}")
    try:
        success = await stock_service.collect_and_save(request.ticker, request.period)
        message = (
            "Stock data collected successfully"
            if success
            else "Failed to collect stock data"
        )
        if success:
            logger.info(
                f"Successfully collected stock data for ticker: {request.ticker}")
        else:
            logger.warning(
                f"Failed to collect stock data for ticker: {request.ticker}")
        return {
            "success": success,
            "message": message,
            "ticker": request.ticker,
            "period": request.period,
        }
    except Exception as e:
        logger.error(
            f"Error collecting stock price for ticker {request.ticker}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/user")
async def get_user(provider: str, provider_id: str, user_data_service: UserDataService = Depends(get_user_data_service)):
    logger.info(
        f"Getting user: provider={provider}, provider_id={provider_id}")
    try:
        user = await user_data_service.get_user(provider, provider_id)
        if user:
            logger.info(
                f"User found: provider={provider}, provider_id={provider_id}")
            return user
        else:
            logger.warning(
                f"User not found: provider={provider}, provider_id={provider_id}")
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting user (provider={provider}, provider_id={provider_id}): {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/stock_price")
async def get_stock_price(ticker: str, stock_service: StockDataService = Depends(get_stock_service)):
    validate_ticker(ticker)
    logger.info(f"Getting stock price for ticker: {ticker}")
    try:
        stock_price = await stock_service.get_stock_data(ticker)
        if stock_price:
            logger.info(
                f"Found {len(stock_price)} stock price records for ticker: {ticker}")
            return {
                "success": True,
                "data": stock_price,
            }
        else:
            logger.warning(f"Stock price not found for ticker: {ticker}")
            raise HTTPException(
                status_code=404, detail="Stock price not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting stock price for ticker {ticker}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/collect_stock_news")
async def collect_stock_news(stock_req: StockSymbol, stock_service: StockDataService = Depends(get_stock_service)):
    validate_ticker(stock_req.ticker)
    logger.info(f"Collecting stock news for ticker: {stock_req.ticker}")
    try:
        success = await stock_service.collect_and_save_stock_news(stock_req.ticker)
        if success:
            logger.info(
                f"Successfully collected stock news for ticker: {stock_req.ticker}")
            return {
                "success": True,
                "message": "Stock news collected successfully",
            }
        else:
            logger.warning(
                f"Failed to collect stock news for ticker: {stock_req.ticker}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to collect stock news for ticker {stock_req.ticker}. This may be due to no news available, external API issues, or database errors."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error collecting stock news for ticker {stock_req.ticker}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/stock_news")
async def get_stock_news(ticker: str, query: str, stock_service: StockDataService = Depends(get_stock_service)):
    validate_ticker(ticker)
    validate_query(query)
    logger.info(f"Getting stock news for ticker: {ticker}, query: {query}")
    try:
        stock_news = await stock_service.get_stock_news(ticker, query, top_k=5, candidate_pool=20)
        if stock_news:
            logger.info(
                f"Found {len(stock_news)} stock news items for ticker: {ticker}, query: {query}")
            return {
                "success": True,
                "data": stock_news,
            }
        else:
            logger.warning(
                f"Stock news not found for ticker: {ticker}, query: {query}")
            raise HTTPException(status_code=404, detail="Stock news not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting stock news for ticker {ticker}, query {query}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {str(e)}")
