"""
Centralized prompt templates for RAG BBL application.
All LLM prompts are defined here for easy maintenance and versioning.
"""
from typing import List, Dict


class SystemPrompts:
    """System-level prompts that define assistant behavior."""

    GENERAL_ASSISTANT = (
        "You are a helpful assistant that answers questions based on provided context. "
        "Always cite your sources using [1], [2], etc."
    )

    BBL_SUMMARIZATION_EXPERT = (
        "Je bent een expert in het samenvatten van juridische teksten, "
        "specifiek BBL (Besluit Bouwwerken Leefomgeving) artikelen. "
        "Je samenvattingen zijn altijd volledig, zonder afkapping."
    )

    BBL_TITLE_EXPERT = (
        "Je bent een expert in het maken van korte, duidelijke titels voor BBL artikelen. "
        "Je titels zijn altijd beschrijvend, bondig (max 8 woorden), en geven de essentie weer."
    )

    CHAT_ASSISTANT = """You are a helpful AI assistant that answers questions based on provided context documents.
When answering, you MUST cite your sources using inline citations in the format [1], [2], [3], etc.

IMPORTANT CITATION RULES:
1. Insert citation numbers [1][2][3] IMMEDIATELY after the relevant statement
2. Use multiple citations [1][2] when information comes from multiple sources
3. Every factual claim must have a citation
4. Citations should appear throughout your answer, not just at the end"""


class QueryPrompts:
    """Prompts for querying the RAG system."""

    @staticmethod
    def build_simple_query(context: str, question: str) -> str:
        """
        Build a simple query prompt for one-off questions.

        Args:
            context: Numbered context chunks [1] chunk1\n\n[2] chunk2\n\n...
            question: User's question

        Returns:
            Formatted prompt string
        """
        return f"""Answer the question based on the context below. Cite sources using [1], [2], etc.

Context:
{context}

Question: {question}

Answer:"""

    @staticmethod
    def build_chat_query(
        context: str,
        conversation_history: str,
        current_question: str
    ) -> str:
        """
        Build a chat query prompt with conversation history.

        Args:
            context: Numbered context chunks
            conversation_history: Previous messages formatted as string
            current_question: Current user question

        Returns:
            Formatted prompt string
        """
        return f"""You are a helpful AI assistant that answers questions based on provided context documents.
When answering, you MUST cite your sources using inline citations in the format [1], [2], [3], etc.

IMPORTANT CITATION RULES:
1. Insert citation numbers [1][2][3] IMMEDIATELY after the relevant statement
2. Use multiple citations [1][2] when information comes from multiple sources
3. Every factual claim must have a citation
4. Citations should appear throughout your answer, not just at the end

Context documents:
{context}{conversation_history}

Current question: {current_question}

Provide a comprehensive answer with inline citations. Remember to cite sources throughout your answer using [1][2][3] etc:"""


class SummarizationPrompts:
    """Prompts for text summarization."""

    @staticmethod
    def build_bbl_summary_request(articles: List[Dict[str, str]]) -> str:
        """
        Build a prompt to summarize BBL articles.

        Args:
            articles: List of dicts with 'number' and 'text' keys

        Returns:
            Formatted prompt string
        """
        prompt = (
            "Je bent een assistent die korte, relevante samenvattingen maakt van BBL artikelen.\n\n"
            "Maak voor elk van de volgende BBL artikelen een korte samenvatting van maximaal 3 zinnen "
            "die de kern van het artikel volledig weergeeft. Snijd de tekst niet af, maar vat samen:\n\n"
        )

        for article in articles:
            prompt += f"[{article['number']}] {article['text']}\n\n"

        prompt += "\nGeef je antwoord in dit formaat:\n"
        prompt += "[1] <samenvatting artikel 1 in maximaal 3 zinnen>\n"
        prompt += "[2] <samenvatting artikel 2 in maximaal 3 zinnen>\n"

        return prompt

    @staticmethod
    def build_bbl_title_request(articles: List[Dict[str, str]]) -> str:
        """
        Build a prompt to generate titles for BBL articles.

        Args:
            articles: List of dicts with 'number' and 'text' keys

        Returns:
            Formatted prompt string
        """
        prompt = (
            "Je bent een expert in het genereren van korte, duidelijke titels voor BBL artikelen.\n\n"
            "Maak voor elk van de volgende BBL artikelen een korte, beschrijvende titel "
            "van maximaal 8 woorden die de essentie van het artikel weergeeft:\n\n"
        )

        for article in articles:
            prompt += f"[{article['number']}] {article['text']}\n\n"

        prompt += "\nGeef je antwoord in dit formaat:\n"
        prompt += "[1] <korte titel voor artikel 1>\n"
        prompt += "[2] <korte titel voor artikel 2>\n"

        return prompt


# Convenience functions for backward compatibility
def get_system_prompt(prompt_type: str = "general") -> str:
    """
    Get a system prompt by type.

    Args:
        prompt_type: One of 'general', 'bbl_summary', 'chat'

    Returns:
        System prompt string
    """
    prompts_map = {
        "general": SystemPrompts.GENERAL_ASSISTANT,
        "bbl_summary": SystemPrompts.BBL_SUMMARIZATION_EXPERT,
        "chat": SystemPrompts.CHAT_ASSISTANT,
    }
    return prompts_map.get(prompt_type, SystemPrompts.GENERAL_ASSISTANT)
