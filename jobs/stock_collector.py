from dependencies import get_stock_service, get_user_data_service
import logging
import os
import asyncio


async def collect_stock_datas():
    """
    Collect stock data and news for all subscribed tickers.
    Processes tickers in batches to respect yfinance API limits.
    Runs daily at 9 AM (configured in lifespan).
    """
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("Starting to collect stock datas")

    stock_service = get_stock_service()
    user_service = get_user_data_service()

    # Get all subscribed tickers
    tickers = await user_service.get_unique_subscriptions_tickers()
    if not tickers:
        logger.info("No tickers found. Skipping data collection.")
        return

    logger.info(f"Found {len(tickers)} tickers: {tickers}")

    # Configuration for API rate limiting
    # Process 5 tickers at a time
    STOCK_DATA_BATCH_SIZE = int(os.getenv('STOCK_DATA_BATCH_SIZE', '5'))
    # Process 3 tickers at a time
    STOCK_NEWS_BATCH_SIZE = int(os.getenv('STOCK_NEWS_BATCH_SIZE', '3'))
    # 2 seconds between batches
    BATCH_DELAY_SECONDS = float(os.getenv('BATCH_DELAY_SECONDS', '2.0'))
    # 0.5 seconds between tickers
    TICKER_DELAY_SECONDS = float(os.getenv('TICKER_DELAY_SECONDS', '0.5'))

    # Collect stock price data in batches
    logger.info("Starting stock price data collection...")
    stock_data_success_count = 0
    stock_data_failed_count = 0

    for i in range(0, len(tickers), STOCK_DATA_BATCH_SIZE):
        batch = tickers[i:i + STOCK_DATA_BATCH_SIZE]
        batch_num = (i // STOCK_DATA_BATCH_SIZE) + 1
        total_batches = (len(tickers) + STOCK_DATA_BATCH_SIZE -
                         1) // STOCK_DATA_BATCH_SIZE

        logger.info(
            f"Processing stock data batch {batch_num}/{total_batches}: {batch}")

        try:
            result = await stock_service.collect_and_save(batch, "1d")
            if result:
                stock_data_success_count += len(batch)
                logger.info(
                    f"Successfully collected stock data for batch {batch_num}: {batch}")
            else:
                stock_data_failed_count += len(batch)
                logger.warning(
                    f"Failed to collect stock data for batch {batch_num}: {batch}")
        except Exception as e:
            stock_data_failed_count += len(batch)
            logger.error(
                f"Error collecting stock data for batch {batch_num} ({batch}): {e}", exc_info=True)

        # Add delay between batches (except for the last batch)
        if i + STOCK_DATA_BATCH_SIZE < len(tickers):
            logger.debug(
                f"Waiting {BATCH_DELAY_SECONDS} seconds before next batch...")
            await asyncio.sleep(BATCH_DELAY_SECONDS)

    logger.info(
        f"Stock price data collection completed: {stock_data_success_count} succeeded, {stock_data_failed_count} failed")

    # Collect stock news in batches (with longer delays due to more intensive processing)
    logger.info("Starting stock news collection...")
    stock_news_success_count = 0
    stock_news_failed_count = 0

    for i in range(0, len(tickers), STOCK_NEWS_BATCH_SIZE):
        batch = tickers[i:i + STOCK_NEWS_BATCH_SIZE]
        batch_num = (i // STOCK_NEWS_BATCH_SIZE) + 1
        total_batches = (len(tickers) + STOCK_NEWS_BATCH_SIZE -
                         1) // STOCK_NEWS_BATCH_SIZE

        logger.info(
            f"Processing stock news batch {batch_num}/{total_batches}: {batch}")

        try:
            result = await stock_service.collect_and_save_stock_news(batch)
            if result:
                stock_news_success_count += len(batch)
                logger.info(
                    f"Successfully collected stock news for batch {batch_num}: {batch}")
            else:
                stock_news_failed_count += len(batch)
                logger.warning(
                    f"Failed to collect stock news for batch {batch_num}: {batch}")
        except Exception as e:
            stock_news_failed_count += len(batch)
            logger.error(
                f"Error collecting stock news for batch {batch_num} ({batch}): {e}", exc_info=True)

        # Add delay between batches (except for the last batch)
        if i + STOCK_NEWS_BATCH_SIZE < len(tickers):
            logger.debug(
                f"Waiting {BATCH_DELAY_SECONDS * 2} seconds before next news batch...")
            # Longer delay for news collection
            await asyncio.sleep(BATCH_DELAY_SECONDS * 2)

    logger.info(
        f"Stock news collection completed: {stock_news_success_count} succeeded, {stock_news_failed_count} failed")

    # Summary
    logger.info("=" * 80)
    logger.info("Finished collecting stock datas")
    logger.info(f"Summary:")
    logger.info(
        f"  - Stock Data: {stock_data_success_count} succeeded, {stock_data_failed_count} failed")
    logger.info(
        f"  - Stock News: {stock_news_success_count} succeeded, {stock_news_failed_count} failed")
    logger.info(f"  - Total tickers: {len(tickers)}")
    logger.info("=" * 80)
