"""Document utility functions for frontend."""
from typing import List, Dict, Any


# BBL document prefix constant
BBL_PREFIX = 'BBL_'


def filter_bbl_documents(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter only BBL documents from document list.

    Args:
        documents: List of document dictionaries

    Returns:
        List of BBL documents only
    """
    if not documents:
        return []

    return [
        doc for doc in documents
        if doc.get('document_id', '').startswith(BBL_PREFIX)
    ]


def get_bbl_document_count(documents_response: Dict[str, Any]) -> int:
    """
    Get count of BBL documents from API response.

    Args:
        documents_response: API response containing documents

    Returns:
        Number of BBL documents
    """
    if not documents_response:
        return 0

    documents = documents_response.get("documents", [])
    bbl_docs = filter_bbl_documents(documents)
    return len(bbl_docs)


def is_bbl_document(document_id: str) -> bool:
    """
    Check if a document ID belongs to a BBL document.

    Args:
        document_id: Document ID to check

    Returns:
        True if document is a BBL document
    """
    return document_id.startswith(BBL_PREFIX)
