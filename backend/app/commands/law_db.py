"""CLI commands for law database management.

Usage:
    uv run law-db init       # Create Qdrant collection + SQLite table
    uv run law-db import     # Import law data from markdown files
    uv run law-db status     # Show law database status
"""

import logging
from pathlib import Path

import click
from sqlalchemy import select

from app.commands import command, error, info, success, warning

logger = logging.getLogger(__name__)


@command("law-db", help="Manage law database (Qdrant + SQLite)")
@click.argument("action", type=click.Choice(["init", "import", "status"]))
@click.option("--source", type=click.Path(exists=True), help="Source directory with .md law files")
@click.option("--law-id", type=str, help="Specific law ID to import (e.g. 民法典)")
def law_db(action: str, source: str | None, law_id: str | None) -> None:
    """Law database management CLI."""
    if action == "init":
        _init()
    elif action == "import":
        _import_data(source, law_id)
    elif action == "status":
        _status()


def _init() -> None:
    """Initialize law database: create Qdrant collection + SQLite tables."""
    from app.core.config import settings
    from app.db.session import SessionLocal
    from app.services.law_data.importer import ensure_collection

    # Create Qdrant collection
    info("Creating Qdrant collection...")
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
        ensure_collection(client)
        success("Qdrant collection 'law_articles' ready.")
    except Exception as e:
        error(f"Failed to connect to Qdrant: {e}")
        raise SystemExit(1) from e

    # Ensure SQLite tables exist (law_metadata is auto-created by SQLAlchemy)
    info("Checking SQLite tables...")
    with SessionLocal() as db:
        from app.db.models.law_metadata import LawMetadata

        # Verify table is accessible
        db.execute(select(LawMetadata).limit(1))
        db.commit()
        success("SQLite 'law_metadata' table ready.")

    success("Law database initialized successfully.")


def _import_data(source: str | None, law_id: str | None) -> None:
    """Import law data from markdown files into Qdrant + SQLite."""
    from app.core.config import settings
    from app.db.session import SessionLocal
    from app.services.law_data.importer import (
        ensure_collection,
        sync_law_metadata,
        upsert_articles,
    )
    from app.services.law_data.parser import parse_law_text

    if not source:
        error("--source is required for import. Example: --source data/laws/")
        raise SystemExit(1)

    source_path = Path(source)
    md_files = list(source_path.glob("**/*.md"))
    if not md_files:
        error(f"No .md files found in {source_path}")
        raise SystemExit(1)

    info(f"Found {len(md_files)} law files in {source_path}")

    from qdrant_client import QdrantClient

    client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
    ensure_collection(client)

    # Lazy-load embedder (offline mode to avoid HuggingFace timeouts)
    import os

    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    from sentence_transformers import SentenceTransformer

    info(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}")
    embedder = SentenceTransformer(
        settings.EMBEDDING_MODEL_NAME,
        cache_folder=settings.EMBEDDING_CACHE_DIR,
    )

    imported_count = 0
    for md_file in sorted(md_files):
        try:
            text = md_file.read_text(encoding="utf-8")
            doc = parse_law_text(text)

            if law_id and doc.law_id != law_id:
                continue

            if not doc.articles:
                warning(f"No articles found in {md_file.name}, skipping.")
                continue

            info(f"Importing {doc.law_id}: {len(doc.articles)} articles...")

            # Batch embed
            contents = [a.content for a in doc.articles]
            vectors = embedder.encode(contents, batch_size=32, show_progress_bar=True)
            vectors = [v.tolist() for v in vectors]

            # Upsert to Qdrant
            upsert_articles(client, doc.articles, vectors)

            # Sync metadata to SQLite
            with SessionLocal() as db:
                sync_law_metadata(db, doc, len(doc.articles))
                db.commit()

            success(f"  {doc.law_id}: {len(doc.articles)} articles imported.")
            imported_count += 1

        except Exception:
            logger.exception("Failed to import %s", md_file.name)
            error(f"  Failed to import {md_file.name}")

    success(f"\nImport complete: {imported_count} laws imported.")


def _status() -> None:
    """Show law database status."""
    from app.core.config import settings
    from app.db.session import SessionLocal
    from app.services.law_data.importer import COLLECTION_NAME

    # Qdrant status
    info("=== Qdrant ===")
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
        collections = [c.name for c in client.get_collections().collections]
        if COLLECTION_NAME in collections:
            collection_info = client.get_collection(COLLECTION_NAME)
            info(f"  Collection: {COLLECTION_NAME}")
            info(f"  Vectors: {collection_info.points_count}")
            info(f"  Status: {collection_info.status}")
        else:
            warning(f"  Collection '{COLLECTION_NAME}' not found. Run 'law-db init' first.")
    except Exception as e:
        error(f"  Cannot connect to Qdrant: {e}")

    # SQLite status
    info("\n=== Law Metadata (SQLite) ===")
    try:
        from app.db.models.law_metadata import LawMetadata

        with SessionLocal() as db:
            laws = db.execute(select(LawMetadata)).scalars().all()
            if not laws:
                warning("  No laws found. Run 'law-db import' first.")
            else:
                total_articles = 0
                for law in laws:
                    info(f"  {law.id}: {law.name} ({law.article_count} articles, {law.status})")
                    total_articles += law.article_count
                info(f"\n  Total: {len(laws)} laws, {total_articles} articles")
    except Exception as e:
        error(f"  Cannot read law_metadata: {e}")
