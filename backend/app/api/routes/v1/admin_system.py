"""Admin system status endpoints — RAG health check and stats."""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentAdmin, LawSearchSvc

router = APIRouter()


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

    return {
        "checked_at": datetime.now(UTC).isoformat(),
        "qdrant": {
            "reachable": qdrant_reachable,
            "collection_exists": collection_exists,
            "article_count": article_count,
        },
        "embedding_model": {
            "loaded": law_search._embedder is not None,
            "model_name": law_search._model_name,
        },
        "redis": {
            "available": law_search._redis is not None,
        },
    }
