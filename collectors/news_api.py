from interfaces import INewsProvider
from schemas.stock import StockNewsCreate
from typing import List, Union
from langchain_community.utilities import SearxSearchWrapper
import logging
import os
from langchain_ollama import OllamaEmbeddings


class NewsDataCollector(INewsProvider):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.news_api = SearxSearchWrapper(
            searx_host=os.getenv("SEARX_BASE_URL", "http:127.0.0.1:8888"))
        self.embedding_model = self._build_embedding_model()
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

    async def fetch_news(self, ticker: Union[str, List[str]]) -> List[StockNewsCreate]:
        """
        Get the news for one or multiple tickers.
        Args:
            ticker: Union[str, List[str]] - The ticker or tickers of the news to fetch.
        Returns:
            List[StockNewsCreate] - The news for the given tickers.
        """
        if isinstance(ticker, str):
            ticker = [ticker]
        news = []
        for t in ticker:
            results = await self.news_api.aresults(
                f"stock news for {t}", k=3, engines=["google_news"])
            breakpoint()
            for result in results:
                news.append(StockNewsCreate(
                    ticker=t, title=result.title, content=result.content, published_at=result.published_at))
        return news
