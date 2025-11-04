"""OpenAI LLM provider implementation."""
import logging
from typing import List

from openai import OpenAI

from config import (
    OPENAI_API_KEY,
    OPENAI_LLM_MODEL,
    OPENAI_EMBED_MODEL,
    EMBEDDING_DIMENSION
)
from rag.llm.base import BaseLLMProvider
from rag.llm.prompts import SystemPrompts, SummarizationPrompts

logger = logging.getLogger(__name__)


class OpenAILLMProvider(BaseLLMProvider):
    """Provides LLM and embedding functionality using OpenAI API."""

    def __init__(self, api_key: str = OPENAI_API_KEY,
                 llm_model: str = OPENAI_LLM_MODEL,
                 embed_model: str = OPENAI_EMBED_MODEL):
        """
        Initialize OpenAI LLM provider.

        Args:
            api_key: OpenAI API key
            llm_model: Name of OpenAI LLM model (default: gpt-5)
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
        self.embedding_dimension = EMBEDDING_DIMENSION
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

    def health_check(self) -> bool:
        """
        Check if OpenAI API is accessible.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Test embedding
            test_embedding = self.get_embeddings(["test"])

            # Test LLM
            test_answer = self.generate_answer("What is 2+2?", max_length=50)

            return True
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
