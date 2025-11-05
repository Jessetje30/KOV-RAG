"""
Comprehensive tests for core RAG functionality:
- Vector store operations
- LLM provider
- Document processing
- BBL parsing and chunking
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np


# ====================
# Vector Store Tests
# ====================
class TestVectorStore:
    """Tests for Qdrant vector store operations."""

    @pytest.fixture
    def mock_qdrant_client(self):
        """Mock Qdrant client."""
        with patch('qdrant_client.QdrantClient') as mock:
            yield mock

    def test_ensure_collection_creates_if_not_exists(self, mock_qdrant_client):
        """Test collection creation if it doesn't exist."""
        from rag.vector_store import VectorStore

        mock_client = Mock()
        mock_client.collection_exists.return_value = False
        mock_qdrant_client.return_value = mock_client

        store = VectorStore()
        store.ensure_collection("test_collection")

        mock_client.create_collection.assert_called_once()

    def test_add_points_stores_vectors(self, mock_qdrant_client):
        """Test adding vectors to collection."""
        from rag.vector_store import VectorStore

        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client

        store = VectorStore()
        texts = ["text1", "text2"]
        embeddings = [[0.1] * 3072, [0.2] * 3072]
        metadata = {"document_id": "doc-123", "user_id": 1}

        result = store.add_points("test_coll", texts, embeddings, metadata)

        assert result == 2
        mock_client.upsert.assert_called_once()

    def test_search_returns_relevant_results(self, mock_qdrant_client):
        """Test searching returns scored results."""
        from rag.vector_store import VectorStore
        from qdrant_client.models import ScoredPoint

        mock_client = Mock()
        mock_point = ScoredPoint(
            id="point-1",
            score=0.95,
            payload={"text": "result", "document_id": "doc-1", "user_id": 1}
        )
        mock_client.search.return_value = [mock_point]
        mock_qdrant_client.return_value = mock_client

        store = VectorStore()
        results = store.search("test_coll", [0.1] * 3072, user_id=1, top_k=3)

        assert len(results) == 1
        assert results[0].score == 0.95

    def test_delete_by_document_id(self, mock_qdrant_client):
        """Test deleting all points for a document."""
        from rag.vector_store import VectorStore

        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client

        store = VectorStore()
        store.delete_by_document_id("test_coll", "doc-123")

        mock_client.delete.assert_called_once()


# ====================
# LLM Provider Tests
# ====================
class TestLLMProvider:
    """Tests for OpenAI LLM provider."""

    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client."""
        with patch('openai.OpenAI') as mock:
            yield mock

    def test_get_embeddings(self, mock_openai_client):
        """Test generating embeddings."""
        from rag.llm.openai_provider import OpenAILLMProvider

        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 3072)]
        mock_client.embeddings.create.return_value = mock_response
        mock_openai_client.return_value = mock_client

        provider = OpenAILLMProvider()
        embeddings = provider.get_embeddings(["test text"])

        assert len(embeddings) == 1
        assert len(embeddings[0]) == 3072

    def test_generate_answer(self, mock_openai_client):
        """Test answer generation."""
        from rag.llm.openai_provider import OpenAILLMProvider

        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Test answer"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_client.return_value = mock_client

        provider = OpenAILLMProvider()
        answer = provider.generate_answer("Test prompt", max_length=100)

        assert answer == "Test answer"

    def test_generate_summaries_batch(self, mock_openai_client):
        """Test batch summary generation."""
        from rag.llm.openai_provider import OpenAILLMProvider

        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="[1] Summary 1\n[2] Summary 2"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_client.return_value = mock_client

        provider = OpenAILLMProvider()
        summaries = provider.generate_summaries(["text1", "text2"])

        assert len(summaries) == 2

    def test_parallel_summaries_and_titles(self, mock_openai_client):
        """Test parallel generation of summaries and titles."""
        from rag.llm.openai_provider import OpenAILLMProvider

        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="[1] Result"))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_client.return_value = mock_client

        provider = OpenAILLMProvider()
        summaries, titles = provider.generate_summaries_and_titles_parallel(["text"])

        assert len(summaries) == 1
        assert len(titles) == 1


# ====================
# Document Processing Tests
# ====================
class TestDocumentProcessor:
    """Tests for document text extraction."""

    def test_extract_text_from_txt(self):
        """Test extracting text from .txt file."""
        from rag.document_processor import DocumentProcessor

        processor = DocumentProcessor()
        content = b"Hello World\nTest content"
        text = processor.extract_text(content, "test.txt")

        assert "Hello World" in text
        assert "Test content" in text

    @patch('fitz.open')
    def test_extract_text_from_pdf(self, mock_fitz):
        """Test extracting text from PDF."""
        from rag.document_processor import DocumentProcessor

        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_text.return_value = "PDF content"
        mock_doc.__iter__.return_value = [mock_page]
        mock_fitz.return_value.__enter__.return_value = mock_doc

        processor = DocumentProcessor()
        text = processor.extract_text(b"pdf bytes", "test.pdf")

        assert "PDF content" in text

    def test_unsupported_file_type_raises_error(self):
        """Test that unsupported file types raise ValueError."""
        from rag.document_processor import DocumentProcessor

        processor = DocumentProcessor()
        with pytest.raises(ValueError, match="Unsupported file type"):
            processor.extract_text(b"data", "test.xyz")


# ====================
# Text Chunking Tests
# ====================
class TestTextChunker:
    """Tests for text chunking with overlap."""

    def test_chunk_text_basic(self):
        """Test basic text chunking."""
        from rag.text_chunker import TextChunker

        chunker = TextChunker(chunk_size=20, chunk_overlap=5)
        text = "This is a test text that should be chunked into multiple pieces."

        chunks = chunker.chunk_text(text)

        assert len(chunks) > 1
        # Check overlap exists
        assert any(chunks[i][-5:] in chunks[i+1] for i in range(len(chunks)-1))

    def test_short_text_single_chunk(self):
        """Test that short text produces single chunk."""
        from rag.text_chunker import TextChunker

        chunker = TextChunker(chunk_size=100, chunk_overlap=10)
        text = "Short text"

        chunks = chunker.chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0] == "Short text"

    def test_empty_text_returns_empty_list(self):
        """Test empty text returns empty list."""
        from rag.text_chunker import TextChunker

        chunker = TextChunker()
        chunks = chunker.chunk_text("")

        assert chunks == []


# ====================
# BBL Parser Tests
# ====================
class TestBBLParser:
    """Tests for BBL document parsing."""

    def test_parse_bbl_xml_structure(self):
        """Test parsing BBL XML structure."""
        from rag.bbl.bbl_parser import BBLParser

        xml_content = """
        <document>
            <artikel label="Artikel 1.1" titel="Definitie">
                <content>Dit is artikel 1.1 inhoud</content>
            </artikel>
            <artikel label="Artikel 1.2" titel="Toelichting">
                <content>Dit is artikel 1.2 inhoud</content>
            </artikel>
        </document>
        """

        parser = BBLParser()
        articles = parser.parse(xml_content)

        assert len(articles) >= 1
        # Articles should have labels and content

    def test_parse_empty_document(self):
        """Test parsing empty document."""
        from rag.bbl.bbl_parser import BBLParser

        parser = BBLParser()
        articles = parser.parse("")

        assert articles == [] or articles is None


# ====================
# BBL Chunker Tests
# ====================
class TestBBLChunker:
    """Tests for BBL-specific chunking."""

    def test_preserves_article_structure(self):
        """Test that BBL chunker preserves article metadata."""
        from rag.bbl.bbl_chunker import BBLChunker

        chunker = BBLChunker()
        articles = [
            {
                "label": "Artikel 1.1",
                "titel": "Test",
                "content": "Content here " * 100
            }
        ]

        chunks = chunker.chunk_articles(articles)

        assert len(chunks) > 0
        # Check metadata is preserved
        for chunk in chunks:
            assert "artikel_label" in chunk
            assert chunk["artikel_label"] == "Artikel 1.1"


# ====================
# RAG Pipeline Integration Tests
# ====================
class TestRAGPipeline:
    """Integration tests for complete RAG pipeline."""

    @patch('rag.pipeline.DocumentProcessor')
    @patch('rag.pipeline.VectorStore')
    @patch('rag.pipeline.OpenAILLMProvider')
    def test_process_document_flow(self, mock_llm, mock_store, mock_processor):
        """Test complete document processing flow."""
        from rag.pipeline import RAGPipeline

        # Setup mocks
        mock_processor.return_value.extract_text.return_value = "Extracted text"
        mock_llm.return_value.get_embeddings.return_value = [[0.1] * 3072]
        mock_store.return_value.add_points.return_value = 1

        pipeline = RAGPipeline()
        doc_id, chunks = pipeline.process_document(
            user_id=1,
            filename="test.pdf",
            file_content=b"content",
            file_size=1024
        )

        assert doc_id is not None
        assert chunks > 0

    @patch('rag.pipeline.VectorStore')
    @patch('rag.pipeline.OpenAILLMProvider')
    def test_query_with_cache_hit(self, mock_llm, mock_store):
        """Test query uses cache on second call."""
        from rag.pipeline import RAGPipeline
        from cache import query_cache

        query_cache.clear()

        # Setup mocks
        mock_llm.return_value.get_embeddings.return_value = [[0.1] * 3072]
        mock_llm.return_value.generate_answer.return_value = "Answer"
        mock_llm.return_value.generate_summaries_and_titles_parallel.return_value = (["summary"], ["title"])

        from qdrant_client.models import ScoredPoint
        mock_result = ScoredPoint(
            id="1",
            score=0.9,
            payload={"text": "source", "document_id": "doc", "filename": "f", "chunk_index": 0}
        )
        mock_store.return_value.search.return_value = [mock_result]

        pipeline = RAGPipeline()

        # First query (cache miss)
        answer1, sources1, time1 = pipeline.query(1, "test query", 3)
        assert mock_llm.return_value.generate_answer.called

        # Second query (cache hit)
        mock_llm.return_value.generate_answer.reset_mock()
        answer2, sources2, time2 = pipeline.query(1, "test query", 3)

        # Should not call LLM again
        assert not mock_llm.return_value.generate_answer.called
        assert answer1 == answer2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
