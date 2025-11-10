"""Document utility functions for frontend - OOP refactored."""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class DocumentType(Enum):
    """Document type enumeration."""
    BBL = "BBL_"
    GENERAL = ""


@dataclass
class DocumentStats:
    """Statistics about a document collection."""
    total_count: int
    bbl_count: int
    general_count: int

    @property
    def has_documents(self) -> bool:
        """Check if there are any documents."""
        return self.total_count > 0

    @property
    def has_bbl_documents(self) -> bool:
        """Check if there are BBL documents."""
        return self.bbl_count > 0


class DocumentFilter:
    """Document filtering and classification utilities."""

    BBL_PREFIX = DocumentType.BBL.value

    @staticmethod
    def is_bbl_document(document_id: str) -> bool:
        """
        Check if a document ID belongs to a BBL document.

        Args:
            document_id: Document ID to check

        Returns:
            True if document is a BBL document
        """
        return document_id.startswith(DocumentFilter.BBL_PREFIX)

    @staticmethod
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
            if DocumentFilter.is_bbl_document(doc.get('document_id', ''))
        ]

    @staticmethod
    def filter_by_type(
        documents: List[Dict[str, Any]],
        doc_type: DocumentType
    ) -> List[Dict[str, Any]]:
        """
        Filter documents by type.

        Args:
            documents: List of document dictionaries
            doc_type: Type to filter by

        Returns:
            Filtered documents
        """
        if not documents:
            return []

        if doc_type == DocumentType.BBL:
            return DocumentFilter.filter_bbl_documents(documents)
        elif doc_type == DocumentType.GENERAL:
            return [
                doc for doc in documents
                if not DocumentFilter.is_bbl_document(doc.get('document_id', ''))
            ]

        return documents

    @staticmethod
    def categorize_documents(
        documents: List[Dict[str, Any]]
    ) -> Dict[DocumentType, List[Dict[str, Any]]]:
        """
        Categorize documents by type.

        Args:
            documents: List of document dictionaries

        Returns:
            Dictionary mapping document type to documents
        """
        if not documents:
            return {DocumentType.BBL: [], DocumentType.GENERAL: []}

        bbl_docs = []
        general_docs = []

        for doc in documents:
            if DocumentFilter.is_bbl_document(doc.get('document_id', '')):
                bbl_docs.append(doc)
            else:
                general_docs.append(doc)

        return {
            DocumentType.BBL: bbl_docs,
            DocumentType.GENERAL: general_docs
        }


class DocumentAnalyzer:
    """Document analysis and statistics utilities."""

    @staticmethod
    def get_stats(documents_response: Optional[Dict[str, Any]]) -> DocumentStats:
        """
        Get document statistics from API response.

        Args:
            documents_response: API response containing documents

        Returns:
            DocumentStats object with counts
        """
        if not documents_response:
            return DocumentStats(total_count=0, bbl_count=0, general_count=0)

        documents = documents_response.get("documents", [])
        total = len(documents)

        categorized = DocumentFilter.categorize_documents(documents)
        bbl_count = len(categorized[DocumentType.BBL])
        general_count = len(categorized[DocumentType.GENERAL])

        return DocumentStats(
            total_count=total,
            bbl_count=bbl_count,
            general_count=general_count
        )

    @staticmethod
    def get_bbl_document_count(documents_response: Optional[Dict[str, Any]]) -> int:
        """
        Get count of BBL documents from API response.

        Args:
            documents_response: API response containing documents

        Returns:
            Number of BBL documents
        """
        stats = DocumentAnalyzer.get_stats(documents_response)
        return stats.bbl_count

    @staticmethod
    def get_total_size(documents: List[Dict[str, Any]]) -> int:
        """
        Calculate total size of documents in bytes.

        Args:
            documents: List of document dictionaries

        Returns:
            Total size in bytes
        """
        if not documents:
            return 0

        return sum(doc.get('file_size', 0) for doc in documents)

    @staticmethod
    def get_total_chunks(documents: List[Dict[str, Any]]) -> int:
        """
        Calculate total number of chunks across documents.

        Args:
            documents: List of document dictionaries

        Returns:
            Total number of chunks
        """
        if not documents:
            return 0

        return sum(doc.get('chunks_count', 0) for doc in documents)


# Backward compatibility - legacy function interface
def filter_bbl_documents(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Legacy function - use DocumentFilter.filter_bbl_documents() instead."""
    return DocumentFilter.filter_bbl_documents(documents)


def get_bbl_document_count(documents_response: Dict[str, Any]) -> int:
    """Legacy function - use DocumentAnalyzer.get_bbl_document_count() instead."""
    return DocumentAnalyzer.get_bbl_document_count(documents_response)


def is_bbl_document(document_id: str) -> bool:
    """Legacy function - use DocumentFilter.is_bbl_document() instead."""
    return DocumentFilter.is_bbl_document(document_id)


# Export constants for backward compatibility
BBL_PREFIX = DocumentFilter.BBL_PREFIX
