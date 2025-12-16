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
        for news in search_results.news:
            downloaded_page = trafilatura.fetch_url(news['link'])
            extracted_content = trafilatura.extract(
                downloaded_page, output_format='json', include_comments=False, with_metadata=True)
            results = json.loads(extracted_content)
            chunks = self.text_splitter.split_text(results['text'])
            for chunk in chunks:
                embedding = self.embedding_model.embed_query(chunk)
                chunks.append(StockNewsChunkCreate(
                    ticker=ticker, title=results['title'], content=chunk, embedding=embedding))
        full_news = StockNewsCreate(
            ticker=ticker, title=results['title'], full_content=results['text'], published_at=results['date'], url=news['link'])
        return full_news, chunks
