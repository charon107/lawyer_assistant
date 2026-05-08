"""Law data importer — writes parsed articles to Qdrant + SQLite.

Uses atomic import strategy: write to temp collection, validate, then swap alias.
"""

import logging
import uuid
from datetime import UTC, datetime

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)
from sqlalchemy.orm import Session

from app.db.models.law_metadata import LawMetadata
from app.schemas.law import LawArticle
from app.services.law_data.models import LawDoc, RawArticle

logger = logging.getLogger(__name__)

COLLECTION_NAME = "law_articles"
TEMP_COLLECTION_NAME = "law_articles_tmp"
VECTOR_DIM = 768  # BGE-base-zh

# Fixed namespace for deterministic UUID generation
_LAW_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


def _make_point_id(article: RawArticle) -> str:
    """Generate deterministic UUID from law_id + article_id for Qdrant."""
    return str(uuid.uuid5(_LAW_NAMESPACE, f"{article.law_id}_{article.article_id}"))


def _raw_to_payload(article: RawArticle) -> dict:
    """Convert RawArticle to Qdrant payload dict."""
    return {
        "law_id": article.law_id,
        "law_name": article.law_name,
        "category": article.category,
        "sub_category": article.sub_category,
        "article_id": article.article_id,
        "chapter": article.chapter,
        "section": article.section,
        "content": article.content,
        "effective_date": article.effective_date,
        "status": article.status,
        "source_type": article.source_type,
    }


def _payload_to_article(payload: dict) -> LawArticle:
    """Convert Qdrant payload to LawArticle schema."""
    return LawArticle(
        law_id=payload["law_id"],
        law_name=payload["law_name"],
        category=payload["category"],
        sub_category=payload.get("sub_category"),
        article_id=payload["article_id"],
        chapter=payload.get("chapter"),
        section=payload.get("section"),
        content=payload["content"],
        effective_date=payload.get("effective_date"),
        status=payload.get("status", "现行有效"),
        source_type=payload.get("source_type", "法律"),
    )


def ensure_collection(client: QdrantClient, collection_name: str = COLLECTION_NAME) -> None:
    """Create collection if it doesn't exist with proper indexes."""
    collections = [c.name for c in client.get_collections().collections]
    if collection_name in collections:
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
    )

    # Create payload indexes for filtering
    for field in ["law_id", "category", "sub_category", "source_type", "status", "article_id"]:
        client.create_payload_index(
            collection_name=collection_name,
            field_name=field,
            field_schema="keyword",
        )

    logger.info("Created Qdrant collection: %s", collection_name)


def delete_collection(client: QdrantClient, collection_name: str) -> None:
    """Delete a Qdrant collection if it exists."""
    collections = [c.name for c in client.get_collections().collections]
    if collection_name in collections:
        client.delete_collection(collection_name=collection_name)
        logger.info("Deleted Qdrant collection: %s", collection_name)


def upsert_articles(
    client: QdrantClient,
    articles: list[RawArticle],
    vectors: list[list[float]],
    collection_name: str = COLLECTION_NAME,
    batch_size: int = 64,
) -> int:
    """Upsert articles with pre-computed vectors into Qdrant.

    Args:
        client: Qdrant client instance.
        articles: Parsed articles.
        vectors: Pre-computed embedding vectors (same length as articles).
        collection_name: Target collection name.
        batch_size: Batch size for upsert.

    Returns:
        Number of articles upserted.
    """
    assert len(articles) == len(vectors), "articles and vectors must have same length"

    total = 0
    for i in range(0, len(articles), batch_size):
        batch_articles = articles[i : i + batch_size]
        batch_vectors = vectors[i : i + batch_size]

        points = []
        for article, vector in zip(batch_articles, batch_vectors):
            point = PointStruct(
                id=_make_point_id(article),
                vector=vector,
                payload=_raw_to_payload(article),
            )
            points.append(point)

        client.upsert(collection_name=collection_name, points=points)
        total += len(points)
        logger.info("Upserted batch %d-%d / %d", i, i + len(points), len(articles))

    return total


def sync_law_metadata(db: Session, doc: LawDoc, article_count: int) -> None:
    """Create or update law metadata in SQLite."""
    existing = db.get(LawMetadata, doc.law_id)
    now = datetime.now(UTC)
    if existing:
        existing.name = doc.law_name
        existing.category = doc.category
        existing.sub_category = doc.sub_category
        existing.source_type = doc.source_type
        existing.effective_date = doc.effective_date
        existing.status = doc.status
        existing.article_count = article_count
        existing.last_synced_at = now
    else:
        meta = LawMetadata(
            id=doc.law_id,
            name=doc.law_name,
            category=doc.category,
            sub_category=doc.sub_category,
            source_type=doc.source_type,
            effective_date=doc.effective_date,
            status=doc.status,
            article_count=article_count,
            last_synced_at=now,
        )
        db.add(meta)
    db.flush()


def delete_law_articles(
    client: QdrantClient, law_id: str, collection_name: str = COLLECTION_NAME
) -> None:
    """Delete all articles for a specific law from Qdrant."""
    client.delete(
        collection_name=collection_name,
        points_selector=Filter(must=[FieldCondition(key="law_id", match=MatchValue(value=law_id))]),
    )
    logger.info("Deleted articles for law: %s", law_id)
