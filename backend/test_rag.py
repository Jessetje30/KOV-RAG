"""
Tests for RAG functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import io
from rag import DocumentProcessor


class TestDocumentProcessor:
    """Test document processing functionality."""

    @pytest.fixture
    def processor(self):
        """Create a DocumentProcessor instance for testing."""
        return DocumentProcessor()

    def test_extract_text_from_txt(self, processor):
        """Test extracting text from a plain text file."""
        content = b"Hello, this is a test document.\nIt has multiple lines."

        text = processor.extract_text_from_txt(content)

        assert "Hello, this is a test document." in text
        assert "It has multiple lines." in text

    def test_extract_text_from_txt_with_encoding(self, processor):
        """Test extracting text from a text file with different encoding."""
        content = "Test met Nederlandse tekst: é, ë, ï".encode('utf-8')

        text = processor.extract_text_from_txt(content)

        assert "Nederlandse" in text
        assert "é" in text

    def test_chunk_text_basic(self, processor):
        """Test basic text chunking."""
        text = "a" * 2000  # Create a long text

        chunks = processor.chunk_text(text)

        assert len(chunks) > 1
        assert all(len(chunk) <= 800 + 100 for chunk in chunks)  # Max chunk_size + overlap

    def test_chunk_text_short_text(self, processor):
        """Test chunking with text shorter than chunk size."""
        text = "This is a short text."

        chunks = processor.chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_text_empty(self, processor):
        """Test chunking empty text."""
        text = ""

        chunks = processor.chunk_text(text)

        # Empty text returns empty list
        assert len(chunks) == 0

    def test_chunk_text_preserves_overlap(self, processor):
        """Test that chunks have proper overlap."""
        # Create text with recognizable patterns
        text = "ABC " * 300  # Repeating pattern

        chunks = processor.chunk_text(text)

        # Check that consecutive chunks have overlap
        if len(chunks) > 1:
            for i in range(len(chunks) - 1):
                # Last part of chunk i should overlap with start of chunk i+1
                overlap_text = chunks[i][-100:]
                assert len(overlap_text) > 0

    @patch('pypdf.PdfReader')
    def test_extract_text_from_pdf(self, mock_pdf_reader, processor):
        """Test extracting text from a PDF file."""
        # Mock PDF reader
        mock_page = Mock()
        mock_page.extract_text.return_value = "Page content"

        mock_reader = Mock()
        mock_reader.pages = [mock_page, mock_page]
        mock_pdf_reader.return_value = mock_reader

        content = b"fake pdf content"

        text = processor.extract_text_from_pdf(content)

        assert "Page content" in text
        # Should have content from both pages
        assert text.count("Page content") == 2

    @patch('docx.Document')
    def test_extract_text_from_docx(self, mock_document, processor):
        """Test extracting text from a DOCX file."""
        # Mock docx document
        mock_para1 = Mock()
        mock_para1.text = "First paragraph"
        mock_para2 = Mock()
        mock_para2.text = "Second paragraph"

        mock_doc = Mock()
        mock_doc.paragraphs = [mock_para1, mock_para2]
        mock_document.return_value = mock_doc

        content = b"fake docx content"

        text = processor.extract_text_from_docx(content)

        assert "First paragraph" in text
        assert "Second paragraph" in text


class TestOllamaLLMProvider:
    """Test Ollama LLM provider functionality."""

    @patch('requests.post')
    def test_get_embeddings(self, mock_post):
        """Test getting embeddings from Ollama."""
        from rag import OllamaLLMProvider

        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {"embedding": [0.1, 0.2, 0.3]}
        mock_post.return_value = mock_response

        provider = OllamaLLMProvider()

        # Get embeddings
        embeddings = provider.get_embeddings(["test text"])

        assert len(embeddings) == 1
        assert embeddings[0] == [0.1, 0.2, 0.3]

    @patch('requests.post')
    def test_generate_answer(self, mock_post):
        """Test generating an answer from Ollama."""
        from rag import OllamaLLMProvider

        # Mock responses for both initialization embedding test and actual answer
        mock_embedding_response = Mock()
        mock_embedding_response.json.return_value = {"embedding": [0.1, 0.2, 0.3]}

        mock_answer_response = Mock()
        mock_answer_response.json.return_value = {"response": "This is the answer"}

        # First call for initialization, second for generate_answer
        mock_post.side_effect = [mock_embedding_response, mock_answer_response]

        provider = OllamaLLMProvider()

        # Generate answer
        answer = provider.generate_answer("Test prompt")

        assert answer == "This is the answer"
        assert mock_post.called
        assert mock_post.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
