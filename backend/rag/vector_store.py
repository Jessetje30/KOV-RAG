"""Qdrant vector store wrapper."""
import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    MatchAny
)

from config import QDRANT_HOST, QDRANT_PORT, EMBEDDING_DIMENSION

logger = logging.getLogger(__name__)


class VectorStore:
    """Wrapper around Qdrant for vector storage and retrieval."""

    def __init__(self, host: str = QDRANT_HOST, port: int = QDRANT_PORT):
        """Initialize Qdrant client with timeout."""
        self.client = QdrantClient(
            host=host,
            port=port,
            timeout=120  # 120 seconds timeout for large batch operations
        )
        self.embedding_dimension = EMBEDDING_DIMENSION
        logger.info(f"Initialized VectorStore: {host}:{port} (timeout: 120s)")

    def ensure_collection(self, collection_name: str) -> None:
        """
        Create collection if it doesn't exist.

        Args:
            collection_name: Name of the collection
        """
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if collection_name not in collection_names:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dimension,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created collection: {collection_name}")
        else:
            logger.info(f"Collection already exists: {collection_name}")

    def add_points(
        self,
        collection_name: str,
        texts: List[str],
        embeddings: List[List[float]],
        metadata: Dict[str, Any]
    ) -> int:
        """
        Add documents to collection.

        Args:
            collection_name: Name of the collection
            texts: List of text chunks
            embeddings: List of embedding vectors
            metadata: Common metadata for all chunks (user_id, document_id, etc)

        Returns:
            Number of chunks added
        """
        points = []
        for idx, (text, embedding) in enumerate(zip(texts, embeddings)):
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "text": text,
                    "chunk_index": idx,
                    "upload_date": datetime.now(timezone.utc).isoformat(),
                    **metadata
                }
            )
            points.append(point)

        self.client.upsert(collection_name=collection_name, points=points)
        logger.info(f"Added {len(points)} points to {collection_name}")
        return len(points)

    def search(
        self,
        collection_name: str,
        query_embedding: List[float],
        user_id: int,
        top_k: int = 5
    ) -> List[Any]:
        """
        Search for similar documents.

        Args:
            collection_name: Name of the collection
            query_embedding: Query vector
            user_id: Filter by user ID
            top_k: Number of results to return

        Returns:
            List of search results from Qdrant
        """
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            )
        )

        logger.info(f"Found {len(results)} results for user {user_id}")
        return results

    def search_with_metadata_filters(
        self,
        collection_name: str,
        query_embedding: List[float],
        user_id: int,
        top_k: int = 5,
        functie_types: Optional[List[str]] = None,
        bouw_type: Optional[str] = None,
        thema_tags: Optional[List[str]] = None,
        hoofdstuk_nr: Optional[str] = None
    ) -> List[Any]:
        """
        Search with BBL metadata filters for intelligent filtering.

        Args:
            collection_name: Name of the collection
            query_embedding: Query vector
            user_id: Filter by user ID
            top_k: Number of results to return
            functie_types: Filter by functie types (Woonfunctie, Kantoorfunctie, etc.)
            bouw_type: Filter by bouw type (Nieuwbouw / Bestaande bouw)
            thema_tags: Filter by thema tags (brandveiligheid, ventilatie, etc.)
            hoofdstuk_nr: Filter by hoofdstuk nummer

        Returns:
            List of search results from Qdrant
        """
        # Build filter conditions
        filter_conditions = [
            FieldCondition(key="user_id", match=MatchValue(value=user_id))
        ]

        # Filter by functie types (match ANY of the provided functie types)
        if functie_types:
            # For articles that have "Algemeen" as functie type, they should match ANY query
            # So we need OR logic: (has matching functie_type) OR (has "Algemeen")
            logger.info(f"Filtering by functie_types: {functie_types}")
            filter_conditions.append(
                FieldCondition(
                    key="functie_types",
                    match=MatchAny(any=functie_types + ["Algemeen"])  # Include general articles
                )
            )

        # Filter by bouw type
        if bouw_type:
            logger.info(f"Filtering by bouw_type: {bouw_type}")
            # Articles with no bouw_type (None) are general and should also match
            # But Qdrant doesn't easily support "is null OR equals"
            # So we'll just filter by exact match here
            # General articles (with bouw_type=None) won't have this field filtered
            filter_conditions.append(
                FieldCondition(key="bouw_type", match=MatchValue(value=bouw_type))
            )

        # Filter by thema tags (match ANY of the provided tags)
        if thema_tags:
            logger.info(f"Filtering by thema_tags: {thema_tags}")
            filter_conditions.append(
                FieldCondition(
                    key="thema_tags",
                    match=MatchAny(any=thema_tags)
                )
            )

        # Filter by hoofdstuk
        if hoofdstuk_nr:
            logger.info(f"Filtering by hoofdstuk_nr: {hoofdstuk_nr}")
            filter_conditions.append(
                FieldCondition(key="hoofdstuk_nr", match=MatchValue(value=hoofdstuk_nr))
            )

        # Perform search with filters
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=Filter(must=filter_conditions) if len(filter_conditions) > 1 else None
        )

        logger.info(f"Found {len(results)} filtered results for user {user_id}")
        return results

    def delete_by_document_id(self, collection_name: str, document_id: str) -> None:
        """
        Delete all chunks of a document.

        Args:
            collection_name: Name of the collection
            document_id: Document ID to delete
        """
        self.client.delete(
            collection_name=collection_name,
            points_selector=Filter(
                must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
            )
        )
        logger.info(f"Deleted document {document_id} from {collection_name}")

    def scroll_documents(self, collection_name: str, user_id: int, limit: int = 1000) -> List[Any]:
        """
        Scroll through all points for a user.

        Args:
            collection_name: Name of the collection
            user_id: User ID
            limit: Maximum number of points to return

        Returns:
            List of points
        """
        results, _ = self.client.scroll(
            collection_name=collection_name,
            scroll_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            ),
            limit=limit
        )

        return results

    def count_points(self, collection_name: str, user_id: int) -> int:
        """
        Count total points for a user without fetching all data.

        Args:
            collection_name: Name of the collection
            user_id: User ID

        Returns:
            Total count of points
        """
        result = self.client.count(
            collection_name=collection_name,
            count_filter=Filter(
                must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
            ),
            exact=True
        )

        return result.count
