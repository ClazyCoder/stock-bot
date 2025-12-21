from db.repositories.base import BaseRepository
from schemas.stock import StockPriceCreate, StockPriceResponse, StockNewsCreate, StockNewsChunkCreate, StockNewsResponse
from db.models import Stock, StockNews, StockNewsChunk
from typing import List, Tuple
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select, func
import os
from langchain_ollama import OllamaEmbeddings


class StockRepository(BaseRepository):

    def __init__(self, session_factory):
        super().__init__(session_factory)
        self.embedding_model = self._build_embedding_model()

    def _build_embedding_model(self):
        """Build embedding model based on environment configuration."""
        self.logger.info("Building embedding model...")
        provider = os.getenv("EMBEDDING_PROVIDER", "ollama")
        model = os.getenv("EMBEDDING_MODEL", "embeddinggemma")
        if provider == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            num_gpu_env = os.getenv("OLLAMA_NUM_GPU")
            num_gpu = None
            if num_gpu_env is not None and num_gpu_env.strip():
                try:
                    num_gpu = int(num_gpu_env.strip())
                except ValueError:
                    self.logger.warning(
                        f"Invalid OLLAMA_NUM_GPU value '{num_gpu_env}', ignoring and using Ollama defaults"
                    )
            kwargs = {"model": model, "base_url": base_url}
            if num_gpu is not None:
                kwargs["num_gpu"] = num_gpu
            return OllamaEmbeddings(**kwargs)
        elif provider == "openai":
            raise NotImplementedError(
                "OpenAI embedding model is not implemented")
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")

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

    async def insert_stock_data(self, stock_data: List[StockPriceCreate] | StockPriceCreate) -> int | None:
        """
        Insert one or multiple stock data entries into the database.
        Accepts a single StockPrice or a list of StockPrice (Pydantic) models.
        Converts StockPrice (Pydantic) to Stock (SQLAlchemy ORM).
        Args:
            stock_data (List[StockPrice] | StockPrice): The stock data to insert.
        Returns:
            int | None: The number of affected rows if successful, None otherwise.
        """
        # Normalize input type to list
        if not isinstance(stock_data, list):
            stock_data = [stock_data]

        async with self._get_session() as session:
            try:
                # Filter out any stock data with None values in required fields
                stock_data_list = [
                    {
                        'ticker': stock.ticker,
                        'trade_date': stock.trade_date,
                        'open_price': stock.open_price,
                        'high_price': stock.high_price,
                        'low_price': stock.low_price,
                        'close_price': stock.close_price,
                        'volume': stock.volume
                    }
                    for stock in stock_data
                    if stock.ticker is not None
                    and stock.trade_date is not None
                    and stock.open_price is not None
                    and stock.high_price is not None
                    and stock.low_price is not None
                    and stock.close_price is not None
                    and stock.volume is not None
                ]
                if not stock_data_list:
                    self.logger.warning(
                        "No valid stock data to insert after filtering")
                    return 0

                stmt = insert(Stock).values(stock_data_list).on_conflict_do_nothing(
                    index_elements=['ticker', 'trade_date'])
                result = await session.execute(stmt)
                affected_rows = result.rowcount
                await session.commit()
                self.logger.info(
                    f"Successfully inserted/updated {affected_rows} stock data record(s) (attempted {len(stock_data_list)})")
                return affected_rows
            except Exception as e:
                self.logger.error(
                    f"Error inserting stock data: {e}", exc_info=True)
                await session.rollback()
                return None

    async def get_stock_data(self, ticker: str) -> List[StockPriceResponse] | None:
        """
        Get stock data from the database.
        Args:
            ticker (str): The ticker of the stock to get data for.
        Returns:
            List[StockPriceResponse] | None: The stock data for the given ticker.
        """
        async with self._get_session() as session:
            try:
                stmt = select(Stock).where(Stock.ticker == ticker)
                result = await session.execute(stmt)
                orm_results = result.scalars().all()
                stock_responses = [StockPriceResponse.model_validate(
                    stock) for stock in orm_results]
                self.logger.info(
                    f"Fetched {len(stock_responses)} stock data records for ticker: {ticker}")
                return stock_responses
            except Exception as e:
                self.logger.error(
                    f"Error fetching stock data for ticker {ticker}: {e}", exc_info=True)
                return None

    async def remove_stock_data(self, id: int) -> bool:
        """
        Remove stock data from the database.
        Args:
            id (int): The id of the stock data to remove.
        Returns:
            bool: True if the stock data was removed successfully, False otherwise.
        """
        async with self._get_session() as session:
            stmt = select(Stock).where(Stock.id == id)
            result = await session.execute(stmt)
            orm_result = result.scalar_one_or_none()
            if orm_result:
                await session.delete(orm_result)
                await session.commit()
                self.logger.info(
                    f"Successfully removed stock data with id: {id}")
                return True
            else:
                self.logger.warning(f"Stock data not found for id: {id}")
                return False

    async def insert_stock_news(self, stock_news: StockNewsCreate, chunks: List[StockNewsChunkCreate]) -> int | None:
        """
        Insert stock news and chunks into the database.
        Args:
            stock_news: StockNewsCreate - The stock news to insert.
            chunks: List[StockNewsChunkCreate] - The chunks of the stock news to insert (embedding will be generated).
        Returns:
            int | None: The number of affected rows (1 for news + number of chunks) if successful, None otherwise.
                       Returns 0 if news already exists (no new rows inserted).
        """
        async with self._get_session() as session:
            try:
                # Generate embeddings for all chunks BEFORE inserting news
                # This ensures we don't insert news without chunks if embedding generation fails
                chunk_data_list = []
                if chunks:
                    try:
                        chunk_contents = [chunk.content for chunk in chunks]
                        embeddings = await self.embedding_model.aembed_documents(chunk_contents)

                        # Prepare chunk data for insertion with generated embeddings
                        # Note: parent_id will be set after news insertion
                        for chunk, embedding in zip(chunks, embeddings):
                            chunk_dict = {
                                'ticker': chunk.ticker,
                                'content': chunk.content,
                                'embedding': embedding,
                                'parent_id': None  # Will be set after news insertion
                            }
                            chunk_data_list.append(chunk_dict)
                    except Exception as e:
                        self.logger.error(
                            f"Error generating embeddings for stock news chunks: {e}", exc_info=True)
                        raise

                # Insert news only after successful embedding generation
                stmt = insert(StockNews).values(
                    stock_news.model_dump())\
                    .on_conflict_do_nothing(index_elements=['url'])\
                    .returning(StockNews.id)
                result = await session.execute(stmt)
                stock_news_id = result.scalar_one_or_none()
                if not stock_news_id:
                    self.logger.info(
                        f"Stock news already exists, skipping insert: {stock_news.url}")
                    return 0

                # Set parent_id for all chunks now that we have stock_news_id
                for chunk_dict in chunk_data_list:
                    chunk_dict['parent_id'] = stock_news_id

                chunk_count = 0
                if chunk_data_list:
                    chunk_result = await session.execute(insert(StockNewsChunk).values(chunk_data_list))
                    chunk_count = chunk_result.rowcount

                await session.commit()
                total_affected = 1 + chunk_count  # 1 for news + chunks
                self.logger.info(
                    f"Successfully inserted stock news: {stock_news.title} (id: {stock_news_id}) with {chunk_count} chunks (total {total_affected} rows)")
                return total_affected
            except Exception as e:
                self.logger.error(
                    f"Error inserting stock news: {e}", exc_info=True)
                await session.rollback()
                return None

    async def insert_multiple_stock_news(self, news_list: List[Tuple[StockNewsCreate, List[StockNewsChunkCreate]]]) -> int | None:
        """
        Insert multiple stock news and their chunks into the database.
        Args:
            news_list: List[Tuple[StockNewsCreate, List[StockNewsChunkCreate]]] - List of tuples containing news and chunks (embedding will be generated).
        Returns:
            int | None: The total number of affected rows (news + chunks) if successful, None otherwise.
                       Returns 0 if no new rows were inserted (all news already existed).
        """
        if not news_list:
            return 0

        async with self._get_session() as session:
            try:
                total_affected = 0
                success_count = 0
                for stock_news, chunks in news_list:
                    try:
                        # Generate embeddings for all chunks BEFORE inserting news
                        # This ensures we don't insert news without chunks if embedding generation fails
                        chunk_data_list = []
                        if chunks:
                            try:
                                chunk_contents = [
                                    chunk.content for chunk in chunks]
                                embeddings = await self.embedding_model.aembed_documents(chunk_contents)

                                # Prepare chunk data for insertion with generated embeddings
                                # Note: parent_id will be set after news insertion
                                for chunk, embedding in zip(chunks, embeddings):
                                    chunk_dict = {
                                        'ticker': chunk.ticker,
                                        'content': chunk.content,
                                        'embedding': embedding,
                                        'parent_id': None  # Will be set after news insertion
                                    }
                                    chunk_data_list.append(chunk_dict)
                            except Exception as e:
                                self.logger.error(
                                    f"Error generating embeddings for stock news chunks ({stock_news.url}): {e}", exc_info=True)
                                raise

                        # Insert news only after successful embedding generation
                        stmt = insert(StockNews).values(
                            stock_news.model_dump())\
                            .on_conflict_do_nothing(index_elements=['url'])\
                            .returning(StockNews.id)
                        result = await session.execute(stmt)
                        stock_news_id = result.scalar_one_or_none()
                        if not stock_news_id:
                            # News already exists, skip
                            continue

                        # Set parent_id for all chunks now that we have stock_news_id
                        for chunk_dict in chunk_data_list:
                            chunk_dict['parent_id'] = stock_news_id

                        chunk_count = 0
                        if chunk_data_list:
                            chunk_result = await session.execute(insert(StockNewsChunk).values(chunk_data_list))
                            chunk_count = chunk_result.rowcount

                        total_affected += 1 + chunk_count  # 1 for news + chunks
                        success_count += 1
                    except Exception as e:
                        self.logger.error(
                            f"Error inserting stock news {stock_news.url}: {e}", exc_info=True)
                        continue

                await session.commit()
                self.logger.info(
                    f"Successfully inserted {success_count}/{len(news_list)} news items (total {total_affected} rows affected)")
                return total_affected
            except Exception as e:
                self.logger.error(
                    f"Error inserting multiple stock news: {e}", exc_info=True)
                await session.rollback()
                return None

    async def get_stock_news(self, ticker: str, query: str, top_k: int = 5, candidate_pool: int = 20) -> List[StockNewsResponse] | None:
        """
        Get stock news from the database.
        Args:
            ticker: str - The ticker of the stock news to get.
            query: str - The query text to get the stock news for (will be converted to embedding internally).
        Returns:
            List[StockNewsResponse] | None: The stock news for the given ticker and query.
        """
        # Generate embedding for the query
        self.logger.debug(f"Generating embedding for query: {query[:50]}...")
        query_embedding = await self.embedding_model.aembed_query(query)

        # Validate query_embedding dimension to match the pgvector column (e.g., 768)
        expected_dim = 768
        if len(query_embedding) != expected_dim:
            self.logger.error(
                f"Invalid query_embedding length for ticker {ticker}: expected {expected_dim}, got {len(query_embedding)}"
            )
            raise ValueError(
                f"query_embedding must have length {expected_dim}")
        async with self._get_session() as session:
            try:
                distance_col = StockNewsChunk.embedding.cosine_distance(
                    query_embedding).label("distance")
                subquery = (
                    select(
                        StockNewsChunk.parent_id,
                        distance_col
                    ).where(StockNewsChunk.ticker == ticker)
                    .order_by(distance_col.asc())
                    .limit(candidate_pool)
                    .subquery()
                )
                score_col = func.sum(
                    1 - subquery.c.distance)
                stmt = (
                    select(StockNews, score_col, func.count(
                        subquery.c.parent_id).label("chunk_count")).join(subquery, StockNews.id == subquery.c.parent_id).group_by(StockNews.id).order_by(score_col.desc()).limit(top_k)
                )
                result = await session.execute(stmt)
                orm_results = result.all()
                news_responses = [StockNewsResponse.model_validate(
                    news) for news, _score, _count in orm_results]
                self.logger.info(
                    f"Fetched {len(news_responses)} stock news items for ticker: {ticker} with query: {query[:50]}...")
                return news_responses
            except Exception as e:
                self.logger.error(
                    f"Error getting stock news for ticker {ticker}: {e}", exc_info=True)
                return None
