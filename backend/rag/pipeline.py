"""Main RAG pipeline orchestration."""
import uuid
import logging
import time
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone

from config import (
    MINIMUM_RELEVANCE_THRESHOLD,
    SIMILARITY_THRESHOLD,
    DEFAULT_TOP_K,
    MAX_TOP_K
)
from rag.document_processor import DocumentProcessor
from rag.text_chunker import TextChunker
from rag.vector_store import VectorStore
from rag.llm.openai_provider import OpenAILLMProvider
from rag.llm.prompts import QueryPrompts
from rag.query_analyzer import QueryAnalyzer
from rag.reranker import BBLReranker
from cache import query_cache

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Main RAG pipeline for document processing and querying."""

    def __init__(self):
        """Initialize RAG pipeline with all components."""
        logger.info("Initializing RAG Pipeline...")

        self.document_processor = DocumentProcessor()
        self.text_chunker = TextChunker()
        self.vector_store = VectorStore()
        self.llm_provider = OpenAILLMProvider()
        self.query_analyzer = QueryAnalyzer(llm_provider=self.llm_provider)
        self.reranker = BBLReranker(llm_provider=self.llm_provider)

        logger.info("RAG Pipeline initialized successfully")

    def _get_collection_name(self, user_id: int) -> str:
        """
        Get collection name for a user.

        Args:
            user_id: User ID

        Returns:
            str: Collection name
        """
        return f"user_{user_id}_documents"

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
        """
        collection_name = self._get_collection_name(user_id)
        
        # Ensure collection exists
        self.vector_store.ensure_collection(collection_name)
        
        # Check if XML file (BBL)
        is_xml = filename.lower().endswith('.xml')

        if is_xml:
            # XML files: use BBL-specific processing that returns structured chunks
            bbl_chunks = self.document_processor.extract_text(file_content, filename)

            if not bbl_chunks or not isinstance(bbl_chunks, list):
                raise ValueError("No chunks could be extracted from BBL XML")

            # Generate document ID from BBL metadata
            # Extract version from BBL chunks metadata
            version_date = bbl_chunks[0]['metadata'].get('version_date', '2025-07-01')
            document_id = f"BBL_{version_date}"

            # Extract texts for embedding
            texts = [chunk['text'] for chunk in bbl_chunks]

            # Get embeddings in batches to avoid timeout
            logger.info(f"Generating embeddings for {len(texts)} BBL chunks in batches...")
            batch_size = 50
            embeddings = []
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
                batch_embeddings = self.llm_provider.get_embeddings(batch_texts)
                embeddings.extend(batch_embeddings)

            # Store with BBL metadata
            from qdrant_client.models import PointStruct
            from datetime import datetime, timezone
            points = []
            for idx, (chunk, embedding) in enumerate(zip(bbl_chunks, embeddings)):
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        # Standard RAG fields
                        "document_id": document_id,
                        "user_id": user_id,
                        "filename": filename,
                        "chunk_index": idx,
                        "text": chunk['text'],
                        "upload_date": datetime.now(timezone.utc).isoformat(),
                        "file_size": file_size,
                        # BBL-specific metadata
                        **chunk['metadata']
                    }
                )
                points.append(point)

            # Upload to Qdrant in batches to avoid timeout
            logger.info(f"Uploading {len(points)} points to Qdrant in batches...")
            upsert_batch_size = 100
            for i in range(0, len(points), upsert_batch_size):
                batch_points = points[i:i + upsert_batch_size]
                logger.info(f"Uploading batch {i//upsert_batch_size + 1}/{(len(points) + upsert_batch_size - 1)//upsert_batch_size}")
                self.vector_store.client.upsert(
                    collection_name=collection_name,
                    points=batch_points
                )
            chunks_created = len(points)

        else:
            # Non-XML files: use standard text processing
            # Generate document ID
            document_id = str(uuid.uuid4())

            # Extract text
            text = self.document_processor.extract_text(file_content, filename)

            # Chunk text
            chunks = self.text_chunker.chunk_text(text)

            if not chunks:
                raise ValueError("No text could be extracted from the document")

            # Get embeddings
            embeddings = self.llm_provider.get_embeddings(chunks)

            # Store in vector database
            metadata = {
                "user_id": user_id,
                "document_id": document_id,
                "filename": filename,
                "file_size": file_size
            }

            chunks_created = self.vector_store.add_points(
                collection_name=collection_name,
                texts=chunks,
                embeddings=embeddings,
                metadata=metadata
            )
        
        logger.info(f"Processed document {document_id}: {chunks_created} chunks created")
        return document_id, chunks_created

    def query(
        self,
        user_id: int,
        query_text: str,
        top_k: int = DEFAULT_TOP_K
    ) -> Tuple[str, List[Dict[str, Any]], float]:
        """
        Query the RAG system with intelligent query analysis.

        Args:
            user_id: User ID
            query_text: Query text
            top_k: Number of chunks to retrieve

        Returns:
            Tuple of (answer, sources, processing_time)
        """
        start_time = time.time()

        # Validate top_k
        top_k = max(1, min(top_k, MAX_TOP_K))

        # Check cache first
        cached_result = query_cache.get(user_id, query_text, top_k)
        if cached_result is not None:
            return cached_result

        collection_name = self._get_collection_name(user_id)

        # STEP 1: Analyze query to extract metadata
        logger.info(f"Analyzing query: {query_text}")
        query_analysis = self.query_analyzer.analyze(query_text)
        logger.info(f"Query analysis: functie_types={query_analysis.functie_types}, "
                   f"bouw_type={query_analysis.bouw_type}, thema={query_analysis.thema}, "
                   f"confidence={query_analysis.confidence:.2f}")

        # STEP 2: Get query embedding using enhanced query
        # Use enhanced query for better semantic matching
        query_for_embedding = query_analysis.enhanced_query
        logger.info(f"Using enhanced query for embedding: {query_for_embedding}")
        query_embedding = self.llm_provider.get_embeddings([query_for_embedding])[0]

        # STEP 3: Search vector store WITH metadata filtering
        # Fetch 3x more results than needed, so we can filter and rerank
        search_top_k = min(top_k * 3, 20)  # Max 20 candidates

        # Use metadata filtering if query analysis found relevant metadata
        use_metadata_filters = (
            query_analysis.functie_types or
            query_analysis.bouw_type or
            query_analysis.thema or
            query_analysis.hoofdstuk_nr
        )

        if use_metadata_filters:
            logger.info("Using metadata-filtered search (functie/bouw/thema filtering enabled)")
            search_results = self.vector_store.search_with_metadata_filters(
                collection_name=collection_name,
                query_embedding=query_embedding,
                user_id=user_id,
                top_k=search_top_k,
                functie_types=query_analysis.functie_types if query_analysis.functie_types else None,
                bouw_type=query_analysis.bouw_type,
                thema_tags=[query_analysis.thema] if query_analysis.thema else None,
                hoofdstuk_nr=query_analysis.hoofdstuk_nr
            )
        else:
            logger.info("Using standard search (no metadata filters detected)")
            search_results = self.vector_store.search(
                collection_name=collection_name,
                query_embedding=query_embedding,
                user_id=user_id,
                top_k=search_top_k
            )

        logger.info(f"Retrieved {len(search_results)} candidate chunks from vector store")

        # STEP 4: Filter by relevance and add metadata
        sources = []
        context_texts = []

        for result in search_results:
            if result.score >= SIMILARITY_THRESHOLD:
                source = {
                    "text": result.payload["text"],
                    "document_id": result.payload["document_id"],
                    "filename": result.payload["filename"],
                    "score": result.score,
                    "chunk_index": result.payload["chunk_index"],
                    # BBL metadata
                    "artikel_label": result.payload.get("artikel_label", ""),
                    "artikel_titel": result.payload.get("artikel_titel", ""),
                    "artikel_nummer": result.payload.get("artikel_nummer", ""),
                    "hoofdstuk_nr": result.payload.get("hoofdstuk_nr", ""),
                    "hoofdstuk_titel": result.payload.get("hoofdstuk_titel", ""),
                    "afdeling_nr": result.payload.get("afdeling_nr", ""),
                    "afdeling_titel": result.payload.get("afdeling_titel", ""),
                    # Query analysis metadata
                    "query_analysis": query_analysis.to_dict()
                }
                sources.append(source)
                context_texts.append(result.payload["text"])

        # If not enough high-quality results, take top results above minimum threshold
        if len(sources) == 0 and search_results:
            logger.info(f"No sources with score >= {SIMILARITY_THRESHOLD}, using fallback with threshold {MINIMUM_RELEVANCE_THRESHOLD}")
            for result in search_results[:3]:
                if result.score >= MINIMUM_RELEVANCE_THRESHOLD:
                    source = {
                        "text": result.payload["text"],
                        "document_id": result.payload["document_id"],
                        "filename": result.payload["filename"],
                        "score": result.score,
                        "chunk_index": result.payload["chunk_index"],
                        # BBL metadata
                        "artikel_label": result.payload.get("artikel_label", ""),
                        "artikel_titel": result.payload.get("artikel_titel", ""),
                        "artikel_nummer": result.payload.get("artikel_nummer", ""),
                        "hoofdstuk_nr": result.payload.get("hoofdstuk_nr", ""),
                        "hoofdstuk_titel": result.payload.get("hoofdstuk_titel", ""),
                        # Query analysis metadata
                        "query_analysis": query_analysis.to_dict()
                    }
                    sources.append(source)
                    context_texts.append(result.payload["text"])

        logger.info(f"Filtered to {len(sources)} sources with score >= {SIMILARITY_THRESHOLD} or fallback")

        # Return empty if no relevant results
        if not sources:
            return "Geen relevante informatie gevonden.", [], time.time() - start_time

        # STEP 5: Rerank sources based on metadata matching
        # Use LLM verification for top candidates if confidence is low
        use_llm_reranking = query_analysis.confidence < 0.6  # Use LLM if uncertain
        sources = self.reranker.rerank(
            sources=sources,
            query_text=query_text,
            query_analysis=query_analysis.to_dict(),
            use_llm=use_llm_reranking,
            top_k=min(top_k, len(sources))  # Limit to requested top_k
        )

        logger.info(f"Reranked to top {len(sources)} sources (LLM verification: {use_llm_reranking})")

        # Update context_texts after reranking
        context_texts = [source["text"] for source in sources]

        # Build context
        context = "\n\n".join([f"[{i+1}] {text}" for i, text in enumerate(context_texts)])
        
        # Build prompt
        prompt = QueryPrompts.build_simple_query(context, query_text)
        
        # Generate answer
        answer = self.llm_provider.generate_answer(prompt, max_length=1024)

        # Generate summaries and titles in parallel for better performance
        source_texts = [source["text"] for source in sources]
        summaries, titles = self.llm_provider.generate_summaries_and_titles_parallel(source_texts)

        # Add summaries and titles to sources
        for source, summary, title in zip(sources, summaries, titles):
            source["summary"] = summary
            source["title"] = title

        processing_time = time.time() - start_time
        logger.info(f"Query processed in {processing_time:.2f}s with {len(sources)} sources")

        # Cache the result
        result = (answer, sources, processing_time)
        query_cache.set(user_id, query_text, top_k, result)

        return result

    def query_with_chat(
        self,
        user_id: int,
        query_text: str,
        chat_history: List[Dict[str, str]],
        top_k: int = DEFAULT_TOP_K
    ) -> Tuple[str, List[Dict[str, Any]], float]:
        """
        Query with conversation history and intelligent query analysis.

        Args:
            user_id: User ID
            query_text: Current query
            chat_history: List of previous messages with 'role' and 'content'
            top_k: Number of chunks to retrieve

        Returns:
            Tuple of (answer, sources, processing_time)
        """
        start_time = time.time()

        # Validate top_k
        top_k = max(1, min(top_k, MAX_TOP_K))

        collection_name = self._get_collection_name(user_id)

        # Analyze query
        query_analysis = self.query_analyzer.analyze(query_text)
        logger.info(f"Chat query analysis: {query_analysis.to_dict()}")

        # Get query embedding using enhanced query
        query_for_embedding = query_analysis.enhanced_query
        query_embedding = self.llm_provider.get_embeddings([query_for_embedding])[0]

        # Search with more candidates and metadata filtering
        search_top_k = min(top_k * 3, 20)

        # Use metadata filtering if query analysis found relevant metadata
        use_metadata_filters = (
            query_analysis.functie_types or
            query_analysis.bouw_type or
            query_analysis.thema or
            query_analysis.hoofdstuk_nr
        )

        if use_metadata_filters:
            logger.info("Chat: Using metadata-filtered search")
            search_results = self.vector_store.search_with_metadata_filters(
                collection_name=collection_name,
                query_embedding=query_embedding,
                user_id=user_id,
                top_k=search_top_k,
                functie_types=query_analysis.functie_types if query_analysis.functie_types else None,
                bouw_type=query_analysis.bouw_type,
                thema_tags=[query_analysis.thema] if query_analysis.thema else None,
                hoofdstuk_nr=query_analysis.hoofdstuk_nr
            )
        else:
            logger.info("Chat: Using standard search (no metadata filters)")
            search_results = self.vector_store.search(
                collection_name=collection_name,
                query_embedding=query_embedding,
                user_id=user_id,
                top_k=search_top_k
            )
        
        # Filter by relevance
        sources = []
        context_texts = []

        for result in search_results:
            if result.score >= SIMILARITY_THRESHOLD:
                source = {
                    "text": result.payload["text"],
                    "document_id": result.payload["document_id"],
                    "filename": result.payload["filename"],
                    "score": result.score,
                    "chunk_index": result.payload["chunk_index"],
                    "artikel_label": result.payload.get("artikel_label", ""),
                    "artikel_titel": result.payload.get("artikel_titel", ""),
                    "artikel_nummer": result.payload.get("artikel_nummer", ""),
                    "hoofdstuk_nr": result.payload.get("hoofdstuk_nr", ""),
                    "hoofdstuk_titel": result.payload.get("hoofdstuk_titel", ""),
                    "query_analysis": query_analysis.to_dict()
                }
                sources.append(source)
                context_texts.append(result.payload["text"])

        if len(sources) == 0 and search_results:
            for result in search_results[:3]:
                if result.score >= MINIMUM_RELEVANCE_THRESHOLD:
                    source = {
                        "text": result.payload["text"],
                        "document_id": result.payload["document_id"],
                        "filename": result.payload["filename"],
                        "score": result.score,
                        "chunk_index": result.payload["chunk_index"],
                        "artikel_label": result.payload.get("artikel_label", ""),
                        "artikel_titel": result.payload.get("artikel_titel", ""),
                        "query_analysis": query_analysis.to_dict()
                    }
                    sources.append(source)
                    context_texts.append(result.payload["text"])
        
        if not sources:
            return "Geen relevante informatie gevonden.", [], time.time() - start_time
        
        # Add citation numbers
        for i, source in enumerate(sources, 1):
            source["citation_number"] = i
        
        # Build context
        context = "\n\n".join([f"[{i+1}] {text}" for i, text in enumerate(context_texts)])
        
        # Build chat history string
        conversation_context = ""
        if chat_history:
            conversation_context = "\n".join([
                f"{msg['role'].capitalize()}: {msg['content']}"
                for msg in chat_history[-5:]  # Last 5 messages
            ])
            conversation_context = f"\n\nPrevious conversation:\n{conversation_context}\n"
        
        # Build prompt
        prompt = QueryPrompts.build_chat_query(context, conversation_context, query_text)
        
        # Generate answer
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
        
        # Get all points for this user
        points = self.vector_store.scroll_documents(collection_name, user_id)
        
        # Group by document_id
        documents = {}
        for point in points:
            doc_id = point.payload.get("document_id")
            if doc_id not in documents:
                documents[doc_id] = {
                    "document_id": doc_id,
                    "filename": point.payload.get("filename"),
                    "upload_date": point.payload.get("upload_date"),
                    "file_size": point.payload.get("file_size"),
                    "chunks_count": 0
                }
            documents[doc_id]["chunks_count"] += 1
        
        return list(documents.values())

    def get_total_chunks_count(self, user_id: int) -> int:
        """
        Get total count of chunks for a user (fast, doesn't fetch all data).

        Args:
            user_id: User ID

        Returns:
            int: Total number of chunks
        """
        collection_name = self._get_collection_name(user_id)

        try:
            count = self.vector_store.count_points(collection_name, user_id)
            logger.info(f"User {user_id} has {count} total chunks")
            return count
        except Exception as e:
            logger.error(f"Error counting chunks: {str(e)}")
            return 0

    def delete_document(self, user_id: int, document_id: str) -> bool:
        """
        Delete a document and all its chunks.

        Args:
            user_id: User ID
            document_id: Document ID to delete

        Returns:
            bool: True if successful
        """
        collection_name = self._get_collection_name(user_id)
        
        try:
            self.vector_store.delete_by_document_id(collection_name, document_id)
            logger.info(f"Deleted document {document_id} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False

    def health_check(self) -> bool:
        """
        Check if RAG pipeline is healthy.

        Returns:
            bool: True if healthy
        """
        return self.llm_provider.health_check()
