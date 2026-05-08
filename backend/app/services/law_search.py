"""Law search service — vector similarity search with metadata filtering.

Singleton pattern: Qdrant client and SentenceTransformer are reused globally.
All sync calls wrapped with asyncio.to_thread() to avoid blocking the event loop.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from app.core.config import settings
from app.schemas.law import LawArticle, LawSearchResult
from app.services.law_data.importer import (
    COLLECTION_NAME,
    _payload_to_article,
)

logger = logging.getLogger(__name__)


class LawSearchService:
    """Legal knowledge retrieval service.

    Singleton: Qdrant client and SentenceTransformer reused globally.
    Use get_instance() to obtain the singleton.
    """

    _instance: "LawSearchService | None" = None

    def __init__(
        self,
        qdrant_url: str,
        qdrant_api_key: str | None,
        model_name: str,
        top_k: int = 5,
    ):
        self.client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        self._top_k = top_k
        self._model_name = model_name
        self._embedder = None
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._redis = None

    @property
    def embedder(self):
        """Lazy-load SentenceTransformer on first use."""
        if self._embedder is None:
            import os

            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            from sentence_transformers import SentenceTransformer

            cache_dir = settings.EMBEDDING_CACHE_DIR
            self._embedder = SentenceTransformer(
                self._model_name,
                cache_folder=cache_dir,
            )
            logger.info("Loaded embedding model: %s", self._model_name)
        return self._embedder

    @property
    def redis(self):
        """Lazy-load Redis client on first use."""
        if self._redis is None:
            try:
                import redis

                self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
                self._redis.ping()
                logger.info("Connected to Redis: %s", settings.REDIS_URL)
            except Exception:
                logger.warning("Redis unavailable, caching disabled")
                self._redis = None
        return self._redis

    @classmethod
    def get_instance(cls) -> "LawSearchService":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls(
                qdrant_url=settings.QDRANT_URL,
                qdrant_api_key=settings.QDRANT_API_KEY,
                model_name=settings.EMBEDDING_MODEL_NAME,
                top_k=settings.LAW_SEARCH_TOP_K,
            )
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton. Used for testing or config changes."""
        cls._instance = None

    def _cache_key(self, query: str, **kwargs) -> str:
        """Build cache key from query and filter params."""
        parts = [f"law_search:{query}"]
        for k, v in sorted(kwargs.items()):
            if v is not None:
                parts.append(f"{k}={v}")
        return "|".join(parts)

    async def search(
        self,
        query: str,
        *,
        category: str | None = None,
        sub_category: str | None = None,
        source_type: str | None = None,
        top_k: int | None = None,
    ) -> list[LawSearchResult]:
        """Vector search with metadata filtering.

        Args:
            query: Search query text.
            category: Filter by law category (e.g. "民法", "劳动法").
            sub_category: Filter by sub-category.
            source_type: Filter by source type (法律/行政法规/司法解释).
            top_k: Number of results (default from config).

        Returns:
            List of LawSearchResult sorted by relevance.
        """
        k = top_k or self._top_k

        # Check Redis cache
        cache_key = self._cache_key(
            query, category=category, sub_category=sub_category, source_type=source_type, top_k=k
        )
        cached = self._check_cache(cache_key)
        if cached is not None:
            return cached

        try:
            # Embed query in thread pool (CPU-bound)
            loop = asyncio.get_event_loop()
            vector = await loop.run_in_executor(self._executor, self.embedder.encode, query)
            vector = vector.tolist()

            # Build filter
            must_conditions = []
            if category:
                must_conditions.append(
                    FieldCondition(key="category", match=MatchValue(value=category))
                )
            if sub_category:
                must_conditions.append(
                    FieldCondition(key="sub_category", match=MatchValue(value=sub_category))
                )
            if source_type:
                must_conditions.append(
                    FieldCondition(key="source_type", match=MatchValue(value=source_type))
                )
            query_filter = Filter(must=must_conditions) if must_conditions else None

            # Qdrant search (sync, wrapped in thread)
            search_kwargs = {
                "collection_name": COLLECTION_NAME,
                "query": vector,
                "limit": k,
            }
            if query_filter:
                search_kwargs["query_filter"] = query_filter

            response = await loop.run_in_executor(
                self._executor,
                lambda: self.client.query_points(**search_kwargs),
            )

            # Convert to LawSearchResult
            search_results = []
            for hit in response.points:
                article = _payload_to_article(hit.payload)
                citation = f"《{article.law_name}》{article.article_id}"
                search_results.append(
                    LawSearchResult(article=article, score=hit.score, citation=citation)
                )

            # Cache results
            self._store_cache(cache_key, search_results)

            return search_results

        except Exception:
            logger.exception("Law search failed for query: %s", query)
            return []

    async def get_article(
        self,
        law_id: str,
        article_id: str,
    ) -> LawArticle | None:
        """Exact lookup by law_id + article_id. No embedding needed."""
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self._executor,
                lambda: self.client.scroll(
                    collection_name=COLLECTION_NAME,
                    scroll_filter=Filter(
                        must=[
                            FieldCondition(key="law_id", match=MatchValue(value=law_id)),
                            FieldCondition(key="article_id", match=MatchValue(value=article_id)),
                        ]
                    ),
                    limit=1,
                ),
            )
            points, _ = results
            if not points:
                return None
            return _payload_to_article(points[0].payload)
        except Exception:
            logger.exception("get_article failed: %s %s", law_id, article_id)
            return None

    async def search_by_category(
        self,
        category: str,
        query: str,
        top_k: int = 10,
    ) -> list[LawSearchResult]:
        """Search within a specific law category."""
        return await self.search(query, category=category, top_k=top_k)

    def _check_cache(self, key: str) -> list[LawSearchResult] | None:
        """Check Redis cache for results."""
        r = self.redis
        if r is None:
            return None
        try:
            import json

            data = r.get(key)
            if data:
                items = json.loads(data)
                return [LawSearchResult.model_validate(item) for item in items]
        except Exception:
            pass
        return None

    def _store_cache(self, key: str, results: list[LawSearchResult], ttl: int = 3600) -> None:
        """Store results in Redis cache."""
        r = self.redis
        if r is None:
            return
        try:
            import json

            data = json.dumps([r.model_dump() for r in results], ensure_ascii=False)
            r.setex(key, ttl, data)
        except Exception:
            pass
