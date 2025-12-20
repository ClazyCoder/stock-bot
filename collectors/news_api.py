from collectors.interfaces import INewsProvider
from schemas.stock import StockNewsCreate, StockNewsChunkCreate
from typing import List, Union
import logging
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
import yfinance as yf
import trafilatura
import json
import asyncio
from typing import Tuple


class NewsDataCollector(INewsProvider):
    def __init__(self, chunk_size: Union[int, None] = None, chunk_overlap: Union[int, None] = None):
        self.logger = logging.getLogger(__name__)

        # Resolve chunking configuration: prefer explicit arguments, then environment, then defaults.
        # Validate NEWS_CHUNK_SIZE
        if chunk_size is not None:
            resolved_chunk_size = chunk_size
        else:
            raw_chunk_size = os.getenv("NEWS_CHUNK_SIZE", "1000")
            try:
                resolved_chunk_size = int(raw_chunk_size)
                if resolved_chunk_size <= 0:
                    raise ValueError(
                        "NEWS_CHUNK_SIZE must be a positive integer")
            except ValueError:
                self.logger.warning(
                    f"Invalid NEWS_CHUNK_SIZE '{raw_chunk_size}'; defaulting to 1000."
                )
                resolved_chunk_size = 1000

        # Validate NEWS_CHUNK_OVERLAP
        if chunk_overlap is not None:
            resolved_chunk_overlap = chunk_overlap
        else:
            raw_chunk_overlap = os.getenv("NEWS_CHUNK_OVERLAP", "200")
            try:
                resolved_chunk_overlap = int(raw_chunk_overlap)
                if resolved_chunk_overlap < 0:
                    raise ValueError(
                        "NEWS_CHUNK_OVERLAP must be a non-negative integer")
            except ValueError:
                self.logger.warning(
                    f"Invalid NEWS_CHUNK_OVERLAP '{raw_chunk_overlap}'; defaulting to 200."
                )
                resolved_chunk_overlap = 200

        # Validate logical constraint: chunk_overlap should be less than chunk_size
        if resolved_chunk_overlap >= resolved_chunk_size:
            self.logger.warning(
                f"NEWS_CHUNK_OVERLAP ({resolved_chunk_overlap}) >= NEWS_CHUNK_SIZE ({resolved_chunk_size}). "
                f"Adjusting chunk_overlap to {resolved_chunk_size - 1}."
            )
            resolved_chunk_overlap = max(0, resolved_chunk_size - 1)

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=resolved_chunk_size,
            chunk_overlap=resolved_chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        self.logger.info(f"News data collector built successfully")

    async def fetch_news(self, ticker: Union[str, List[str]]) -> List[Tuple[StockNewsCreate, List[StockNewsChunkCreate]]]:
        """
        Get the news for one or multiple tickers.
        Args:
            ticker: Union[str, List[str]] - The ticker or tickers of the news to fetch.
        Returns:
            List[Tuple[StockNewsCreate, List[StockNewsChunkCreate]]] - List of tuples containing news and chunks (without embeddings) for each ticker.
        """
        if isinstance(ticker, str):
            tickers_list = [ticker]
        else:
            tickers_list = ticker

        results: List[Tuple[StockNewsCreate, List[StockNewsChunkCreate]]] = []

        for ticker_symbol in tickers_list:
            try:
                self.logger.info(f"Fetching news for ticker: {ticker_symbol}")
                ticker_news: List[Tuple[StockNewsCreate,
                                        List[StockNewsChunkCreate]]] = []
                search_results = yf.Search(ticker_symbol).search()
                loop = asyncio.get_running_loop()
                self.logger.debug(
                    f"Found {len(search_results.news)} news items from search for ticker: {ticker_symbol}")

                for news_item in search_results.news:
                    try:
                        downloaded_page = await loop.run_in_executor(
                            None, lambda url=news_item['link']: trafilatura.fetch_url(url))
                        if not downloaded_page:
                            continue

                        extracted_content = await loop.run_in_executor(
                            None, lambda page=downloaded_page: trafilatura.extract(page, output_format='json', include_comments=False, with_metadata=True))
                        if not extracted_content:
                            continue

                        results_json = json.loads(extracted_content)
                        if not results_json.get('text'):
                            continue

                        chunked_contents = await loop.run_in_executor(
                            None, lambda text=results_json['text']: self.text_splitter.split_text(text))

                        if not chunked_contents:
                            continue

                        chunks = [StockNewsChunkCreate(
                            ticker=ticker_symbol,
                            content=content
                        ) for content in chunked_contents]

                        full_news = StockNewsCreate(
                            ticker=ticker_symbol,
                            title=results_json.get('title', ''),
                            full_content=results_json.get('text', ''),
                            published_at=results_json.get('date'),
                            url=news_item['link']
                        )

                        ticker_news.append((full_news, chunks))
                        self.logger.debug(
                            f"Processed news item: {full_news.title} for ticker {ticker_symbol}")
                    except Exception as e:
                        self.logger.error(
                            f"Error processing news item for ticker {ticker_symbol}: {e}", exc_info=True)
                        continue

                results.extend(ticker_news)
                self.logger.info(
                    f"Collected {len(ticker_news)} news items for ticker {ticker_symbol}")
            except Exception as e:
                self.logger.error(
                    f"Error fetching news for ticker {ticker_symbol}: {e}", exc_info=True)
                continue

        self.logger.info(
            f"News collection completed: {len(results)} total news items for {len(tickers_list)} ticker(s)")
        return results
