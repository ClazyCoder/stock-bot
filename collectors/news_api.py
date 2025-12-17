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

    async def fetch_news(self, ticker: str) -> Tuple[StockNewsCreate, List[StockNewsChunkCreate]]:
        """
        Get the news for one or multiple tickers.
        Args:
            ticker: str - The ticker of the news to fetch.
        Returns:
            Tuple[StockNewsCreate, List[StockNewsChunkCreate]] - The news for the given tickers.
        """
        chunks = []
        search_results = yf.Search(ticker).search()
        loop = asyncio.get_running_loop()
        for news in search_results.news:
            downloaded_page = await loop.run_in_executor(
                None, lambda: trafilatura.fetch_url(news['link']))
            extracted_content = await loop.run_in_executor(
                None, lambda: trafilatura.extract(downloaded_page, output_format='json', include_comments=False, with_metadata=True))
            results = json.loads(extracted_content)
            chunked_contents = await loop.run_in_executor(
                None, lambda: self.text_splitter.split_text(results['text']))
            embeddings = await self.embedding_model.aembed_documents(chunked_contents)
            chunks.extend([StockNewsChunkCreate(
                ticker=ticker, title=results['title'], content=content, embedding=embedding) for content, embedding in zip(chunked_contents, embeddings)])
        full_news = StockNewsCreate(
            ticker=ticker, title=results['title'], full_content=results['text'], published_at=results['date'], url=news['link'])
        return full_news, chunks

    async def get_embedding(self, text: str) -> List[float]:
        """
        Get the embedding for the given text.
        Args:
            text (str): The text to get the embedding for.
        Returns:
            List[float]: The embedding for the given text.
        """
        return await self.embedding_model.aembed_query(text)
