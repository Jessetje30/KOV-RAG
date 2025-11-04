"""
RAG (Retrieval-Augmented Generation) pipeline implementation.
Handles document processing, embedding, vector storage, and query processing.
Uses OpenAI GPT-5 for state-of-the-art reasoning and text-embedding-3-large for embeddings.
"""
import os
import uuid
import time
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone
import io
import logging

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)
import fitz  # PyMuPDF
import docx

# OpenAI imports
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import centralized configuration
from config import (
    QDRANT_HOST,
    QDRANT_PORT,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    OPENAI_API_KEY,
    OPENAI_LLM_MODEL,
    OPENAI_EMBED_MODEL,
    EMBEDDING_DIMENSION,
    MINIMUM_RELEVANCE_THRESHOLD,
    SIMILARITY_THRESHOLD
)
# Import prompts
from rag.llm.prompts import SystemPrompts, QueryPrompts, SummarizationPrompts


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
        import re

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

        return chunks


class OpenAILLMProvider:
    """Provides LLM and embedding functionality using OpenAI API."""

    def __init__(self, api_key: str = OPENAI_API_KEY,
                 llm_model: str = OPENAI_LLM_MODEL,
                 embed_model: str = OPENAI_EMBED_MODEL):
        """
        Initialize OpenAI LLM provider.

        Args:
            api_key: OpenAI API key
            llm_model: Name of OpenAI LLM model (default: gpt-4o)
            embed_model: Name of OpenAI embedding model (default: text-embedding-3-large)
        """
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable must be set")

        self.client = OpenAI(api_key=api_key)
        self.llm_model = llm_model
        self.embed_model = embed_model

        logger.info(f"Initializing OpenAI provider")
        logger.info(f"LLM model: {llm_model}")
        logger.info(f"Embedding model: {embed_model}")

        # text-embedding-3-large has 3072 dimensions
        self.embedding_dimension = 3072
        logger.info(f"Embedding dimension: {self.embedding_dimension}")

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using OpenAI.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        embeddings = []

        try:
            # OpenAI API supports batch processing
            response = self.client.embeddings.create(
                model=self.embed_model,
                input=texts
            )

            for data in response.data:
                embeddings.append(data.embedding)

            return embeddings

        except Exception as e:
            logger.error(f"Error getting embeddings: {str(e)}")
            raise

    def generate_answer(self, prompt: str, max_length: int = 512) -> str:
        """
        Generate answer using OpenAI GPT-4o.

        Args:
            prompt: Input prompt
            max_length: Maximum tokens for generated answer

        Returns:
            Generated answer text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": SystemPrompts.GENERAL_ASSISTANT},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=max_length  # GPT-5 uses max_completion_tokens and default temperature=1
            )

            answer = response.choices[0].message.content

            # Debug logging
            logger.info(f"OpenAI response finish_reason: {response.choices[0].finish_reason}")
            logger.info(f"Answer length: {len(answer) if answer else 0}")
            if not answer or not answer.strip():
                logger.warning("Empty answer received from OpenAI API!")
                logger.warning(f"Response: {response}")

            return answer if answer else ""

        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            raise

    def generate_summaries(self, texts: List[str]) -> List[str]:
        """
        Generate concise summaries for multiple texts using OpenAI GPT-4-turbo.

        Args:
            texts: List of texts to summarize

        Returns:
            List of summaries (one per text)
        """
        try:
            # Build prompt for batch summarization using centralized prompts
            articles = [{"number": i, "text": text} for i, text in enumerate(texts, 1)]
            summaries_prompt = SummarizationPrompts.build_bbl_summary_request(articles)

            response = self.client.chat.completions.create(
                model="gpt-4-turbo",  # Use GPT-4-turbo for summaries
                messages=[
                    {"role": "system", "content": SystemPrompts.BBL_SUMMARIZATION_EXPERT},
                    {"role": "user", "content": summaries_prompt}
                ],
                max_completion_tokens=800  # Increased for 3 sentences per summary
            )

            summaries_text = response.choices[0].message.content

            # Parse summaries from response
            summaries = []
            lines = summaries_text.strip().split('\n')
            for line in lines:
                if line.strip() and line.strip().startswith('['):
                    # Extract summary after the [N] prefix
                    parts = line.split(']', 1)
                    if len(parts) > 1:
                        summaries.append(parts[1].strip())

            # Fallback: if parsing failed, return first 300 chars of each text
            if len(summaries) != len(texts):
                logger.warning(f"Summary parsing failed, using fallback. Expected {len(texts)}, got {len(summaries)}")
                summaries = [text[:300] + "..." if len(text) > 300 else text for text in texts]

            return summaries

        except Exception as e:
            logger.error(f"Error generating summaries: {str(e)}")
            # Fallback to longer truncation (300 chars for ~3 sentences)
            return [text[:300] + "..." if len(text) > 300 else text for text in texts]

    def health_check(self) -> str:
        """
        Check if OpenAI API is accessible.

        Returns:
            Health status string
        """
        try:
            # Test embedding
            test_embedding = self.get_embeddings(["test"])

            # Test LLM
            test_answer = self.generate_answer("What is 2+2?", max_length=50)

            return "healthy"
        except Exception as e:
            return f"unhealthy: {str(e)}"


class RAGPipeline:
    """Main RAG pipeline for document processing and querying."""

    def __init__(self):
        """Initialize RAG pipeline with Qdrant and OpenAI LLM provider."""
        self.qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

        # Initialize OpenAI LLM provider
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable must be set")

        logger.info("Initializing OpenAI LLM provider...")
        self.llm_provider = OpenAILLMProvider()

        self.embedding_dimension = self.llm_provider.embedding_dimension
        logger.info(f"Models initialized. Embedding dimension: {self.embedding_dimension}")

    def _get_collection_name(self, user_id: int) -> str:
        """
        Get collection name for a user.

        Args:
            user_id: User ID

        Returns:
            str: Collection name
        """
        return f"user_{user_id}_documents"

    def _ensure_collection_exists(self, user_id: int):
        """
        Ensure collection exists for user, create if not.

        Args:
            user_id: User ID
        """
        collection_name = self._get_collection_name(user_id)

        # Check if collection exists
        collections = self.qdrant_client.get_collections().collections
        collection_names = [col.name for col in collections]

        if collection_name not in collection_names:
            # Create collection
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dimension,
                    distance=Distance.COSINE
                )
            )

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for texts using local embedding model.

        Args:
            texts: List of texts to embed

        Returns:
            List[List[float]]: List of embedding vectors
        """
        return self.llm_provider.get_embeddings(texts)

    def process_document(
        self,
        user_id: int,
        filename: str,
        file_content: bytes,
        file_size: int
    ) -> Tuple[str, int]:
        """
        Process a document: extract text, chunk, embed, and store in Qdrant.

        Args:
            user_id: User ID
            filename: Original filename
            file_content: File content as bytes
            file_size: File size in bytes

        Returns:
            Tuple[str, int]: Document ID and number of chunks created

        Raises:
            Exception: If document processing fails
        """
        # Ensure collection exists
        self._ensure_collection_exists(user_id)

        # Generate document ID
        document_id = str(uuid.uuid4())

        # Extract text
        text = DocumentProcessor.extract_text(file_content, filename)

        # Chunk text
        chunks = DocumentProcessor.chunk_text(text)

        if not chunks:
            raise ValueError("No text could be extracted from the document")

        # Get embeddings
        embeddings = self._get_embeddings(chunks)

        # Prepare points for Qdrant
        collection_name = self._get_collection_name(user_id)
        points = []

        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "document_id": document_id,
                    "user_id": user_id,
                    "filename": filename,
                    "chunk_index": idx,
                    "text": chunk,
                    "upload_date": datetime.now(timezone.utc).isoformat(),
                    "file_size": file_size
                }
            )
            points.append(point)

        # Upload to Qdrant
        self.qdrant_client.upsert(
            collection_name=collection_name,
            points=points
        )

        return document_id, len(chunks)

    def query(
        self,
        user_id: int,
        query_text: str,
        top_k: int = 5
    ) -> Tuple[str, List[Dict[str, Any]], float]:
        """
        Query the RAG system: retrieve relevant chunks and generate answer.

        Args:
            user_id: User ID
            query_text: Query text
            top_k: Number of top results to retrieve

        Returns:
            Tuple containing:
                - Generated answer (str)
                - List of source chunks (List[Dict])
                - Processing time in seconds (float)

        Raises:
            ValueError: If no documents found for user
        """
        start_time = time.time()

        # Ensure collection exists
        collection_name = self._get_collection_name(user_id)
        collections = self.qdrant_client.get_collections().collections
        collection_names = [col.name for col in collections]

        if collection_name not in collection_names:
            raise ValueError("No documents found. Please upload documents first.")

        # Get query embedding
        query_embedding = self._get_embeddings([query_text])[0]

        # Search in Qdrant
        search_results = self.qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id)
                    )
                ]
            )
        )

        if not search_results:
            raise ValueError("No relevant documents found for your query.")

        # Check minimum relevance threshold
        # Als alle resultaten onder 0.4 scoren, geen bronnen tonen
        MINIMUM_THRESHOLD = 0.4
        SIMILARITY_THRESHOLD = 0.65

        # Check of er überhaupt resultaten zijn boven de minimum threshold
        max_score = max([result.score for result in search_results]) if search_results else 0

        if max_score < MINIMUM_THRESHOLD:
            # Geen relevante resultaten gevonden
            processing_time = time.time() - start_time
            return "Er is niks gevonden, dat dicht genoeg overeen kwam met jouw vraag.", [], processing_time

        # Extract source chunks met score filtering
        # Filter alleen chunks met hoge relevantie score (> 0.65 voor BBL artikelen)
        sources = []
        context_texts = []

        for result in search_results:
            # Filter op similarity score
            if result.score >= SIMILARITY_THRESHOLD:
                source = {
                    "text": result.payload["text"],
                    "document_id": result.payload["document_id"],
                    "filename": result.payload["filename"],
                    "score": result.score,
                    "chunk_index": result.payload["chunk_index"]
                }
                sources.append(source)
                context_texts.append(result.payload["text"])

        # Als geen chunks boven threshold maar wel boven minimum, neem de top 3 beste
        if not sources and search_results:
            logger.warning(f"No chunks above threshold {SIMILARITY_THRESHOLD}, using top 3")
            for result in search_results[:3]:
                source = {
                    "text": result.payload["text"],
                    "document_id": result.payload["document_id"],
                    "filename": result.payload["filename"],
                    "score": result.score,
                    "chunk_index": result.payload["chunk_index"]
                }
                sources.append(source)
                context_texts.append(result.payload["text"])

        # Build context
        context = "\n\n".join([f"[{i+1}] {text}" for i, text in enumerate(context_texts)])

        # Generate answer using local LLM
        prompt = QueryPrompts.build_simple_query(context, query_text)

        answer = self.llm_provider.generate_answer(prompt, max_length=1024)

        # Generate AI summaries for each source
        source_texts = [source["text"] for source in sources]
        summaries = self.llm_provider.generate_summaries(source_texts)

        # Add summaries to sources
        for source, summary in zip(sources, summaries):
            source["summary"] = summary

        processing_time = time.time() - start_time

        return answer, sources, processing_time

    def query_with_chat(
        self,
        user_id: int,
        query_text: str,
        chat_history: List[Dict[str, str]] = None,
        top_k: int = 5
    ) -> Tuple[str, List[Dict[str, Any]], float]:
        """
        Query the RAG system with chat history for conversational context.
        Generates answers with inline citations like Perplexity [1][2][3].

        Args:
            user_id: User ID
            query_text: Current query text
            chat_history: List of previous messages [{"role": "user/assistant", "content": "..."}]
            top_k: Number of top results to retrieve

        Returns:
            Tuple containing:
                - Generated answer with inline citations (str)
                - List of source chunks with citation numbers (List[Dict])
                - Processing time in seconds (float)

        Raises:
            ValueError: If no documents found for user
        """
        start_time = time.time()

        # Ensure collection exists
        collection_name = self._get_collection_name(user_id)
        collections = self.qdrant_client.get_collections().collections
        collection_names = [col.name for col in collections]

        if collection_name not in collection_names:
            raise ValueError("No documents found. Please upload documents first.")

        # Get query embedding
        query_embedding = self._get_embeddings([query_text])[0]

        # Search in Qdrant
        search_results = self.qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id)
                    )
                ]
            )
        )

        if not search_results:
            raise ValueError("No relevant documents found for your query.")

        # Check minimum relevance threshold
        # Als alle resultaten onder 0.4 scoren, geen bronnen tonen
        MINIMUM_THRESHOLD = 0.4
        SIMILARITY_THRESHOLD = 0.65

        # Check of er überhaupt resultaten zijn boven de minimum threshold
        max_score = max([result.score for result in search_results]) if search_results else 0

        if max_score < MINIMUM_THRESHOLD:
            # Geen relevante resultaten gevonden
            processing_time = time.time() - start_time
            return "Er is niks gevonden, dat dicht genoeg overeen kwam met jouw vraag.", [], processing_time

        # Extract source chunks with score filtering
        sources = []
        context_texts = []

        for result in search_results:
            if result.score >= SIMILARITY_THRESHOLD:
                source = {
                    "text": result.payload["text"],
                    "document_id": result.payload["document_id"],
                    "filename": result.payload["filename"],
                    "score": result.score,
                    "chunk_index": result.payload["chunk_index"]
                }
                sources.append(source)
                context_texts.append(result.payload["text"])

        # If no chunks above threshold but above minimum, take top 3 best
        if not sources and search_results:
            logger.warning(f"No chunks above threshold {SIMILARITY_THRESHOLD}, using top 3")
            for result in search_results[:3]:
                source = {
                    "text": result.payload["text"],
                    "document_id": result.payload["document_id"],
                    "filename": result.payload["filename"],
                    "score": result.score,
                    "chunk_index": result.payload["chunk_index"]
                }
                sources.append(source)
                context_texts.append(result.payload["text"])

        # Add citation numbers to sources
        for i, source in enumerate(sources, 1):
            source["citation_number"] = i

        # Build context with numbered citations
        context = "\n\n".join([f"[{i+1}] {text}" for i, text in enumerate(context_texts)])

        # Build chat history string if provided
        conversation_context = ""
        if chat_history:
            conversation_context = "\n".join([
                f"{msg['role'].capitalize()}: {msg['content']}"
                for msg in chat_history[-5:]  # Include last 5 messages for context
            ])
            conversation_context = f"\n\nPrevious conversation:\n{conversation_context}\n"

        # Generate answer with improved prompt for inline citations
        prompt = QueryPrompts.build_chat_query(context, conversation_context, query_text)

        answer = self.llm_provider.generate_answer(prompt, max_length=1024)

        processing_time = time.time() - start_time

        return answer, sources, processing_time

    def get_user_documents(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get list of all documents for a user.

        Args:
            user_id: User ID

        Returns:
            List[Dict]: List of document information
        """
        collection_name = self._get_collection_name(user_id)

        # Check if collection exists
        collections = self.qdrant_client.get_collections().collections
        collection_names = [col.name for col in collections]

        if collection_name not in collection_names:
            return []

        # Scroll through all points to get unique documents
        offset = None
        documents_map = {}

        while True:
            results, offset = self.qdrant_client.scroll(
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

    def delete_document(self, user_id: int, document_id: str) -> bool:
        """
        Delete a document and all its chunks.

        Args:
            user_id: User ID
            document_id: Document ID to delete

        Returns:
            bool: True if successful

        Raises:
            ValueError: If collection doesn't exist
        """
        collection_name = self._get_collection_name(user_id)

        # Check if collection exists
        collections = self.qdrant_client.get_collections().collections
        collection_names = [col.name for col in collections]

        if collection_name not in collection_names:
            raise ValueError("No documents found")

        # Delete points with matching document_id
        self.qdrant_client.delete(
            collection_name=collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        )

        return True

    def health_check(self) -> Dict[str, str]:
        """
        Check health of Qdrant and local LLM provider.

        Returns:
            Dict[str, str]: Health status
        """
        status = {
            "qdrant": "unknown",
            "local_llm": "unknown"
        }

        # Check Qdrant
        try:
            self.qdrant_client.get_collections()
            status["qdrant"] = "healthy"
        except Exception as e:
            status["qdrant"] = f"unhealthy: {str(e)}"

        # Check local LLM provider
        try:
            status["local_llm"] = self.llm_provider.health_check()
        except Exception as e:
            status["local_llm"] = f"unhealthy: {str(e)}"

        return status
