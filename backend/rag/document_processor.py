"""Document processing utilities for extracting text from various formats."""
import io
import logging

import fitz  # PyMuPDF
import docx

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Handles document parsing and text extraction."""

    @staticmethod
    def extract_text_from_pdf(file_content: bytes) -> str:
        """
        Extract text from PDF file using PyMuPDF (faster and more accurate than pypdf).

        Args:
            file_content: PDF file content as bytes

        Returns:
            str: Extracted text from PDF
        """
        # Open PDF from bytes using PyMuPDF
        doc = fitz.open(stream=file_content, filetype="pdf")

        text = ""
        for page in doc:
            text += page.get_text() + "\n"

        doc.close()
        return text

    @staticmethod
    def extract_text_from_docx(file_content: bytes) -> str:
        """
        Extract text from DOCX file.

        Args:
            file_content: DOCX file content as bytes

        Returns:
            str: Extracted text from DOCX
        """
        docx_file = io.BytesIO(file_content)
        doc = docx.Document(docx_file)

        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"

        return text

    @staticmethod
    def extract_text_from_txt(file_content: bytes) -> str:
        """
        Extract text from TXT file.

        Args:
            file_content: TXT file content as bytes

        Returns:
            str: Extracted text from TXT
        """
        return file_content.decode('utf-8', errors='ignore')

    @staticmethod
    def extract_text(file_content: bytes, filename: str) -> str:
        """
        Extract text from file based on extension.

        Args:
            file_content: File content as bytes
            filename: Original filename with extension

        Returns:
            str: Extracted text

        Raises:
            ValueError: If file type is not supported
        """
        extension = filename.lower().split('.')[-1]

        if extension == 'pdf':
            return DocumentProcessor.extract_text_from_pdf(file_content)
        elif extension == 'docx':
            return DocumentProcessor.extract_text_from_docx(file_content)
        elif extension == 'txt':
            return DocumentProcessor.extract_text_from_txt(file_content)
        else:
            raise ValueError(f"Unsupported file type: {extension}")
