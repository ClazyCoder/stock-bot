from interfaces import INewsProvider
from schemas.stock import StockNewsCreate, StockNewsChunkCreate
from typing import List, Union
import logging
import os
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import yfinance as yf
import trafilatura
import json
import asyncio
from typing import Tuple


class NewsDataCollector(INewsProvider):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.embedding_model = self._build_embedding_model()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, separators=["\n\n", "\n", ".", " ", ""])
        self.logger.info(f"News data collector built successfully")

    def _build_embedding_model(self):
        self.logger.info("Building embedding model...")
        provider = os.getenv("EMBEDDING_PROVIDER", "ollama")
        model = os.getenv("EMBEDDING_MODEL", "embeddinggemma")
        if provider == "ollama":
            return OllamaEmbeddings(model=model, base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"), num_gpu=0)
        elif provider == "openai":
            raise NotImplementedError(
                "OpenAI embedding model is not implemented")
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")

    async def fetch_news(self, ticker: Union[str, List[str]]) -> List[Tuple[StockNewsCreate, List[StockNewsChunkCreate]]]:
        """
        Get the news for one or multiple tickers.
        Args:
            ticker: Union[str, List[str]] - The ticker or tickers of the news to fetch.
        Returns:
            List[Tuple[StockNewsCreate, List[StockNewsChunkCreate]]] - List of tuples containing news and chunks for each ticker.
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

                        embeddings = await self.embedding_model.aembed_documents(chunked_contents)
                        chunks = [StockNewsChunkCreate(
                            ticker=ticker_symbol,
                            title=results_json.get('title', ''),
                            content=content,
                            embedding=embedding
                        ) for content, embedding in zip(chunked_contents, embeddings)]

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

    async def get_embedding(self, text: str) -> List[float]:
        """
        Get the embedding for the given text.
        Args:
            text (str): The text to get the embedding for.
        Returns:
            List[float]: The embedding for the given text.
        """
        self.logger.debug(
            f"Getting embedding for text (length: {len(text)} characters)")
        try:
            embedding = await self.embedding_model.aembed_query(text)
            self.logger.debug(
                f"Successfully generated embedding (dimension: {len(embedding)})")
            return embedding
        except Exception as e:
            self.logger.error(
                f"Error generating embedding: {e}", exc_info=True)
            raise
