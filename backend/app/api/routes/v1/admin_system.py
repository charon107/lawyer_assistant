"""Admin system status endpoints — RAG health check and stats."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, status

from app.api.deps import CurrentAdmin, LawSearchSvc
from app.core.config import settings
from app.core.exceptions import BadRequestError

router = APIRouter()


def _is_model_cached(model_name: str) -> bool:
    """Check if SentenceTransformer model files exist on disk without loading."""
    cache_base = (
        Path(settings.EMBEDDING_CACHE_DIR)
        if settings.EMBEDDING_CACHE_DIR
        else Path.home() / ".cache" / "torch" / "sentence_transformers"
    )
    folder = "models--" + model_name.replace("/", "--")
    return (cache_base / folder).exists()


@router.get("/rag-status")
def get_rag_status(
    law_search: LawSearchSvc,
    _: CurrentAdmin,
) -> Any:
    """Check Qdrant / RAG pipeline health (admin only)."""
    qdrant_reachable = law_search._qdrant_available()
    article_count = 0
    collection_exists = False

    if qdrant_reachable:
        try:
            info = law_search.client.get_collection("law_articles")
            collection_exists = True
            article_count = info.points_count or 0
        except Exception:
            collection_exists = False

    # Trigger actual Redis connection rather than reading uninitialized private attr
    redis_available = law_search.redis is not None

    model_cached = _is_model_cached(law_search._model_name)

    return {
        "checked_at": datetime.now(UTC).isoformat(),
        "qdrant": {
            "reachable": qdrant_reachable,
            "collection_exists": collection_exists,
            "article_count": article_count,
        },
        "embedding_model": {
            "loaded": law_search._embedder is not None,
            "cached": model_cached,
            "model_name": law_search._model_name,
        },
        "redis": {
            "available": redis_available,
        },
    }


@router.post("/rag-init", status_code=status.HTTP_200_OK)
def init_rag_collection(_: CurrentAdmin) -> Any:
    """Create Qdrant 'law_articles' collection if it doesn't exist (admin only)."""
    from qdrant_client import QdrantClient

    from app.services.law_data.importer import ensure_collection

    client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
    try:
        ensure_collection(client)
    except Exception as e:
        raise BadRequestError(message=f"Failed to initialize collection: {e}") from e

    return {"status": "ok", "message": "Collection 'law_articles' initialized"}
