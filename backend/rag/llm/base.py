"""Abstract base class for LLM providers."""
from abc import ABC, abstractmethod
from typing import List


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers (OpenAI, Anthropic, etc)."""

    @abstractmethod
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of strings to embed

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    def generate_answer(self, prompt: str, max_length: int = 512) -> str:
        """
        Generate an answer using the LLM.

        Args:
            prompt: The prompt to send to the LLM
            max_length: Maximum tokens to generate

        Returns:
            Generated text
        """
        pass

    @abstractmethod
    def generate_summaries(self, texts: List[str]) -> List[str]:
        """
        Generate summaries for a list of texts.

        Args:
            texts: List of texts to summarize

        Returns:
            List of summaries
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the LLM provider is healthy.

        Returns:
            True if healthy, False otherwise
        """
        pass
