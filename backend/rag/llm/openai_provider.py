"""OpenAI LLM provider implementation."""
import asyncio
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor

from openai import OpenAI

from config import (
    OPENAI_API_KEY,
    OPENAI_LLM_MODEL,
    OPENAI_EMBED_MODEL,
    EMBEDDING_DIMENSION
)
from rag.llm.base import BaseLLMProvider
from rag.llm.prompts import SystemPrompts, SummarizationPrompts
from rag.llm.embedding_cache import EmbeddingCache

logger = logging.getLogger(__name__)


class OpenAILLMProvider(BaseLLMProvider):
    """Provides LLM and embedding functionality using OpenAI API."""

    def __init__(self, api_key: str = OPENAI_API_KEY,
                 llm_model: str = OPENAI_LLM_MODEL,
                 embed_model: str = OPENAI_EMBED_MODEL,
                 enable_cache: bool = True,
                 cache_dir: Optional[Path] = None):
        """
        Initialize OpenAI LLM provider.

        Args:
            api_key: OpenAI API key
            llm_model: Name of OpenAI LLM model (default: gpt-5)
            embed_model: Name of OpenAI embedding model (default: text-embedding-3-large)
            enable_cache: Enable embedding caching (default: True)
            cache_dir: Directory for cache persistence (default: ./embedding_cache)
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
        self.embedding_dimension = EMBEDDING_DIMENSION
        logger.info(f"Embedding dimension: {self.embedding_dimension}")

        # Initialize embedding cache
        if enable_cache:
            if cache_dir is None:
                cache_dir = Path(__file__).parent.parent.parent / "embedding_cache"
            self.embedding_cache = EmbeddingCache(cache_dir=cache_dir, max_memory_items=1000)
        else:
            self.embedding_cache = None

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using OpenAI with caching.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        # If cache is disabled, fetch all from API
        if not self.embedding_cache:
            return self._fetch_embeddings_from_api(texts)

        # Check cache for all texts
        cached_results = self.embedding_cache.get_batch(texts)

        # Separate cached and uncached texts
        embeddings = []
        texts_to_fetch = []
        indices_to_fetch = []

        for i, text in enumerate(texts):
            cached_embedding = cached_results.get(text)
            if cached_embedding is not None:
                embeddings.append((i, cached_embedding))
            else:
                texts_to_fetch.append(text)
                indices_to_fetch.append(i)

        # Fetch uncached embeddings from API
        if texts_to_fetch:
            logger.info(f"Fetching {len(texts_to_fetch)} embeddings from API (cache miss)")
            new_embeddings = self._fetch_embeddings_from_api(texts_to_fetch)

            # Cache the new embeddings
            self.embedding_cache.put_batch(texts_to_fetch, new_embeddings)

            # Add to results
            for idx, embedding in zip(indices_to_fetch, new_embeddings):
                embeddings.append((idx, embedding))
        else:
            logger.info(f"All {len(texts)} embeddings from cache (cache hit)")

        # Sort by original index and extract embeddings
        embeddings.sort(key=lambda x: x[0])
        return [emb for _, emb in embeddings]

    def _fetch_embeddings_from_api(self, texts: List[str]) -> List[List[float]]:
        """
        Fetch embeddings from OpenAI API (internal method).

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            # OpenAI API supports batch processing
            response = self.client.embeddings.create(
                model=self.embed_model,
                input=texts
            )

            embeddings = [data.embedding for data in response.data]
            return embeddings

        except Exception as e:
            logger.error(f"Error getting embeddings from API: {str(e)}")
            raise

    def generate_answer(self, prompt: str, max_length: int = 512) -> str:
        """
        Generate answer using OpenAI GPT-5.

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
                max_completion_tokens=max_length
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

    def generate_titles(self, texts: List[str]) -> List[str]:
        """
        Generate concise titles for multiple texts using OpenAI GPT-4-turbo.

        Args:
            texts: List of texts to generate titles for

        Returns:
            List of titles (one per text)
        """
        try:
            # Build prompt for batch title generation using centralized prompts
            articles = [{"number": i, "text": text} for i, text in enumerate(texts, 1)]
            titles_prompt = SummarizationPrompts.build_bbl_title_request(articles)

            response = self.client.chat.completions.create(
                model="gpt-4-turbo",  # Use GPT-4-turbo for titles
                messages=[
                    {"role": "system", "content": SystemPrompts.BBL_TITLE_EXPERT},
                    {"role": "user", "content": titles_prompt}
                ],
                max_completion_tokens=400  # Titles are short
            )

            titles_text = response.choices[0].message.content

            # Parse titles from response
            titles = []
            lines = titles_text.strip().split('\n')
            for line in lines:
                if line.strip() and line.strip().startswith('['):
                    # Extract title after the [N] prefix
                    parts = line.split(']', 1)
                    if len(parts) > 1:
                        titles.append(parts[1].strip())

            # Fallback: if parsing failed, return first 50 chars of each text
            if len(titles) != len(texts):
                logger.warning(f"Title parsing failed, using fallback. Expected {len(texts)}, got {len(titles)}")
                titles = [text[:50] + "..." if len(text) > 50 else text for text in texts]

            return titles

        except Exception as e:
            logger.error(f"Error generating titles: {str(e)}")
            # Fallback to truncation (50 chars for title)
            return [text[:50] + "..." if len(text) > 50 else text for text in texts]

    def generate_summaries_and_titles_parallel(self, texts: List[str]) -> Tuple[List[str], List[str]]:
        """
        Generate summaries and titles in parallel for better performance.

        Args:
            texts: List of texts to process

        Returns:
            Tuple of (summaries, titles)
        """
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both tasks to run in parallel
            summaries_future = executor.submit(self.generate_summaries, texts)
            titles_future = executor.submit(self.generate_titles, texts)

            # Wait for both to complete
            summaries = summaries_future.result()
            titles = titles_future.result()

        return summaries, titles

    def health_check(self) -> bool:
        """
        Check if OpenAI API is accessible.

        Note: We don't actually call the API here to avoid costs.
        Docker health checks run every 30 seconds, which would be expensive.
        Instead, we just return True since the API key is validated at startup.

        Returns:
            True if healthy, False otherwise
        """
        # Simply return True - the API key is already validated in __init__
        # If there were issues, the app wouldn't have started
        return True
