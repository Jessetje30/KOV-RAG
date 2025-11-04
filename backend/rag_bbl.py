"""
BBL-specific RAG wrapper
Uses the separate BBL collection instead of the mixed collection
"""

from rag import RAGPipeline


class BBLRAGPipeline(RAGPipeline):
    """
    BBL-specific RAG pipeline that uses the bbl_documents collection
    """

    def _get_collection_name(self, user_id: int) -> str:
        """
        Get BBL collection name for a user.

        Args:
            user_id: User ID

        Returns:
            str: BBL collection name
        """
        return f"user_{user_id}_bbl_documents"

    def get_user_documents(self, user_id: int):
        """
        Get list of BBL documents for a user.
        Returns documents from the BBL-specific collection.
        """
        collection_name = self._get_collection_name(user_id)

        # Check if collection exists
        collections = self.vector_store.client.get_collections().collections
        collection_names = [col.name for col in collections]

        if collection_name not in collection_names:
            return []

        # Scroll through all points to get unique documents
        offset = None
        documents_map = {}

        while True:
            results, offset = self.vector_store.client.scroll(
                collection_name=collection_name,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )

            if not results:
                break

            for point in results:
                doc_id = point.payload["document_id"]
                if doc_id not in documents_map:
                    documents_map[doc_id] = {
                        "document_id": doc_id,
                        "filename": point.payload["filename"],
                        "file_size": point.payload.get("file_size", 0),
                        "upload_date": point.payload["upload_date"],
                        "chunks_count": 1
                    }
                else:
                    documents_map[doc_id]["chunks_count"] += 1

            if offset is None:
                break

        return list(documents_map.values())


# Global instance - initialized on first import (requires OPENAI_API_KEY to be set)
# This will be created when main.py starts up after environment variables are loaded
try:
    rag_pipeline = BBLRAGPipeline()
except ValueError as e:
    # API key not set yet - this is fine during module discovery/testing
    import logging
    logging.warning(f"RAG pipeline not initialized: {e}")
    rag_pipeline = None
