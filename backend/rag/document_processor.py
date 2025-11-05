"""Document processing utilities for extracting text from various formats."""
import io
import logging
from pathlib import Path
from typing import List, Dict

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
    def extract_text_from_bbl_xml(file_content: bytes, filename: str) -> List[Dict]:
        """
        Extract structured chunks from BBL XML file.
        Uses the specialized BBL parser and chunker.

        Args:
            file_content: XML file content as bytes
            filename: Original filename

        Returns:
            List[Dict]: List of chunks with text and metadata

        Raises:
            ValueError: If XML parsing fails
        """
        try:
            # Import BBL-specific parsers
            from bbl.xml_parser import parse_bbl_xml
            from bbl.chunker import create_bbl_chunks

            # Write to temporary file for parser
            import tempfile
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.xml', delete=False) as tmp_file:
                tmp_file.write(file_content)
                tmp_path = Path(tmp_file.name)

            try:
                # Parse BBL XML
                metadata, artikelen = parse_bbl_xml(tmp_path)
                logger.info(f"Parsed BBL XML: {len(artikelen)} artikelen found")

                # Extract version from filename or use default
                version_date = "2025-07-01"  # Default
                if "_" in filename:
                    # Try to extract date from filename like BWBR0041297_2025-07-01_0.xml
                    parts = filename.split("_")
                    if len(parts) >= 2:
                        potential_date = parts[1]
                        if len(potential_date) == 10 and potential_date.count("-") == 2:
                            version_date = potential_date

                # Create chunks
                chunks = create_bbl_chunks(artikelen, version_date)
                logger.info(f"Created {len(chunks)} BBL chunks")

                return chunks

            finally:
                # Clean up temporary file
                tmp_path.unlink(missing_ok=True)

        except Exception as e:
            logger.error(f"Error parsing BBL XML: {str(e)}")
            raise ValueError(f"Failed to parse BBL XML: {str(e)}")

    @staticmethod
    def extract_text(file_content: bytes, filename: str):
        """
        Extract text from file based on extension.
        For XML files, returns structured chunks instead of plain text.

        Args:
            file_content: File content as bytes
            filename: Original filename with extension

        Returns:
            str or List[Dict]: Extracted text, or list of chunks for XML files

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
        elif extension == 'xml':
            # XML returns structured chunks, not plain text
            return DocumentProcessor.extract_text_from_bbl_xml(file_content, filename)
        else:
            raise ValueError(f"Unsupported file type: {extension}")
