"""Qdrant vector store wrapper."""
import uuid
import logging
from typing import List, Dict, Any
from datetime import datetime, timezone

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
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
