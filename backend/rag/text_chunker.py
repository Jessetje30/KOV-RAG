"""Text chunking utilities for splitting documents into manageable pieces."""
import re
import logging
from typing import List

from config import CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)


class TextChunker:
    """Handles intelligent text chunking with sentence boundary respect."""

    @staticmethod
    def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
        """
        Split text into overlapping chunks, respecting sentence boundaries.

        Args:
            text: Text to chunk
            chunk_size: Target size of each chunk in characters
            overlap: Number of characters to overlap between chunks

        Returns:
            List[str]: List of text chunks
        """
        # Split text into sentences using common sentence delimiters
        # Matches periods, exclamation marks, question marks followed by space or newline
        sentence_endings = re.compile(r'(?<=[.!?])\s+')
        sentences = sentence_endings.split(text)

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_length = len(sentence)

            # If single sentence exceeds chunk_size, split it by words
            if sentence_length > chunk_size * 1.5:
                # If we have accumulated sentences, save them first
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_length = 0

                # Split long sentence into word-based chunks
                words = sentence.split()
                word_chunk = []
                word_length = 0

                for word in words:
                    if word_length + len(word) + 1 > chunk_size and word_chunk:
                        chunks.append(' '.join(word_chunk))
                        # Keep overlap by retaining last few words
                        overlap_words = int(overlap / 10)  # Rough estimate
                        word_chunk = word_chunk[-overlap_words:] if overlap_words > 0 else []
                        word_length = sum(len(w) + 1 for w in word_chunk)

                    word_chunk.append(word)
                    word_length += len(word) + 1

                if word_chunk:
                    chunks.append(' '.join(word_chunk))
                continue

            # Check if adding this sentence would exceed chunk_size
            if current_length + sentence_length > chunk_size and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))

                # Start new chunk with overlap
                # Keep sentences that fit in overlap size
                overlap_chunk = []
                overlap_length = 0
                for sent in reversed(current_chunk):
                    if overlap_length + len(sent) <= overlap:
                        overlap_chunk.insert(0, sent)
                        overlap_length += len(sent) + 1
                    else:
                        break

                current_chunk = overlap_chunk
                current_length = overlap_length

            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_length += sentence_length + 1

        # Add remaining chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        # Filter out empty chunks
        chunks = [chunk.strip() for chunk in chunks if chunk.strip()]

        logger.info(f"Created {len(chunks)} chunks from text of length {len(text)}")
        return chunks
